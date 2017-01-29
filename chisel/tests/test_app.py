# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import datetime
from io import StringIO
import logging
import os
import sys
import types
import unittest
import unittest.mock

from chisel import action, Application, Context, Environ, HTTPStatus, Request
from chisel.app_defs import StartResponse


class TestApplication(unittest.TestCase):

    def setUp(self):

        class MyApplication(Application):
            def __init__(self):
                Application.__init__(self)
                self.load_specs(os.path.join(os.path.dirname(__file__), 'test_app_files'))
                self.load_requests('.test_app_files', __package__)
                self.log_level = logging.INFO

        self.app = MyApplication()

        self.assertTrue('test_app_files' not in sys.modules)
        self.assertTrue('module' not in sys.modules)
        self.assertTrue(isinstance(sys.modules['chisel.tests.test_app_files'], types.ModuleType))
        self.assertTrue(isinstance(sys.modules['chisel.tests.test_app_files.module'], types.ModuleType))

    def test_load_requests_error(self):
        try:
            self.app.load_requests('chisel.tests.test_app_files2')
        except ImportError as exc:
            self.assertEqual(str(exc), "No module named 'chisel.tests.test_app_files2'")
        else:
            self.fail()

    def test_request_redefinition(self):
        app = Application()
        app.add_request(Request(name='my_request'))
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request'))
        self.assertEqual(str(raises.exception), 'redefinition of request "my_request"')

    def test_request_url_redefinition(self):
        app = Application()
        app.add_request(Request(name='my_request'))
        with self.assertRaises(ValueError) as raises:
            app.add_request(Request(name='my_request2', urls='/my_request'))
        self.assertEqual(str(raises.exception), 'redefinition of request URL "/my_request"')

    def test_call(self):
        environ = Environ.create('GET', '/my_action')
        environ['wsgi.errors'] = StringIO()
        start_response = StartResponse()
        response = self.app(environ, start_response)
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'application/json')])
        self.assertEqual(response, ['{}'.encode('utf-8')])
        self.assertNotIn('Some info', environ['wsgi.errors'].getvalue())
        self.assertIn('A warning...', environ['wsgi.errors'].getvalue())

    def test_call_generator(self):
        def generator_response(environ, dummy_start_response):
            def response():
                yield 'Hello'.encode('utf-8')
                yield 'World'.encode('utf-8')
            ctx = environ[Environ.CTX]
            return ctx.response(HTTPStatus.OK, 'text/plain', response())

        self.app.add_request(Request(generator_response))

        environ = Environ.create('GET', '/generator_response')
        start_response = StartResponse()
        response = self.app(environ, start_response)
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])
        self.assertEqual(list(response), ['Hello'.encode('utf-8'), 'World'.encode('utf-8')])

    def test_call_string_response(self):

        def string_response(environ, dummy_start_response):
            ctx = environ[Environ.CTX]
            return ctx.response(HTTPStatus.OK, 'text/plain', 'Hello World')

        app = Application()
        app.add_request(Request(string_response))

        # Successfully create and call the application
        environ = Environ.create('GET', '/string_response', environ={'wsgi.errors': StringIO()})
        start_response = StartResponse()
        response_parts = app(environ, start_response)
        self.assertEqual(start_response.status, '500 Internal Server Error')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])
        self.assertEqual(list(response_parts), ['Unexpected Error'.encode('utf-8')])
        self.assertIn('response content cannot be of type str or bytes', environ['wsgi.errors'].getvalue())

    def test_request(self):

        # POST
        self.app.log_format = '%(message)s'
        environ = {'wsgi.errors': StringIO()}
        status, headers, response = self.app.request('POST', '/my_action2', wsgi_input=b'{"value": 7}', environ=environ)
        self.assertEqual(response.decode('utf-8'), '{"result":14}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(environ['wsgi.errors'].getvalue(), 'In my_action2\n')

        # GET
        status, headers, response = self.app.request('GET', '/my_action2', query_string='value=8')
        self.assertEqual(response.decode('utf-8'), '{"result":16}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # GET (dict query string)
        status, headers, response = self.app.request('GET', '/my_action2', query_string={'value': 8})
        self.assertEqual(response.decode('utf-8'), '{"result":16}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # HTTP error
        status, headers, response = self.app.request('GET', '/unknownAction')
        self.assertEqual(response.decode('utf-8'), 'Not Found')
        self.assertEqual(status, '404 Not Found')
        self.assertTrue(('Content-Type', 'text/plain') in headers)

        # Request with environ
        status, headers, response = self.app.request('POST', '/my_action2', wsgi_input=b'{"value": 9}',
                                                     environ={'MYENVIRON': '10'})
        self.assertEqual(response.decode('utf-8'), '{"result":90}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request with environ with QUERY_STRING
        status, headers, response = self.app.request('GET', '/my_action2', query_string='value=8')
        self.assertEqual(response.decode('utf-8'), '{"result":16}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex
        status, headers, response = self.app.request('GET', '/my_action3/123')
        self.assertEqual(response.decode('utf-8'), '{"myArg":"123"}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex - POST
        status, headers, response = self.app.request('POST', '/my_action3/123', wsgi_input=b'{}')
        self.assertEqual(response.decode('utf-8'), '{"myArg":"123"}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex - duplicate member error
        status, headers, response = self.app.request('GET', '/my_action3/123', query_string='myArg=321')
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Duplicate URL argument member \'myArg\'"}')
        self.assertEqual(status, '400 Bad Request')
        self.assertTrue(('Content-Type', 'application/json') in headers)

    def test_log_format_callable(self):

        def my_wsgi(environ, start_response):
            ctx = environ[Environ.CTX]
            ctx.log.warning('Hello log')
            start_response(HTTPStatus.OK, [('Content-Type', 'text/plain')])
            return ['Hello'.encode('utf-8')]

        class MyFormatter(object):
            def __init__(self, ctx):
                assert ctx is not None

            @staticmethod
            def format(record):
                return record.getMessage()

            @staticmethod
            def formatTime(record, dummy_datefmt=None): # pylint: disable=invalid-name
                return record.getMessage()

            @staticmethod
            def formatException(dummy_exc_info): # pylint: disable=invalid-name
                return 'Bad'

        app = Application()
        app.add_request(Request(my_wsgi))
        app.log_format = MyFormatter

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_wsgi', environ=environ)
        self.assertEqual(response, 'Hello'.encode('utf-8'))
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(environ['wsgi.errors'].getvalue(), 'Hello log\n')

    def test_nested_requests(self):

        def request1(environ, dummy_start_response):
            ctx = environ[Environ.CTX]
            return ctx.response_text(HTTPStatus.OK, '7')

        def request2(environ, dummy_start_response):
            ctx = environ[Environ.CTX]
            dummy_status, dummy_headers, response = ctx.app.request('GET', '/request1')
            return ctx.response_text(HTTPStatus.OK, str(5 + int(response)))

        app = Application()
        app.add_request(Request(request1))
        app.add_request(Request(request2))

        status, dummy_headers, response = app.request('GET', '/request2')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'12')

    def test_request_exception(self):

        def request1(dummy_environ, dummy_start_response):
            raise Exception('')

        app = Application()
        app.add_request(Request(request1))

        status, headers, response = app.request('GET', '/request1')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(response, b'Unexpected Error')

    def test_request_url_mix(self):

        @action(urls=[(None, '/action/1')],
                spec='''\
action my_action1
  output
    int number
''')
        def my_action1(dummy_ctx, dummy_req):
            return {'number': 1}

        @action(urls=[('GET', '/action/{dummy_number}')],
                spec='''\
action my_action2
  input
    int dummy_number
  output
    int number
''')
        def my_action2(dummy_ctx, dummy_req):
            return {'number': 2}

        app = Application()
        app.add_request(my_action1)
        app.add_request(my_action2)

        status, dummy_headers, response = app.request('GET', '/action/1')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{"number":2}')

        status, dummy_headers, response = app.request('POST', '/action/1', wsgi_input=b'{}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{"number":1}')

    def test_request_url_method(self):

        @action(urls=[('GET', '/my_action'), ('POST', '/my_action/')],
                spec='''\
action my_action
''')
        def my_action(dummy_ctx, dummy_req):
            pass

        app = Application()
        app.add_request(my_action)

        status, dummy_headers, response = app.request('GET', '/my_action')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{}')

        status, dummy_headers, response = app.request('POST', '/my_action/', wsgi_input=b'{}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{}')

        status, dummy_headers, response = app.request('GET', '/my_action/')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

        status, dummy_headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

        status, dummy_headers, response = app.request('PUT', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

    def test_request_url_method_arg(self):

        @action(urls=[('GET', '/my_action/{a}/{b}'), ('POST', '/my_action/{a}/{b}/')],
                spec='''\
action my_action
  input
    int a
    int b
  output
    int sum
''')
        def my_action(dummy_ctx, req):
            return {'sum': req['a'] + req['b']}

        app = Application()
        app.add_request(my_action)

        status, dummy_headers, response = app.request('GET', '/my_action/3/4')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{"sum":7}')

        status, dummy_headers, response = app.request('POST', '/my_action/3/4/', wsgi_input=b'{}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{"sum":7}')

        status, dummy_headers, response = app.request('GET', '/my_action/3/4/')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

        status, dummy_headers, response = app.request('POST', '/my_action/3/4', wsgi_input=b'{}')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

        status, dummy_headers, response = app.request('PUT', '/my_action/3/4', wsgi_input=b'{}')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(response, b'Method Not Allowed')

    def test_request_url_arg_underscore(self):

        @action(urls=['/my_action/{number_one}/{number_two}'],
                spec='''\
action my_action
  input
    int number_one
    int number_two
  output
    int sum
''')
        def my_action(dummy_ctx, req):
            return {'sum': req['number_one'] + req['number_two']}

        app = Application()
        app.add_request(my_action)

        status, dummy_headers, response = app.request('GET', '/my_action/3/4')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'{"sum":7}')


class TestContext(unittest.TestCase):

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
        content = b'Hello, World!'
        response = ctx.response(HTTPStatus.OK, 'text/plain', [content])
        self.assertEqual(response, [content])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])

    def test_response_text(self):
        app = Application()
        start_response = StartResponse()
        ctx = Context(app, start_response=start_response)
        content = 'Hello, World!'
        response = ctx.response_text(HTTPStatus.OK, content)
        self.assertEqual(response, [content.encode('utf-8')])
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
