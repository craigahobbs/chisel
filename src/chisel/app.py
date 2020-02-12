# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from datetime import datetime, timedelta
from http import HTTPStatus
from io import BytesIO
import logging
import re
from urllib.parse import quote, unquote

from .util import encode_query_string, JSONEncoder


# Regular expression for matching URL arguments
RE_URL_ARG = re.compile(r'/\{([A-Za-z]\w*)\}')
RE_URL_ARG_ESC = re.compile(r'/\\{([A-Za-z]\w*)\\}')


class Application:
    """
    TODO
    """

    __slots__ = (
        'log_level',
        'log_format',
        'pretty_output',
        'validate_output',
        'requests',
        '__request_urls',
        '__request_regex'
    )

    def __init__(self):

        #: TODO
        self.log_level = logging.WARNING

        #: TODO
        self.log_format = '%(levelname)s [%(process)s / %(thread)s] %(message)s'

        #: TODO
        self.pretty_output = False

        #: TODO
        self.validate_output = True

        #: TODO
        self.requests = {}

        self.__request_urls = {}
        self.__request_regex = []

    def add_request(self, request):
        """
        TODO
        """

        # Duplicate request name?
        if request.name in self.requests:
            raise ValueError(f'redefinition of request "{request.name}"')
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
                    raise ValueError(f'redefinition of request URL "{url}"')
                self.__request_urls[request_key] = request

    def add_requests(self, requests):
        """
        TODO
        """

        for request in requests:
            self.add_request(request)

    def __call__(self, environ, start_response):
        """
        TODO
        """

        # Match the request by method and exact URL
        path_info = environ['PATH_INFO']
        request_method = environ['REQUEST_METHOD'].upper()
        is_head = (request_method == 'HEAD')
        if is_head:
            request_method = environ['REQUEST_METHOD'] = 'GET'
        request, url_args = self.__request_urls.get((request_method, path_info)), None
        if request is None:

            # Match the request by method and URL regex
            request, url_args = next(
                (
                    (request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in request_match.groupdict().items()})
                    for request, request_match in
                    (
                        (request, regex.match(path_info)) for method, regex, request in self.__request_regex
                        if method is not None and method == request_method
                    )
                    if request_match
                ),
                (None, None)
            )
            if request is None:

                # Match the request by exact URL (any method)
                request, url_args = self.__request_urls.get((None, path_info)), None
                if request is None:

                    # Match the request by URL regex (any method)
                    request, url_args = next(
                        (
                            (request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in request_match.groupdict().items()})
                            for request, request_match in
                            (
                                (request, regex.match(path_info)) for method, regex, request in self.__request_regex
                                if method is None
                            )
                            if request_match
                        ),
                        (None, None)
                    )

        # Create the request context
        ctx = environ[Context.ENVIRON_CTX] = Context(self, environ, start_response, url_args)

        # Request not found?
        if request is None:
            if any(path == path_info for _, path in self.__request_urls) or \
               any(regex.match(path_info) for _, regex, _ in self.__request_regex):
                response = ctx.response_text(HTTPStatus.METHOD_NOT_ALLOWED)
            else:
                response = ctx.response_text(HTTPStatus.NOT_FOUND)
        else:
            # Handle the request
            try:
                response = request(ctx.environ, ctx.start_response)
            except: # pylint: disable=bare-except
                ctx.log.exception('exception raised by request "%s"', request.name)
                response = ctx.response_text(HTTPStatus.INTERNAL_SERVER_ERROR)

        if is_head:
            return []
        return response

    def request(self, request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        """
        TODO
        """

        request_environ = Context.create_environ(request_method, path_info, query_string, wsgi_input, environ=environ)
        start_response = StartResponse()
        response = self(request_environ, start_response)
        return start_response.status, start_response.headers, b''.join(response)


class Context:
    """
    TODO
    """

    __slots__ = ('app', 'environ', '_start_response', 'url_args', 'log', 'headers')

    #: TODO
    ENVIRON_CTX = 'chisel.ctx'

    def __init__(self, app, environ=None, start_response=None, url_args=None):

        #: TODO
        self.app = app

        #: TODO
        self.environ = environ or {}

        self._start_response = start_response

        #: TODO
        self.url_args = url_args

        #: TODO
        self.headers = {}

        #: TODO
        self.log = logging.getLoggerClass()('')
        self.log.setLevel(app.log_level)
        wsgi_errors = environ.get('wsgi.errors') if environ else None
        if wsgi_errors is None:
            handler = logging.NullHandler()
        else:
            handler = logging.StreamHandler(wsgi_errors)
        if callable(app.log_format):
            handler.setFormatter(app.log_format(self))
        else:
            handler.setFormatter(logging.Formatter(app.log_format))
        self.log.addHandler(handler)

    @staticmethod
    def create_environ(request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        """
        TODO
        """

        if environ is None:
            environ = {}
        environ.setdefault('REQUEST_METHOD', request_method)
        environ.setdefault('PATH_INFO', path_info)
        environ.setdefault('QUERY_STRING', query_string if isinstance(query_string, str) else encode_query_string(query_string))
        environ.setdefault('SCRIPT_NAME', '')
        environ.setdefault('SERVER_NAME', 'localhost')
        environ.setdefault('SERVER_PORT', '80')
        environ.setdefault('wsgi.input', BytesIO(wsgi_input))
        environ.setdefault('wsgi.url_scheme', 'http')
        return environ

    def start_response(self, status, headers):
        """
        TODO
        """

        if not isinstance(status, str):
            status = f'{status.value} {status.phrase}'
        for key, value in headers:
            self.add_header(key, value)
        self._start_response(status, sorted(self.headers.items()))

    def add_header(self, key, value):
        """
        TODO
        """

        assert isinstance(key, str), 'header key must be of type str'
        assert isinstance(value, str), 'header value must be of type str'
        self.headers[key] = value

    def add_cache_headers(self, control=None, ttl_seconds=None, utcnow=None):
        """
        TODO
        """

        if self.environ.get('REQUEST_METHOD') == 'GET':
            if control is None:
                assert ttl_seconds is None
                self.add_header('Cache-Control', 'no-cache')
            else:
                assert control in ('public', 'private')
                assert isinstance(ttl_seconds, int) and ttl_seconds > 0
                self.add_header('Cache-Control', f'{control},max-age={ttl_seconds}')
                if utcnow is None:
                    utcnow = datetime.utcnow()
                self.add_header('Expires', (utcnow + timedelta(seconds=ttl_seconds)).strftime('%a, %d %b %Y %H:%M:%S GMT'))

    def response(self, status, content_type, content, headers=None):
        """
        TODO
        """

        assert not isinstance(content, (str, bytes)), 'response content cannot be of type str or bytes'
        response_headers = [('Content-Type', content_type)]
        if headers:
            response_headers.extend(headers)
        self.start_response(status, response_headers)
        return content

    def response_text(self, status, text=None, content_type='text/plain', encoding='utf-8', headers=None):
        """
        TODO
        """

        if text is None:
            if isinstance(status, str):
                text = status
            else:
                text = status.phrase
        return self.response(status, content_type, [text.encode(encoding)], headers=headers)

    def response_json(self, status, response, content_type='application/json', encoding='utf-8', headers=None, jsonp=None):
        """
        TODO
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

    def reconstruct_url(self, path_info=None, query_string=None, relative=False):
        """
        TODO
        """

        environ = self.environ
        if relative:
            url = ''
        else:
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


class StartResponse:
    """
    TODO
    """

    __slots__ = ('status', 'headers')

    def __init__(self):
        self.status = None
        self.headers = None

    def __call__(self, status, headers):
        assert self.status is None and self.headers is None
        self.status = status
        self.headers = headers
