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

from collections import OrderedDict
from io import BytesIO
from itertools import chain
import logging
import os
import re
from urllib.parse import quote, unquote

from .app_defs import ENVIRON_CTX, STATUS_404_NOT_FOUND, STATUS_405_METHOD_NOT_ALLOWED, STATUS_500_INTERNAL_SERVER_ERROR
from .request import Request
from .spec import SpecParser
from .url import encode_query_string
from .util import JSONEncoder, load_modules


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

        # Duplicate request name?
        if request.name in self.requests:
            raise Exception('Redefinition of request "{0}"'.format(request.name))
        self.requests[request.name] = request

        # Add the request URLs
        for method, url in request.urls:

            # URL with arguments?
            if RE_URL_ARG.search(url):
                request_regex = '^' + RE_URL_ARG_ESC.sub(r'/(?P<\1>[^/]+)', re.escape(url)) + '$'
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
                if isinstance(request, Request) and request.module_name == module.__name__:
                    self.add_request(request)

    def __call__(self, environ, start_response):
        """
        Chisel application WSGI entry point
        """

        # Match the request by exact URL
        path_info = environ['PATH_INFO']
        request_method = environ['REQUEST_METHOD'].upper()
        request, url_args = self.__request_urls.get((request_method, path_info)), None
        if request is None:
            request, url_args = next((
                (request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in request_match.groupdict().items()})
                for request, request_match in
                ((request, regex.match(path_info)) for method, regex, request in self.__request_regex if method == request_method)
                if request_match), (None, None))
            if request is None:
                request, url_args = self.__request_urls.get((None, path_info)), None
                if request is None:
                    request, url_args = next((
                        (request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in request_match.groupdict().items()})
                        for request, request_match in
                        ((request, regex.match(path_info)) for method, regex, request in self.__request_regex if method is None)
                        if request_match), (None, None))

        # Create the request context
        ctx = Context(self, environ, start_response, url_args)
        environ[ENVIRON_CTX] = ctx

        # Request not found?
        if request is None:
            if next((True for _, path in self.__request_urls.keys() if path == path_info), False) or \
               next((True for _, regex, _ in self.__request_regex if regex.match(path_info)), False):
                return ctx.response_text(STATUS_405_METHOD_NOT_ALLOWED, 'Method Not Allowed')
            return ctx.response_text(STATUS_404_NOT_FOUND, 'Not Found')

        # Handle the request
        try:
            return request(ctx.environ, ctx.start_response)
        except: # pylint: disable=bare-except
            ctx.log.exception('Exception raised by WSGI request "%s"', request.name)
            return ctx.response_text(STATUS_500_INTERNAL_SERVER_ERROR, 'Unexpected Error')

    def request(self, request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        """
        Make an HTTP request on this application
        """

        # WSGI environment
        if environ is None:
            environ = {}
        environ['REQUEST_METHOD'] = request_method
        environ['PATH_INFO'] = path_info
        environ.setdefault('SCRIPT_NAME', '')
        environ.setdefault('QUERY_STRING', query_string)
        environ.setdefault('SERVER_NAME', 'localhost')
        environ.setdefault('SERVER_PORT', '80')
        if 'wsgi.input' not in environ:
            environ['wsgi.input'] = BytesIO(wsgi_input)

        # Capture the response status and headers
        status, headers = '', []
        def start_response(status_, headers_):
            nonlocal status, headers
            status, headers = status_, headers_ # pylint: disable=unused-variable

        # Make the request
        response = self(environ, start_response)
        return status, headers, b''.join(response)


class Context(object):
    """
    Chisel request context
    """

    __slots__ = ('app', 'environ', '_start_response', 'url_args', 'log', 'headers')

    def __init__(self, app, environ=None, start_response=None, url_args=None):
        self.app = app
        self.environ = environ or {}
        self._start_response = start_response
        self.url_args = url_args
        self.headers = OrderedDict()

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
        if self._start_response is not None:
            self._start_response(status, list(chain(headers, self.headers.items())))

    def add_header(self, key, value):
        """
        Add a response header
        """
        assert isinstance(key, str)
        assert isinstance(value, str)
        self.headers[key] = value

    def response(self, status, content_type, content, headers=None):
        """
        Send an HTTP response
        """
        assert not isinstance(content, str) and not isinstance(content, bytes), \
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

    def response_json(self, status, response, content_type='application/json', encoding='utf-8', headers=None, jsonp=None):
        """
        Send a JSON response
        """
        encoder = JSONEncoder(check_circular=self.app.validate_output,
                              allow_nan=False,
                              sort_keys=True,
                              indent=2 if self.app.pretty_output else None,
                              separators=(',', ': ') if self.app.pretty_output else (',', ':'))
        content = encoder.encode(response)
        if jsonp:
            content_list = [jsonp.encode(encoding), b'(', content.encode(encoding), b');']
        else:
            content_list = [content.encode(encoding)]
        return self.response(status, content_type, content_list, headers=headers)

    def reconstruct_url(self, path_info=None, query_string=None):
        """
        Reconstructs the request URL using the algorithm provided by PEP3333
        """

        environ = self.environ
        url = environ['wsgi.url_scheme']+'://'

        if environ.get('HTTP_HOST'):
            url += environ['HTTP_HOST']
        else:
            url += environ['SERVER_NAME']

            if environ['wsgi.url_scheme'] == 'https':
                if environ['SERVER_PORT'] != '443':
                    url += ':' + environ['SERVER_PORT']
            else:
                if environ['SERVER_PORT'] != '80':
                    url += ':' + environ['SERVER_PORT']

        url += quote(environ.get('SCRIPT_NAME', ''))
        if path_info is None:
            url += quote(environ.get('PATH_INFO', ''))
        else:
            url += path_info
        if query_string is None:
            if environ.get('QUERY_STRING'):
                url += '?' + environ['QUERY_STRING']
        else:
            encoded_query_string = encode_query_string(query_string)
            if encoded_query_string:
                url += '?' + encoded_query_string

        return url
