# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import datetime, timedelta
import logging
import re
from urllib.parse import quote, unquote

from .app_defs import Environ, HTTPStatus, StartResponse
from .request import Request
from .spec import SpecParser
from .url import encode_query_string
from .util import JSONEncoder


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

    def add_request(self, request):
        """
        Add a request object
        """

        # Duplicate request name?
        if request.name in self.requests:
            raise ValueError('redefinition of request "{0}"'.format(request.name))
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
                    raise ValueError('redefinition of request URL "{0}"'.format(url))
                self.__request_urls[request_key] = request

        # Make the request app-aware at load-time
        request.onload(self)

    def load_requests(self, package, parent_package=None):
        """
        Recursively import all requests in a directory
        """
        for request in Request.import_requests(package, parent_package):
            self.add_request(request)

    def load_specs(self, spec_path, spec_ext='.chsl', finalize=True):
        """
        Load a spec file or directory
        """
        self.specs.load(spec_path, spec_ext, finalize)

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
                (
                    (request, regex.match(path_info)) for method, regex, request in self.__request_regex
                    if method is not None and method == request_method
                )
                if request_match), (None, None))
            if request is None:
                request, url_args = self.__request_urls.get((None, path_info)), None
                if request is None:
                    request, url_args = next((
                        (request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in request_match.groupdict().items()})
                        for request, request_match in
                        (
                            (request, regex.match(path_info)) for method, regex, request in self.__request_regex
                            if method is None
                        )
                        if request_match
                    ), (None, None))

        # Create the request context
        ctx = environ[Environ.CTX] = Context(self, environ, start_response, url_args)

        # Request not found?
        if request is None:
            if any(path == path_info for _, path in self.__request_urls.keys()) or \
               any(regex.match(path_info) for _, regex, _ in self.__request_regex):
                return ctx.response_text(HTTPStatus.METHOD_NOT_ALLOWED)
            else:
                return ctx.response_text(HTTPStatus.NOT_FOUND)

        # Handle the request
        try:
            return request(ctx.environ, ctx.start_response)
        except: # pylint: disable=bare-except
            ctx.log.exception('exception raised by request "%s"', request.name)
            return ctx.response_text(HTTPStatus.INTERNAL_SERVER_ERROR)

    def request(self, request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        request_environ = Environ.create(request_method, path_info, query_string, wsgi_input, environ=environ)
        start_response = StartResponse()
        response = self(request_environ, start_response)
        return start_response.status, start_response.headers, b''.join(response)


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
        self.headers = {}

        # Create the logger
        self.log = logging.getLoggerClass()('')
        self.log.setLevel(app.log_level)
        wsgi_errors = environ.get('wsgi.errors') if environ else None
        if wsgi_errors is None:
            handler = logging.NullHandler()
        else:
            handler = logging.StreamHandler(wsgi_errors)
        if hasattr(app.log_format, '__call__'):
            handler.setFormatter(app.log_format(self))
        else:
            handler.setFormatter(logging.Formatter(app.log_format))
        self.log.addHandler(handler)

    def start_response(self, status, headers):
        if not isinstance(status, str):
            status = str(status.value) + ' ' + status.phrase
        for key, value in headers:
            self.add_header(key, value)
        self._start_response(status, sorted(self.headers.items()))

    def add_header(self, key, value):
        """
        Add a response header
        """

        assert isinstance(key, str), 'header key must be of type str'
        assert isinstance(value, str), 'header value must be of type str'
        self.headers[key] = value

    def add_cache_headers(self, control=None, ttl_seconds=None, utcnow=None):
        if self.environ.get('REQUEST_METHOD') == 'GET':
            if control is None:
                assert ttl_seconds is None
                self.add_header('Cache-Control', 'no-cache')
            else:
                assert control in ('public', 'private')
                assert isinstance(ttl_seconds, int) and ttl_seconds > 0
                self.add_header('Cache-Control', '{0},max-age={1}'.format(control, ttl_seconds))
                if utcnow is None:
                    utcnow = datetime.utcnow()
                self.add_header('Expires', (utcnow + timedelta(seconds=ttl_seconds)).strftime('%a, %d %b %Y %H:%M:%S GMT'))

    def response(self, status, content_type, content, headers=None):
        """
        Send an HTTP response
        """

        assert not isinstance(content, (str, bytes)), 'response content cannot be of type str or bytes'
        response_headers = [('Content-Type', content_type)]
        if headers:
            response_headers.extend(headers)
        self.start_response(status, response_headers)
        return content

    def response_text(self, status, text=None, content_type='text/plain', encoding='utf-8', headers=None):
        """
        Send a plain-text response
        """

        if text is None:
            if isinstance(status, str):
                text = status
            else:
                text = status.phrase
        return self.response(status, content_type, [text.encode(encoding)], headers=headers)

    def response_json(self, status, response, content_type='application/json', encoding='utf-8', headers=None, jsonp=None):
        """
        Send a JSON response
        """
        encoder = JSONEncoder(
            check_circular=self.app.validate_output,
            allow_nan=False,
            sort_keys=True,
            indent=2 if self.app.pretty_output else None,
            separators=(',', ': ') if self.app.pretty_output else (',', ':')
        )
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
        url = environ['wsgi.url_scheme'] + '://'

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
            if query_string:
                if isinstance(query_string, str):
                    url += '?' + query_string
                else:
                    url += '?' + encode_query_string(query_string)

        return url
