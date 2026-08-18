# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

"""
Chisel WSGI application base class and utilities
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from email.utils import format_datetime
from http import HTTPStatus
from io import BytesIO
from json import JSONEncoder
import logging
import re
from urllib.parse import quote, unquote
from uuid import UUID

from bare_script.include import url_encode_query_string


# Regular expression for matching a URL argument path segment (e.g. "{id}")
RE_URL_ARG = re.compile(r'\{([A-Za-z][A-Za-z0-9_]*)\}')


# JSON encoder with support for datetime, date, Decimal, and UUID objects - raises
# TypeError for unsupported value types (bare-script's value_json serializes them as null)
class _JSONEncoder(JSONEncoder):
    __slots__ = ()

    def default(self, o):
        if isinstance(o, datetime):
            return (o if o.tzinfo else o.replace(tzinfo=timezone.utc)).isoformat()
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, UUID):
            return f'{o}'
        return super().default(o)


class Application:
    """
    The chisel application base class. Override this class if you need additional state for your application (like
    application configuration). Add functionality to your application by adding :class:`~chisel.Request` or
    :class:`~chisel.Action` objects to it using :func:`~chisel.Application.add_request` or
    :func:`~chisel.Application.add_requests`).
    """

    __slots__ = (
        'log_level',
        'log_format',
        'pretty_output',
        'validate_output',
        'requests',
        '__request_urls',
        '__request_paths',
        '__request_regex',
        '__request_regex_urls'
    )

    def __init__(self):

        #: The application's :ref:`logging level <levels>`. The default is :py:data:`logging.WARNING`.
        self.log_level = logging.WARNING

        #: The application's log format string. The default is ``'%(levelname)s [%(process)s / %(thread)s] %(message)s'``.
        self.log_format = '%(levelname)s [%(process)s / %(thread)s] %(message)s'

        #: Set to True for "pretty" request output. Individual requests can use this application state as they see
        #: fit. For example, :class:`~chisel.Action` requests return indented JSON when this value is True. Default is
        #: False.
        self.pretty_output = False

        #: Set to True to validate request output. Individual requests can use this application state as they see fit. For
        #: example, :class:`~chisel.Action` requests schema-validate return content data when this value is True.
        #: Default is True.
        self.validate_output = True

        #: The chisel application's map of request name to :class:`~chisel.Request` object map.
        self.requests = {}

        self.__request_urls = {}
        self.__request_paths = set()
        self.__request_regex = []
        self.__request_regex_urls = set()

    def add_request(self, request):
        """
        Add a :class:`~chisel.Request` to the application. URL arguments (e.g. ``'/documents/{id}'``) must span an
        entire path segment.

        :param ~chisel.Request request: The request object.
        :raises ValueError: If the request name or a request URL is redefined, or if a request URL contains an
            invalid URL argument
        """

        # Duplicate request name?
        if request.name in self.requests:
            raise ValueError(f'redefinition of request "{request.name}"')

        # Validate the request URLs - the request is added only if the entire request is valid
        request_urls = {}
        request_regex = []
        for method, url in request.urls:

            # URL with arguments?
            if '{' in url or '}' in url:

                # Compute the URL regular expression - it is matched with fullmatch
                url_args = []
                regex_segments = []
                for segment in url.split('/'):
                    match_url_arg = RE_URL_ARG.fullmatch(segment)
                    if match_url_arg is not None:
                        url_arg = match_url_arg.group(1)
                        if url_arg in url_args:
                            raise ValueError(f'duplicate URL argument "{segment}" in URL "{url}" of request "{request.name}"')
                        url_args.append(url_arg)
                        regex_segments.append(f'(?P<{url_arg}>[^/]+)')
                    elif '{' in segment or '}' in segment:
                        raise ValueError(f'invalid URL argument "{segment}" in URL "{url}" of request "{request.name}"')
                    else:
                        regex_segments.append(re.escape(segment))

                # Duplicate request URL? URL argument URLs match regardless of argument names.
                url_key = (method, RE_URL_ARG.sub('{}', url))
                if url_key in self.__request_regex_urls or any(key == url_key for key, _ in request_regex):
                    raise ValueError(f'redefinition of request URL "{url}"')
                request_regex.append((url_key, re.compile('/'.join(regex_segments))))
            else:
                # Duplicate request URL?
                url_key = (method, url)
                if url_key in self.__request_urls or url_key in request_urls:
                    raise ValueError(f'redefinition of request URL "{url}"')
                request_urls[url_key] = request

        # Add the request and its URLs
        self.requests[request.name] = request
        self.__request_urls.update(request_urls)
        self.__request_paths.update(path for _, path in request_urls)
        for url_key, url_regex in request_regex:
            self.__request_regex_urls.add(url_key)
            self.__request_regex.append((url_key[0], url_regex, request))

    def add_requests(self, requests):
        """
        Add a series of :class:`~chisel.Request` objects to the application.

        :param ~collections.abc.Iterable(~chisel.Request) requests: A list of :class:`~chisel.Request` objects.
        """

        for request in requests:
            self.add_request(request)

    def match_request(self, request_method, path_info):
        """
        Match an application request by request method and path

        :param request_method: The request method
        :type request_method: str
        :param path_info: The request path
        :type path_info: str
        :return: A tuple of :class:`~chisel.Request` and URL argument :class:`dict`. If the request is None,
            there is no matching request. If the URL argument dict is None, there are no URL arguments.
        :rtype: tuple(chisel.Request or None, dict or None)
        """

        # Match the request by exact URL and method
        request = self.__request_urls.get((request_method, path_info))
        if request is not None:
            return request, None

        # Match the request by URL regular expression and method
        for method, regex, request in self.__request_regex:
            if method is not None and method == request_method:
                match_path = regex.fullmatch(path_info)
                if match_path is not None:
                    return request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in match_path.groupdict().items()}

        # Match the request by exact URL (any method)
        request = self.__request_urls.get((None, path_info))
        if request is not None:
            return request, None

        # Match the request by URL regular expression (any method)
        for method, regex, request in self.__request_regex:
            if method is None:
                match_path = regex.fullmatch(path_info)
                if match_path is not None:
                    return request, {unquote(url_arg): unquote(url_value) for url_arg, url_value in match_path.groupdict().items()}

        # No matching request
        return None, None

    def __call__(self, environ, start_response):
        """
        The chisel application WSGI callback. When the application receives an HTTP request, this method matches the
        appropriate :class:`~chisel.Request` object and then calls its :func:`~chisel.Request.__call__` method. The
        application and URL path arguments (e.g. ``'/documents/{id}'``) are made available to the request through the
        request's :class:`~chisel.Context` object.

        :param dict environ: The :pep:`WSGI <3333>` environ dictionary
        :param ~collections.abc.Callable start_response: The :pep:`WSGI <3333>` start-response callable
        :returns: The WSGI content iterable
        """

        # HEAD request?
        request_method = environ['REQUEST_METHOD'].upper()
        is_head = (request_method == 'HEAD')
        if is_head:
            request_method = environ['REQUEST_METHOD'] = 'GET'

        # Match the request by method and exact URL
        path_info = environ['PATH_INFO']
        request, url_args = self.match_request(request_method, path_info)

        # Create the request context
        ctx = environ[Context.ENVIRON_CTX] = Context(self, environ, start_response, url_args)

        # Request not found? The request path exists if it matches an exact URL under any method or a URL regular
        # expression under another method - match_request already tried this method's and any-method's regexes.
        if request is None:
            if path_info in self.__request_paths or \
               any(regex.fullmatch(path_info)
                   for method, regex, _ in self.__request_regex if method is not None and method != request_method):
                response = ctx.response_text(HTTPStatus.METHOD_NOT_ALLOWED)
            else:
                response = ctx.response_text(HTTPStatus.NOT_FOUND)
        else:
            # Handle the request
            try:
                response = request(ctx.environ, ctx.start_response)
            except Exception:
                # A logging failure (e.g. invalid log_format) must not suppress the error response
                try:
                    ctx.log.exception('exception raised by request "%s"', request.name)
                except Exception:
                    pass
                response = ctx.response_text(HTTPStatus.INTERNAL_SERVER_ERROR)

        if is_head:
            # PEP 3333 - the discarded response content must be closed. A close failure must not
            # suppress the HEAD response.
            if hasattr(response, 'close'):
                try:
                    response.close()
                except Exception:
                    pass
            return []
        return response

    def request(self, request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        """
        Execute an application request

        :param str request_method: The HTTP request method string (e.g. ``'GET'``)
        :param str path_info: The request URL path (e.g. ``'/doc/'``)
        :param str query_string: Optional query string
        :param bytes wsgi_input: Optional request content
        :param dict environ: Optional environ dict. If not provided, a minimal default environ is created.
        :returns: Response status, headers, and content bytes
        """

        request_environ = Context.create_environ(request_method, path_info, query_string, wsgi_input, environ=environ)
        start_response = StartResponse()
        response = self(request_environ, start_response)
        return start_response.status, start_response.headers, b''.join(response)


class Context:
    """
    Class to encapsulate HTTP request state. :class:`~chisel.Application` passes a Context object to each request in
    the WSGI environ dict, ``environ[chisel.Context.ENVIRON_CTX]``.

    :param ~chisel.Application app: The chisel application object
    :param dict environ: The :pep:`WSGI <3333>` environ dictionary
    :param ~collections.abc.Callable start_response: The :pep:`WSGI <3333>` start-response callable
    :param dict url_args: The parsed URL arguments dictionary
    """

    __slots__ = ('app', 'environ', '_start_response', 'url_args', '_log', 'headers')

    #: The context WSGI environ key
    ENVIRON_CTX = 'chisel.ctx'

    def __init__(self, app, environ=None, start_response=None, url_args=None):

        #: The :class:`~chisel.Application` serving the request
        self.app = app

        #: The WSGI environ dictionary
        self.environ = environ or {}

        self._start_response = start_response

        #: The URL path arguments, if any
        self.url_args = url_args

        #: The request's header map. These headers are added to the response.
        self.headers = {}

        self._log = None

    @property
    def log(self):
        """
        The python logger instance. Write log messages using this object directly. The logger is created lazily on
        first access using the application's :attr:`~chisel.Application.log_level` and
        :attr:`~chisel.Application.log_format`.
        """

        if self._log is None:
            # Assign the logger before formatting so a callable log_format may access it
            log = self._log = logging.getLoggerClass()('')
            log.setLevel(self.app.log_level)
            wsgi_errors = self.environ.get('wsgi.errors')
            if wsgi_errors is None:
                handler = logging.NullHandler()
            else:
                handler = logging.StreamHandler(wsgi_errors)
            if callable(self.app.log_format):
                handler.setFormatter(self.app.log_format(self))
            else:
                handler.setFormatter(logging.Formatter(self.app.log_format))
            log.addHandler(handler)
        return self._log

    @log.setter
    def log(self, log):
        self._log = log

    @log.deleter
    def log(self):
        self._log = None

    @staticmethod
    def create_environ(request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        """
        Create a minimal, test WSGI environ dict

        :param str request_method: The HTTP request method (e.g. ``'GET'``)
        :param str path_info: The request URL path (e.g. ``'/doc/'``)
        :param str query_string: Optional query string
        :param bytes wsgi_input: Optional request content
        :param dict environ: Optional environ dict. If not provided, a minimal default environ is created.
        :returns: The created environ dict
        """

        if environ is None:
            environ = {}
        environ.setdefault('HTTP_HOST', 'localhost:80')
        environ.setdefault('PATH_INFO', path_info)
        environ.setdefault('QUERY_STRING', query_string if isinstance(query_string, str) else url_encode_query_string(query_string))
        environ.setdefault('REQUEST_METHOD', request_method)
        environ.setdefault('SCRIPT_NAME', '')
        environ.setdefault('SERVER_NAME', 'localhost')
        environ.setdefault('SERVER_PORT', '80')
        environ.setdefault('wsgi.input', BytesIO(wsgi_input))
        environ.setdefault('wsgi.url_scheme', 'http')
        return environ

    def start_response(self, status, headers):
        """
        Call start response on the WSGI request's start_response function. Any headers added using
        :meth:`~chisel.Context.add_header` are included.

        :param status: The response HTTP status (e.g. "HTTPStatus.OK")
        :type status: ~http.HTTPStatus or str
        :param list(tuple) headers: List of key/value header tuples
        """

        if not isinstance(status, str):
            status = f'{status.value} {status.phrase}'
        for key, value in headers:
            self.add_header(key, value)
        self._start_response(status, sorted(self.headers.items()))

    def add_header(self, key, value):
        """
        Add a header key/value to the request's response. Adding a header key again replaces its value - repeated
        response headers (e.g. multiple "Set-Cookie" headers) are not supported.

        >>> @chisel.action(spec='''
        ... action my_action
        ...     urls
        ...         GET
        ... ''')
        ... def my_action(ctx, req):
        ...    ctx.add_header('ETag', 'foo')
        ...    return {}
        ...
        >>> application = chisel.Application()
        >>> application.add_request(my_action)
        >>> application.request('GET', '/my_action')
        ('200 OK', [('Content-Type', 'application/json'), ('ETag', 'foo')], b'{}')

        :param str key: The header key
        :param str value: The header value
        """

        assert isinstance(key, str), 'header key must be of type str'
        assert isinstance(value, str), 'header value must be of type str'
        self.headers[key] = value

    def add_cache_headers(self, control, ttl_seconds=None, utcnow=None):
        """
        Add a cache header to the response. You can specify a public or private cache with a time-to-live. You can specify
        no-cache by passing control as None.

        >>> from datetime import datetime
        >>> from pprint import pprint
        ...
        >>> @chisel.action(spec='''
        ... action my_action
        ...     urls
        ...         GET
        ... ''')
        ... def my_action(ctx, req):
        ...    ctx.add_cache_headers('private', ttl_seconds=300, utcnow=datetime.fromisoformat('2020-05-19T17:19:00-07:00'))
        ...    return {}
        ...
        >>> application = chisel.Application()
        >>> application.add_request(my_action)
        >>> pprint(application.request('GET', '/my_action'))
        ('200 OK',
         [('Cache-Control', 'private,max-age=300'),
          ('Content-Type', 'application/json'),
          ('Expires', 'Wed, 20 May 2020 00:24:00 GMT')],
         b'{}')

        :param str control: ``'public'``, ``'private'``, or None (for no-cache)
        :param int ttl_seconds: Cache duration in seconds. Do not specify for no-cache.
        :param ~datetime.datetime utcnow: A :func:`~datetime.datetime` to use as the current datetime. A naive
            datetime is assumed to be UTC.
        """

        if self.environ.get('REQUEST_METHOD') == 'GET':
            if control is None:
                self.add_header('Cache-Control', 'no-cache')
            else:
                assert control in ('public', 'private')
                assert isinstance(ttl_seconds, int) and not isinstance(ttl_seconds, bool) and ttl_seconds > 0
                self.add_header('Cache-Control', f'{control},max-age={ttl_seconds}')
                if utcnow is None:
                    utcnow = datetime.now(timezone.utc)
                elif utcnow.tzinfo is None:
                    utcnow = utcnow.replace(tzinfo=timezone.utc)
                else:
                    utcnow = utcnow.astimezone(timezone.utc)
                self.add_header('Expires', format_datetime(utcnow + timedelta(seconds=ttl_seconds), usegmt=True))

    def response(self, status, content_type, content, headers=None):
        """
        A generic WSGI response

        >>> from http import HTTPStatus
        ...
        >>> @chisel.action(wsgi_response=True, spec='''
        ... action my_action
        ...     urls
        ...         GET
        ... ''')
        ... def my_action(ctx, req):
        ...    return ctx.response(HTTPStatus.OK, 'text/plain', [b'Hello'])
        ...
        >>> application = chisel.Application()
        >>> application.add_request(my_action)
        >>> application.request('GET', '/my_action')
        ('200 OK', [('Content-Type', 'text/plain')], b'Hello')

        :param status: The HTTP response status
        :type status: ~http.HTTPStatus or str
        :param str content_type: The response content type
        :param ~collections.abc.Iterable(bytes) content: The WSGI response content
        :param list(tuple) headers: Optional list of key/value header tuples to add to the response
        :returns: The WSGI response content iterable
        """

        assert not isinstance(content, (str, bytes)), 'response content cannot be of type str or bytes'
        response_headers = [('Content-Type', content_type)]
        if headers:
            response_headers.extend(headers)
        self.start_response(status, response_headers)
        return content

    def response_text(self, status, text=None, content_type=None, encoding='utf-8', headers=None):
        """
        A plain-text WSGI response

        >>> from http import HTTPStatus
        ...
        >>> @chisel.action(wsgi_response=True, spec='''
        ... action my_action
        ...     urls
        ...         GET
        ... ''')
        ... def my_action(ctx, req):
        ...    return ctx.response_text(HTTPStatus.OK, "Hello")
        ...
        >>> application = chisel.Application()
        >>> application.add_request(my_action)
        >>> application.request('GET', '/my_action')
        ('200 OK', [('Content-Type', 'text/plain; charset=utf-8')], b'Hello')

        :param status: The HTTP response status
        :type status: ~http.HTTPStatus or str
        :param str text: The response text
        :param str content_type: The response content type. The default is "text/plain" with the
            "encoding" parameter's charset.
        :param str encoding: The content encoding. The default is "utf-8".
        :param list(tuple) headers: Optional list of key/value header tuples to add to the response
        """

        if content_type is None:
            content_type = f'text/plain; charset={encoding}'
        if text is None:
            if isinstance(status, str):
                text = status
            else:
                text = status.phrase
        return self.response(status, content_type, [text.encode(encoding)], headers=headers)

    def response_json(self, status, response, content_type='application/json', encoding='utf-8', headers=None):
        """
        A JSON response

        >>> from http import HTTPStatus
        ...
        >>> @chisel.action(wsgi_response=True, spec='''
        ... action my_action
        ...     urls
        ...         GET
        ... ''')
        ... def my_action(ctx, req):
        ...    return ctx.response_json(HTTPStatus.OK, {'a': 5, 'b': 7})
        ...
        >>> application = chisel.Application()
        >>> application.add_request(my_action)
        >>> application.request('GET', '/my_action')
        ('200 OK', [('Content-Type', 'application/json')], b'{"a":5,"b":7}')

        :param status: The HTTP response status
        :type status: ~http.HTTPStatus or str
        :param dict response: The response dictionary
        :param str content_type: The response content type. The default is "application/json".
        :param str encoding: The content encoding. The default is "utf-8".
        :param list(tuple) headers: Optional list of key/value header tuples to add to the response
        """

        encoder = _JSONEncoder(
            check_circular=self.app.validate_output,
            allow_nan=False,
            sort_keys=True,
            indent=2 if self.app.pretty_output else None,
            separators=(',', ': ') if self.app.pretty_output else (',', ':')
        )
        content = encoder.encode(response)
        return self.response(status, content_type, [content.encode(encoding)], headers=headers)

    def reconstruct_url(self, path_info=None, query_string=None, relative=False):
        """
        Reconstruct the request's URL

        >>> application = chisel.Application()
        >>> ctx = chisel.Context(application, chisel.Context.create_environ('GET', '/hello'))
        >>> ctx.reconstruct_url()
        'http://localhost:80/hello'

        :param str path_info: Optional replacement for the URL path
        :param str query_string: Optional replacement for the query string
        :param bool relative: If True, creates a relative URL. Default is False.
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
                    url += '?' + url_encode_query_string(query_string)

        return url


class StartResponse:
    """
    A WSGI start_response callable object that records its status and headers arguments

    >>> def application(environ, start_response):
    ...     start_response('200 OK', [('Content-Type', 'text/plain')])
    ...     return [b'Hello']
    >>> start_response = chisel.app.StartResponse()
    >>> application({}, start_response)
    [b'Hello']
    >>> start_response.status, start_response.headers
    ('200 OK', [('Content-Type', 'text/plain')])
    """

    __slots__ = ('status', 'headers')

    def __init__(self):

        #: The start_response call's status argument
        self.status = None

        #: The start_response call's headers argument
        self.headers = None

    def __call__(self, status, headers):
        assert self.status is None and self.headers is None
        self.status = status
        self.headers = headers
