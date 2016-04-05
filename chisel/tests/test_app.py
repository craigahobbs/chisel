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

from io import StringIO
import logging
import os
import re
import sys
import types
import unittest

from chisel import action, Application, ENVIRON_CTX


class TestAppApplication(unittest.TestCase):

    def setUp(self):

        class MyApplication(Application):
            def __init__(self):
                Application.__init__(self)
                self.load_specs(os.path.join(os.path.dirname(__file__), 'test_app_files'))
                self.load_requests(os.path.join(os.path.dirname(__file__), 'test_app_files'))
                self.log_level = logging.INFO

        self.app = MyApplication()

        self.assertTrue('test_app_files' not in sys.modules)
        self.assertTrue('module' not in sys.modules)
        self.assertTrue(isinstance(sys.modules['chisel.tests.test_app_files'], types.ModuleType))
        self.assertTrue(isinstance(sys.modules['chisel.tests.test_app_files.module'], types.ModuleType))

    def test_load_requests_error(self):
        sys_path = sys.path
        try:
            sys.path = []
            self.app.load_requests(os.path.join(os.path.dirname(__file__), 'test_app_files'))
        except ImportError as exc:
            self.assertTrue(re.search("'.*?' not found on system path", str(exc)))
        else:
            self.fail()
        finally:
            sys.path = sys_path

    def test_call(self):

        # Test WSGI environment
        environ = {
            'SCRIPT_FILENAME': os.path.join(__file__),
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/my_action',
            'wsgi.errors': StringIO()
            }
        start_response_data = {
            'status': [],
            'headers': []
            }

        def start_response(status, headers):
            start_response_data['status'].append(status)
            start_response_data['headers'].append(headers)

        # Successfully create and call the application
        response_parts = self.app(environ, start_response)
        self.assertEqual(start_response_data['status'], ['200 OK'])
        self.assertEqual(start_response_data['headers'], [[('Content-Type', 'application/json'), ('Content-Length', '2')]])
        self.assertEqual(list(response_parts), ['{}'.encode('utf-8')])
        self.assertTrue('Some info' not in environ['wsgi.errors'].getvalue())
        self.assertTrue('A warning...' in environ['wsgi.errors'].getvalue())

    def test_call_generator(self):

        # Test WSGI environment
        environ = {
            'SCRIPT_FILENAME': os.path.join(__file__),
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/generator_response',
            'wsgi.errors': StringIO()
            }
        start_response_data = {
            'status': [],
            'headers': []
            }

        def start_response(status, headers):
            start_response_data['status'].append(status)
            start_response_data['headers'].append(headers)

        # Request that returns a generator
        def generator_response(environ, dummy_start_response):
            def response():
                yield 'Hello'.encode('utf-8')
                yield 'World'.encode('utf-8')
            ctx = environ[ENVIRON_CTX]
            return ctx.response('200 OK', 'text/plain', response())

        self.app.add_request(generator_response)

        # Successfully create and call the application
        response_parts = self.app(environ, start_response)
        self.assertEqual(start_response_data['status'], ['200 OK'])
        self.assertEqual(start_response_data['headers'], [[('Content-Type', 'text/plain')]])
        self.assertEqual(list(response_parts), ['Hello'.encode('utf-8'), 'World'.encode('utf-8')])

    def test_call_string_response(self):

        # Test WSGI environment
        environ = {
            'SCRIPT_FILENAME': os.path.join(__file__),
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/string_response',
            'wsgi.errors': StringIO()
            }
        start_response_data = {
            'status': [],
            'headers': []
            }

        def start_response(status, headers):
            start_response_data['status'].append(status)
            start_response_data['headers'].append(headers)

        # Request that returns a generator
        def string_response(environ, dummy_start_response):
            ctx = environ[ENVIRON_CTX]
            return ctx.response('200 OK', 'text/plain', 'Hello World')

        self.app.add_request(string_response)

        # Successfully create and call the application
        response_parts = self.app(environ, start_response)
        self.assertEqual(start_response_data['status'], ['500 Internal Server Error'])
        self.assertEqual(start_response_data['headers'], [[('Content-Type', 'text/plain'), ('Content-Length', '16')]])
        self.assertEqual(list(response_parts), ['Unexpected Error'.encode('utf-8')])
        self.assertTrue('Response content of type str or bytes received' in environ['wsgi.errors'].getvalue())

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
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'application/json') in headers)

    def test_log_format_callable(self):

        def my_wsgi(environ, start_response):
            ctx = environ[ENVIRON_CTX]
            ctx.log.warning('Hello log')
            start_response('200 OK', [('Content-Type', 'text/plain')])
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
        app.add_request(my_wsgi)
        app.log_format = MyFormatter

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_wsgi', environ=environ)
        self.assertEqual(response, 'Hello'.encode('utf-8'))
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(environ['wsgi.errors'].getvalue(), 'Hello log\n')

    def test_nested_requests(self):

        def request1(environ, dummy_start_response):
            ctx = environ[ENVIRON_CTX]
            return ctx.response_text('200 OK', '7')

        def request2(environ, dummy_start_response):
            ctx = environ[ENVIRON_CTX]
            dummy_status, dummy_headers, response = ctx.app.request('GET', '/request1')
            return ctx.response_text('200 OK', str(5 + int(response)))

        app = Application()
        app.add_request(request1)
        app.add_request(request2)

        status, dummy_headers, response = app.request('GET', '/request2')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'12')

    def test_request_exception(self):

        def request1(dummy_environ, dummy_start_response):
            raise Exception('')

        app = Application()
        app.add_request(request1)

        status, headers, response = app.request('GET', '/request1')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(response, b'Unexpected Error')

    def test_request_url_mix(self):

        @action(urls=['/action/1'],
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
