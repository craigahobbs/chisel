# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring

from datetime import date, datetime, timezone
from decimal import Decimal
from http import HTTPStatus
from io import StringIO
import logging
from unittest import TestCase
import unittest.mock
from uuid import UUID

from chisel import Application, Context, Request
from chisel.app import StartResponse


class TestApplication(TestCase):

    def test_add_request(self):
        app = Application()
        request1 = Request(name='request1')
        request2 = Request(name='request2', urls=(('GET', '/request-two'),))
        request3 = Request(
            name='request3',
            urls=(('GET', '/request3'), ('POST', '/request3'), ('GET', '/request3/'), ('POST', '/request3/'))
        )
        request4 = Request(name='request4', urls=((None, '/request4/{arg}'),))
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
                (None, '/request4/(?P<arg>[^/]+)', request4),
                ('GET', '/request5/(?P<arg>[^/]+)', request5),
                ('POST', '/request5/(?P<arg>[^/]+)/foo', request5)
            ]
        )


    def test_add_requests(self):
        request1 = Request(name='request1')
        request2 = Request(name='request2', urls=(('GET', '/request-two'),))

        def get_requests():
            yield request1
            yield request2

        app = Application()
        app.add_requests(get_requests())
        self.assertDictEqual(app.requests, {
            'request1': request1,
            'request2': request2
        })
        self.assertDictEqual(app._Application__request_urls, { # pylint: disable=protected-access
            (None, '/request1'): request1,
            ('GET', '/request-two'): request2
        })


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
            app.add_request(Request(name='my_request2', urls=[(None, '/my_request')]))
        self.assertEqual(str(raises.exception), 'redefinition of request URL "/my_request"')
        self.assertNotIn('my_request2', app.requests)

        # Duplicate URL within a single request
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request2', urls=[(None, '/other'), (None, '/other')]))
        self.assertEqual(str(raises.exception), 'redefinition of request URL "/other"')
        self.assertNotIn('my_request2', app.requests)


    def test_add_request_url_arg_redefinition(self):
        app = Application()
        app.add_request(Request(name='my_request', urls=[('GET', '/doc/{id}')]))

        # URL argument URLs match regardless of argument name
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request2', urls=[('GET', '/doc/{name}')]))
        self.assertEqual(str(raises.exception), 'redefinition of request URL "/doc/{name}"')
        self.assertNotIn('my_request2', app.requests)

        # Duplicate URL argument URL within a single request
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request3', urls=[('GET', '/thing/{a}'), ('GET', '/thing/{b}')]))
        self.assertEqual(str(raises.exception), 'redefinition of request URL "/thing/{b}"')
        self.assertNotIn('my_request3', app.requests)


    def test_add_request_url_invalid_argument(self):
        app = Application()

        # URL argument not spanning an entire path segment
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/api/v{version}/thing')]))
        self.assertEqual(str(raises.exception), 'invalid URL argument "v{version}" in URL "/api/v{version}/thing" of request "my_request"')

        # URL argument with a trailing suffix
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/docs/{id}.json')]))
        self.assertEqual(str(raises.exception), 'invalid URL argument "{id}.json" in URL "/docs/{id}.json" of request "my_request"')

        # Stray closing brace
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/api/thing}')]))
        self.assertEqual(str(raises.exception), 'invalid URL argument "thing}" in URL "/api/thing}" of request "my_request"')

        # Invalid URL argument name
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/api/{1arg}')]))
        self.assertEqual(str(raises.exception), 'invalid URL argument "{1arg}" in URL "/api/{1arg}" of request "my_request"')

        # Duplicate URL argument name
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/api/{a}/{a}')]))
        self.assertEqual(str(raises.exception), 'duplicate URL argument "{a}" in URL "/api/{a}/{a}" of request "my_request"')

        # Mid-segment URL argument alongside a valid URL argument
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/api/v{version}/thing/{id}')]))
        self.assertEqual(
            str(raises.exception),
            'invalid URL argument "v{version}" in URL "/api/v{version}/thing/{id}" of request "my_request"'
        )

        # The application is unmodified - the request name can be reused with valid URLs
        self.assertDictEqual(app.requests, {})
        app.add_request(Request(name='my_request', urls=[('GET', '/api/{version}/thing')]))
        self.assertIn('my_request', app.requests)


    def test_add_request_url_invalid_argument_atomic(self):
        app = Application()

        # Valid URLs before the invalid URL are not registered
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request', urls=[('GET', '/ok'), ('GET', '/ok/{a}'), ('GET', '/bad/v{x}/c')]))
        self.assertEqual(str(raises.exception), 'invalid URL argument "v{x}" in URL "/bad/v{x}/c" of request "my_request"')
        self.assertDictEqual(app.requests, {})
        self.assertEqual(app.match_request('GET', '/ok'), (None, None))
        self.assertEqual(app.match_request('GET', '/ok/foo'), (None, None))

        # The request can be re-added with corrected URLs
        request = Request(name='my_request', urls=[('GET', '/ok'), ('GET', '/ok/{a}')])
        app.add_request(request)
        self.assertEqual(app.match_request('GET', '/ok'), (request, None))
        self.assertEqual(app.match_request('GET', '/ok/foo'), (request, {'a': 'foo'}))


    def test_request(self):

        def request1(environ, unused_start_response):
            ctx = environ[Context.ENVIRON_CTX]
            return ctx.response_text(HTTPStatus.OK, 'request1')

        def request2(environ, unused_start_response):
            ctx = environ[Context.ENVIRON_CTX]
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
            ctx = environ[Context.ENVIRON_CTX]
            return ctx.response_text(HTTPStatus.OK, 'the response')

        app = Application()
        app.add_request(Request(request, urls=(('GET', None),)))

        status, headers, response = app.request('GET', '/request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'the response')
        self.assertListEqual(headers, [('Content-Type', 'text/plain; charset=utf-8')])

        status, headers, response = app.request('HEAD', '/request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'')
        self.assertListEqual(headers, [('Content-Type', 'text/plain; charset=utf-8')])


    def test_request_head_close(self):

        class CloseableResponse:
            def __init__(self):
                self.closed = False

            def __iter__(self):
                return iter([b'the response'])

            def close(self):
                self.closed = True

        response_content = CloseableResponse()

        def request(unused_environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return response_content

        app = Application()
        app.add_request(Request(request, urls=(('GET', None),)))

        # GET returns the response content
        status, headers, response = app.request('GET', '/request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'the response')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])
        self.assertFalse(response_content.closed)

        # The discarded HEAD response content is closed
        status, headers, response = app.request('HEAD', '/request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])
        self.assertTrue(response_content.closed)

        # A close failure must not suppress the HEAD response
        class CloseErrorResponse:
            def __iter__(self):
                return iter([b'the response'])

            def close(self):
                raise Exception('close failure')

        def request2(unused_environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return CloseErrorResponse()

        app.add_request(Request(request2, urls=(('GET', '/request2'),)))
        status, headers, response = app.request('GET', '/request2')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'the response')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])

        status, headers, response = app.request('HEAD', '/request2')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'')
        self.assertListEqual(headers, [('Content-Type', 'text/plain')])


    def test_request_args(self):

        def request1(environ, unused_start_response):
            ctx = environ[Context.ENVIRON_CTX]
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
            ctx = environ[Context.ENVIRON_CTX]
            return ctx.response_text(HTTPStatus.OK, '7')

        def request2(environ, unused_start_response):
            ctx = environ[Context.ENVIRON_CTX]
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
        self.assertTrue(('Content-Type', 'text/plain; charset=utf-8') in headers)
        self.assertEqual(response, b'Internal Server Error')


    def test_request_exception_base_exception(self):

        def request1(unused_environ, unused_start_response):
            raise KeyboardInterrupt()

        app = Application()
        app.add_request(Request(request1))

        # Base exceptions are not converted to an error response
        with self.assertRaises(KeyboardInterrupt):
            app.request('GET', '/request1')


    def test_request_exception_log_format_invalid(self):

        def request1(unused_environ, unused_start_response):
            raise Exception('FAIL')

        app = Application()
        app.add_request(Request(request1))
        app.log_format = '%(levelname'

        # An invalid log format must not suppress the error response
        status, headers, response = app.request('GET', '/request1')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'text/plain; charset=utf-8') in headers)
        self.assertEqual(response, b'Internal Server Error')


    def test_request_string_response(self):

        def string_response(environ, unused_start_response):
            ctx = environ[Context.ENVIRON_CTX]
            return ctx.response(HTTPStatus.OK, 'text/plain', 'Hello World')

        app = Application()
        app.add_request(Request(string_response))

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/string_response', environ=environ)
        self.assertEqual(status, '500 Internal Server Error')
        self.assertListEqual(headers, [('Content-Type', 'text/plain; charset=utf-8')])
        self.assertEqual(response, b'Internal Server Error')
        self.assertIn('response content cannot be of type str or bytes', environ['wsgi.errors'].getvalue())


    def test_log_format_callable(self):

        def my_wsgi(environ, start_response):
            ctx = environ[Context.ENVIRON_CTX]
            ctx.log.warning('Hello log')
            start_response(HTTPStatus.OK, [('Content-Type', 'text/plain')])
            return ['Hello'.encode('utf-8')]

        class MyFormatter:

            def __init__(self, ctx):
                # The context's logger is assigned and accessible during formatter creation
                assert isinstance(ctx.log, logging.Logger)

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
        ctx.environ[Context.ENVIRON_CTX] = ctx

        ctx.add_cache_headers(None)
        self.assertEqual(ctx.headers['Cache-Control'], 'no-cache')
        self.assertNotIn('Expires', ctx.headers)


    def test_add_cache_headers_public(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Context.ENVIRON_CTX] = ctx

        with unittest.mock.patch('chisel.app.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2017, 1, 15, 20, 39, 32, tzinfo=timezone.utc)
            ctx.add_cache_headers('public', 60)
        mock_datetime.now.assert_called_once_with(timezone.utc)
        self.assertEqual(ctx.headers['Cache-Control'], 'public,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')


    def test_add_cache_headers_private(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Context.ENVIRON_CTX] = ctx

        with unittest.mock.patch('chisel.app.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2017, 1, 15, 20, 39, 32, tzinfo=timezone.utc)
            ctx.add_cache_headers('private', 60)
        mock_datetime.now.assert_called_once_with(timezone.utc)
        self.assertEqual(ctx.headers['Cache-Control'], 'private,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')


    def test_add_cache_headers_non_get(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'POST'
        })
        ctx.environ[Context.ENVIRON_CTX] = ctx

        ctx.add_cache_headers('private', 60)
        self.assertNotIn('Cache-Control', ctx.headers)
        self.assertNotIn('Expires', ctx.headers)


    def test_add_cache_headers_utcnow(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Context.ENVIRON_CTX] = ctx

        ctx.add_cache_headers('public', 60, utcnow=datetime(2017, 1, 15, 20, 39, 32, tzinfo=timezone.utc))
        self.assertEqual(ctx.headers['Cache-Control'], 'public,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')


    def test_add_cache_headers_utcnow_naive(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Context.ENVIRON_CTX] = ctx

        # A naive datetime is assumed to be UTC
        ctx.add_cache_headers('public', 60, utcnow=datetime(2017, 1, 15, 20, 39, 32))
        self.assertEqual(ctx.headers['Cache-Control'], 'public,max-age=60')
        self.assertEqual(ctx.headers['Expires'], 'Sun, 15 Jan 2017 20:40:32 GMT')


    def test_add_cache_headers_ttl_invalid(self):
        app = Application()
        ctx = Context(app, environ={
            'REQUEST_METHOD': 'GET'
        })
        ctx.environ[Context.ENVIRON_CTX] = ctx

        # A boolean ttl_seconds is not an integer
        with self.assertRaises(AssertionError):
            ctx.add_cache_headers('public', True)
        self.assertNotIn('Cache-Control', ctx.headers)
        self.assertNotIn('Expires', ctx.headers)


    def test_log_lazy(self):
        app = Application()
        ctx = Context(app, environ={})
        log = ctx.log
        self.assertIs(ctx.log, log)

        # The log attribute may be set directly
        other_log = logging.getLoggerClass()('other')
        ctx.log = other_log
        self.assertIs(ctx.log, other_log)

        # Deleting the log attribute resets it to lazy creation
        del ctx.log
        self.assertIsNot(ctx.log, other_log)
        self.assertIsInstance(ctx.log, logging.Logger)


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
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])


    def test_response_text_status(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_text(HTTPStatus.OK)
        self.assertEqual(response, [b'OK'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])


    def test_response_text_status_str(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_text('200 OK')
        self.assertEqual(response, [b'200 OK'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])


    def test_response_text_content_type(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_text(HTTPStatus.OK, 'Hello', content_type='text/html')
        self.assertEqual(response, [b'Hello'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/html')])


    def test_response_text_encoding(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)

        # The default content type's charset follows the encoding
        response = ctx.response_text(HTTPStatus.OK, 'Hello', encoding='latin-1')
        self.assertEqual(response, [b'Hello'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=latin-1')])


    def test_response_json(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_json(HTTPStatus.OK, {
            'a': 7,
            'b': 'abc',
            'c': date(2018, 2, 24),
            'd': datetime(2018, 2, 24, 10, 30),
            'e': datetime(2018, 2, 24, 10, 30, tzinfo=timezone.utc),
            'f': Decimal('7.5'),
            'g': UUID('8daeb11e-3a83-4554-8593-f9291b1cf491')
        })
        self.assertEqual(response, [
            b'{"a":7,"b":"abc","c":"2018-02-24","d":"2018-02-24T10:30:00+00:00","e":"2018-02-24T10:30:00+00:00",'
            b'"f":7.5,"g":"8daeb11e-3a83-4554-8593-f9291b1cf491"}'
        ])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'application/json')])


    def test_response_json_content_type(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        response = ctx.response_json(HTTPStatus.OK, {'a': 7}, content_type='application/schema+json')
        self.assertEqual(response, [b'{"a":7}'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'application/schema+json')])


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
