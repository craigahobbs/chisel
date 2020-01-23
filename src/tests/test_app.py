# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import date, datetime
from http import HTTPStatus
from io import StringIO
import unittest.mock

from chisel import Application, Context, Environ, Request
from chisel.app_defs import StartResponse

from . import TestCase


class TestApplication(TestCase):

    def test_add_request(self):
        app = Application()
        request1 = Request(name='request1')
        request2 = Request(name='request2', method='GET', urls='/request-two')
        request3 = Request(name='request3', method=('GET', 'POST'), urls=('/request3', '/request3/'))
        request4 = Request(name='request4', urls='/request4/{arg}')
        request5 = Request(name='request5', urls=(('GET', '/request5/{arg}'), ('POST', '/request5/{arg}/foo')))
        app.add_request(request1)
        app.add_request(request2)
        app.add_request(request3)
        app.add_request(request4)
        app.add_request(request5)
        self.assertDictEqual(app.requests, {
            'request1': request1,
            'request2': request2,
            'request3': request3,
            'request4': request4,
            'request5': request5
        })
        self.assertDictEqual(app._Application__request_urls, { # pylint: disable=protected-access
            (None, '/request1'): request1,
            ('GET', '/request-two'): request2,
            ('GET', '/request3'): request3,
            ('POST', '/request3'): request3,
            ('GET', '/request3/'): request3,
            ('POST', '/request3/'): request3
        })
        self.assertListEqual(
            [
                (method, regex.pattern.replace('\\/', '/'), request)
                for method, regex, request in app._Application__request_regex # pylint: disable= protected-access
            ],
            [
                (None, '^/request4/(?P<arg>[^/]+)$', request4),
                ('GET', '^/request5/(?P<arg>[^/]+)$', request5),
                ('POST', '^/request5/(?P<arg>[^/]+)/foo$', request5)
            ]
        )

    def test_add_request_redefinition(self):
        app = Application()
        app.add_request(Request(name='my_request'))
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request'))
        self.assertEqual(str(raises.exception), 'redefinition of request "my_request"')

    def test_add_request_url_redefinition(self):
        app = Application()
        app.add_request(Request(name='my_request'))
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request2', urls='/my_request'))
        self.assertEqual(str(raises.exception), 'redefinition of request URL "/my_request"')

    def test_request(self):

        def request1(environ, unused_start_response):
            ctx = environ[Environ.CTX]
            return ctx.response_text(HTTPStatus.OK, 'request1')

        def request2(environ, unused_start_response):
            ctx = environ[Environ.CTX]
            return ctx.response_text(HTTPStatus.OK, 'request2 ' + ctx.url_args['arg'] + ' ' + ctx.url_args.get('arg2', '?'))

        app = Application()
        app.add_request(Request(request1, urls=(
            ('GET', '/request1a'),
            (None, '/request1b')
        )))
        app.add_request(Request(request2, urls=(
            ('GET', '/request2a/{arg}'),
            (None, '/request2b/{arg}/bar/{arg2}/bonk')
        )))

        # Exact method and exact URL
        status, _, response = app.request('GET', '/request1a')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'request1')

        # Wrong method and exact URL
        status, _, response = app.request('POST', '/request1a')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

        # Any method and exact URL
        status, _, response = app.request('GET', '/request1b')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'request1')

        # Exact method and regex URL
        status, _, response = app.request('GET', '/request2a/foo')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'request2 foo ?')

        # Wrong method and regex URL
        status, _, response = app.request('POST', '/request2a/foo')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

        # Any method and regex URL
        status, _, response = app.request('POST', '/request2b/foo/bar/blue/bonk')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'request2 foo blue')

        # URL not found
        status, _, response = app.request('GET', '/request3')
        self.assertEqual(status, '404 Not Found')
        self.assertEqual(response, b'Not Found')

    def test_request_head(self):

        def request(environ, unused_start_response):
            assert environ['REQUEST_METHOD'] == 'GET'
            ctx = environ[Environ.CTX]
            return ctx.response_text(HTTPStatus.OK, 'the response')

        app = Application()
        app.add_request(Request(request, method='GET'))

        status, headers, response = app.request('GET', '/request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'the response')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])

        status, headers, response = app.request('HEAD', '/request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])

    def test_request_args(self):

        def request1(environ, unused_start_response):
            ctx = environ[Environ.CTX]
            self.assertEqual(environ['QUERY_STRING'], 'a=1&b=2')
            self.assertEqual(environ['wsgi.input'].read(), b'hello')
            ctx.log.warning('in request1')
            return ctx.response_text(HTTPStatus.OK, 'request1')

        app = Application()
        app.add_request(Request(request1))

        environ = {'wsgi.errors': StringIO()}
        status, _, response = app.request('GET', '/request1', query_string='a=1&b=2', wsgi_input=b'hello', environ=environ)
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'request1')
        self.assertIn('in request1', environ['wsgi.errors'].getvalue())

    def test_request_nested(self):

        def request1(environ, unused_start_response):
            ctx = environ[Environ.CTX]
            return ctx.response_text(HTTPStatus.OK, '7')

        def request2(environ, unused_start_response):
            ctx = environ[Environ.CTX]
            unused_status, _, response = ctx.app.request('GET', '/request1')
            return ctx.response_text(HTTPStatus.OK, str(5 + int(response)))

        app = Application()
        app.add_request(Request(request1))
        app.add_request(Request(request2))

        status, _, response = app.request('GET', '/request2')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'12')

    def test_request_exception(self):

        def request1(unused_environ, unused_start_response):
            raise Exception('')

        app = Application()
        app.add_request(Request(request1))

        status, headers, response = app.request('GET', '/request1')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(response, b'Internal Server Error')

    def test_request_string_response(self):

        def string_response(environ, unused_start_response):
            ctx = environ[Environ.CTX]
            return ctx.response(HTTPStatus.OK, 'text/plain', 'Hello World')

        app = Application()
        app.add_request(Request(string_response))

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/string_response', environ=environ)
        self.assertEqual(status, '500 Internal Server Error')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])
        self.assertEqual(response, b'Internal Server Error')
        self.assertIn('response content cannot be of type str or bytes', environ['wsgi.errors'].getvalue())

    def test_log_format_callable(self):

        def my_wsgi(environ, start_response):
            ctx = environ[Environ.CTX]
            ctx.log.warning('Hello log')
            start_response(HTTPStatus.OK, [('Content-Type', 'text/plain')])
            return ['Hello'.encode('utf-8')]

        class MyFormatter:

            def __init__(self, ctx):
                assert ctx is not None

            @staticmethod
            def format(record):
                return record.getMessage()

        app = Application()
        app.add_request(Request(my_wsgi))
        app.log_format = MyFormatter

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_wsgi', environ=environ)
        self.assertEqual(response, 'Hello'.encode('utf-8'))
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(environ['wsgi.errors'].getvalue(), 'Hello log\n')


class TestContext(TestCase):

    def test_add_cache_headers(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Environ.CTX] = ctx

        ctx.add_cache_headers()
        self.assertEqual(ctx.headers['Cache-Control'], 'no-cache')
        self.assertNotIn('Expires', ctx.headers)

    def test_add_cache_headers_public(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Environ.CTX] = ctx

        with unittest.mock.patch('chisel.app.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2017, 1, 15, 20, 39, 32)
            ctx.add_cache_headers('public', 60)
        self.assertEqual(ctx.headers['Cache-Control'], 'public,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')

    def test_add_cache_headers_private(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Environ.CTX] = ctx

        with unittest.mock.patch('chisel.app.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2017, 1, 15, 20, 39, 32)
            ctx.add_cache_headers('private', 60)
        self.assertEqual(ctx.headers['Cache-Control'], 'private,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')

    def test_add_cache_headers_non_get(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'POST'
        })
        ctx.environ[Environ.CTX] = ctx

        ctx.add_cache_headers('private', 60)
        self.assertNotIn('Cache-Control', ctx.headers)
        self.assertNotIn('Expires', ctx.headers)

    def test_add_cache_headers_utcnow(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Environ.CTX] = ctx

        ctx.add_cache_headers('public', 60, utcnow=datetime(2017, 1, 15, 20, 39, 32))
        self.assertEqual(ctx.headers['Cache-Control'], 'public,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')

    def test_response(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response(HTTPStatus.OK, 'text/plain', [b'Hello, World!'])
        self.assertEqual(response, [b'Hello, World!'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])

    def test_response_text(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_text(HTTPStatus.OK, 'Hello, World!')
        self.assertEqual(response, [b'Hello, World!'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])

    def test_response_text_status(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_text(HTTPStatus.OK)
        self.assertEqual(response, [b'OK'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])

    def test_response_text_status_str(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_text('200 OK')
        self.assertEqual(response, [b'200 OK'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])

    def test_response_json(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_json(HTTPStatus.OK, {'a': 7, 'b': 'abc', 'c': date(2018, 2, 24)})
        self.assertEqual(response, [b'{"a":7,"b":"abc","c":"2018-02-24"}'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'application/json')])

    def test_response_json_jsonp(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_json(HTTPStatus.OK, {'a': 7, 'b': 'abc', 'c': date(2018, 2, 24)}, jsonp='jsonp')
        self.assertEqual(response, [b'jsonp', b'(', b'{"a":7,"b":"abc","c":"2018-02-24"}', b');'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'application/json')])

    def test_response_headers(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response(HTTPStatus.OK, 'text/plain', [b'Hello, World!'], headers=[('MY_HEADER', 'MY_VALUE')])
        self.assertEqual(response, [b'Hello, World!'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain'), (('MY_HEADER', 'MY_VALUE'))])

    def test_context_reconstruct_url(self):
        app = Application()

        # Minimal HTTP_HOST
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost'
        })
        self.assertEqual(ctx.reconstruct_url(), 'http://localhost')

        # Minimal SERVER_NAME/SERVER_PORT
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80'
        })
        self.assertEqual(ctx.reconstruct_url(), 'http://localhost')

        # HTTP non-80 SERVER_PORT
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8080'
        })
        self.assertEqual(ctx.reconstruct_url(), 'http://localhost:8080')

        # HTTPS
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '443'
        })
        self.assertEqual(ctx.reconstruct_url(), 'https://localhost')

        # HTTPS non-443 SERVER_PORT
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8443'
        })
        self.assertEqual(ctx.reconstruct_url(), 'https://localhost:8443')

        # Complete
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(), 'http://localhost/request?foo=bar')

        # Relative
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(relative=True), '/request?foo=bar')

        # Replace path_info
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(path_info='/other'), 'http://localhost/other?foo=bar')

        # Replace query_string (dict)
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(query_string={'bar': 'foo', 'bonk': 19}), 'http://localhost/request?bar=foo&bonk=19')

        # Remove query_string (dict)
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(query_string={}), 'http://localhost/request')

        # Replace query_string (encoded string)
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(query_string='bar=foo&bonk=19'), 'http://localhost/request?bar=foo&bonk=19')

        # Remove query_string (empty string)
        ctx = Context(app, environ={
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/request',
            'QUERY_STRING': 'foo=bar'
        })
        self.assertEqual(ctx.reconstruct_url(query_string=''), 'http://localhost/request')
