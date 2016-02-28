#
# Copyright (C) 2012-2016 Craig Hobbs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from io import BytesIO
import itertools
import json
import logging
import os
import re

from .app_defs import ENVIRON_CTX
from .compat import basestring_, iteritems, re_escape, urllib_parse_unquote, xrange_
from .request import Request
from .spec import SpecParser
from .util import load_modules


# Regular expression for matching URL arguments
RE_URL_ARG = re.compile(r'/\{([A-Za-z]\w*)\}')
RE_URL_ARG_ESC = re.compile(r'/\\{([A-Za-z]\w*)\\}')


class Application(object):
    """
    Chisel base application
    """

    __slots__ = ('log_level', 'log_format', 'pretty_output', 'validate_output', 'specs', 'requests', '__request_urls', '__request_regex')

    def __init__(self):
        self.log_level = logging.WARNING
        self.log_format = '%(levelname)s [%(process)s / %(thread)s] %(message)s'
        self.pretty_output = False
        self.validate_output = True
        self.specs = SpecParser()
        self.requests = {}
        self.__request_urls = {}
        self.__request_regex = []

    def load_specs(self, spec_path, spec_ext='.chsl', finalize=True):
        """
        Load a spec file or directory
        """
        if os.path.isdir(spec_path):
            for dirpath, dummy_dirnames, filenames in os.walk(spec_path):
                for filename in filenames:
                    (dummy_base, ext) = os.path.splitext(filename)
                    if ext == spec_ext:
                        with open(os.path.join(dirpath, filename), 'r') as file_spec:
                            self.specs.parse(file_spec, finalize=False)
        else:
            with open(spec_path, 'r') as file_spec:
                self.specs.parse(file_spec, finalize=False)

        if finalize:
            self.specs.finalize()

    def add_request(self, request):
        """
        Add a request object
        """

        # Wrap bare functions in a request decorator
        if not isinstance(request, Request):
            request = Request(request)

        # Duplicate request name?
        if request.name in self.requests:
            raise Exception('Redefinition of request "{0}"'.format(request.name))
        self.requests[request.name] = request

        # Add the request URLs
        for method, url in request.urls:

            # URL with arguments?
            if RE_URL_ARG.search(url):
                request_regex = '^' + RE_URL_ARG_ESC.sub('/(?P<\\1>[^/]+)', re_escape(url)) + '$'
                self.__request_regex.append((method, re.compile(request_regex), request))
            else:
                request_key = (method, url)
                if request_key in self.__request_urls:
                    raise Exception('Redefinition of request URL "{0}"'.format(url))
                self.__request_urls[request_key] = request

        # Make the request app-aware at load-time
        request.onload(self)

    def load_requests(self, module_path, module_ext='.py'):
        """
        Recursively load all requests in a directory
        """
        for module in load_modules(module_path, module_ext=module_ext):
            for module_attr in dir(module):
                request = getattr(module, module_attr)
                if isinstance(request, Request):
                    self.add_request(request)

    def __call__(self, environ, start_response):
        """
        Chisel application WSGI entry point
        """

        # Match the request by exact URL
        path_info = environ['PATH_INFO']
        request_method = environ['REQUEST_METHOD'].upper()
        url_args = None
        for pass_ in xrange_(2):
            request_key = (request_method if pass_ == 0 else None, path_info)
            request = self.__request_urls.get(request_key)
            if request is None:
                # If no request was matched, match by url regular expression
                for request_method_, request_regex, request_ in self.__request_regex:
                    if (pass_ == 0 and request_method_ == request_method) or (pass_ == 1 and request_method_ is None):
                        match_request = request_regex.match(path_info)
                        if match_request:
                            request = request_
                            url_args = {urllib_parse_unquote(url_arg): urllib_parse_unquote(url_value)
                                        for url_arg, url_value in iteritems(match_request.groupdict())}
                            break
            if request is not None:
                break

        # Create the request context
        ctx = Context(self, environ, start_response, url_args)
        environ[ENVIRON_CTX] = ctx

        # Request not found?
        if request is None:
            return ctx.response_text('404 Not Found', 'Not Found')

        # Handle the request
        try:
            return request(ctx.environ, ctx.start_response)
        except: # pylint: disable=bare-except
            ctx.log.exception('Exception raised by WSGI request "%s"', request.name)
            return ctx.response_text('500 Internal Server Error', 'Unexpected Error')

    def request(self, request_method, path_info, query_string=None, wsgi_input=None, environ=None):
        """
        Make an HTTP request on this application
        """

        # WSGI environment
        if environ is None:
            environ = {}
        environ['REQUEST_METHOD'] = request_method
        environ['PATH_INFO'] = path_info
        if 'SCRIPT_NAME' not in environ:
            environ['SCRIPT_NAME'] = ''
        if 'QUERY_STRING' not in environ:
            environ['QUERY_STRING'] = '' if query_string is None else query_string
        if wsgi_input is not None:
            environ['wsgi.input'] = BytesIO(wsgi_input)

        # Capture the response status and headers
        start_response_args = {}
        def start_response(status, response_headers):
            start_response_args['status'] = status
            start_response_args['response_headers'] = response_headers

        # Make the request
        response = self(environ, start_response)
        return start_response_args['status'], start_response_args['response_headers'], b''.join(response)


class Context(object):
    """
    Chisel request context
    """

    __slots__ = ('app', 'environ', '_start_response', 'url_args', 'jsonp', 'log', 'headers')

    def __init__(self, app, environ, start_response, url_args):
        self.app = app
        self.environ = environ
        self._start_response = start_response
        self.url_args = url_args
        self.jsonp = None
        self.headers = []

        # Create the logger
        self.log = logging.getLoggerClass()('')
        self.log.setLevel(self.app.log_level)
        wsgi_errors = environ.get('wsgi.errors')
        if wsgi_errors is None:
            handler = logging.NullHandler()
        else:
            handler = logging.StreamHandler(wsgi_errors) # pylint: disable=redefined-variable-type
        if hasattr(self.app.log_format, '__call__'):
            handler.setFormatter(self.app.log_format(self))
        else:
            handler.setFormatter(logging.Formatter(self.app.log_format))
        self.log.addHandler(handler)

    def start_response(self, status, headers):
        return self._start_response(status, list(itertools.chain(headers, self.headers)))

    def add_header(self, key, value):
        """
        Add a response header
        """
        self.headers.append((key, value))

    def response(self, status, content_type, content, headers=None):
        """
        Send an HTTP response
        """
        assert not isinstance(content, basestring_) and not isinstance(content, bytes), \
            'Response content of type str or bytes received'

        # Build the headers array
        _headers = list(headers) if headers is not None else []
        headers_set = {header[0] for header in _headers}
        if 'Content-Type' not in headers_set:
            _headers.append(('Content-Type', content_type))
        if isinstance(content, list) and 'Content-Length' not in headers_set:
            _headers.append(('Content-Length', str(sum(len(x) for x in content))))

        # Return the response
        self.start_response(status, _headers)
        return content

    def response_text(self, status, text, content_type='text/plain', encoding='utf-8', headers=None):
        """
        Send a plain-text response
        """
        return self.response(status, content_type, [text.encode(encoding)], headers=headers)

    def response_json(self, response, status=None, headers=None, is_error=False):
        """
        Send a JSON response
        """
        if status is None:
            status = '200 OK' if not is_error or self.jsonp is not None else '500 Internal Server Error'
        content = json.dumps(response, sort_keys=True,
                             indent=2 if self.app.pretty_output else None,
                             separators=(', ', ': ') if self.app.pretty_output else (',', ':'))
        if self.jsonp:
            content_list = [self.jsonp.encode('utf-8'), b'(', content.encode('utf-8'), b');']
        else:
            content_list = [content.encode('utf-8')]
        return self.response(status, 'application/json', content_list, headers=headers)
