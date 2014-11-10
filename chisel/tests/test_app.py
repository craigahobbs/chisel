#
# Copyright (C) 2012-2014 Craig Hobbs
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

from chisel import Application
from chisel.compat import StringIO

import logging
import os
import sys
import types
import unittest


# Main WSGI application callable-object tests
class TestAppApplication(unittest.TestCase):

    def setUp(self):

        class MyApplication(Application):
            def __init__(self):
                Application.__init__(self)
                self.loadSpecs(os.path.join(os.path.dirname(__file__), 'test_app_files'))
                self.loadRequests(os.path.join(os.path.dirname(__file__), 'test_app_files'))
                self.logLevel = logging.INFO

        self.app = MyApplication()

        self.assertTrue('test_app_files' not in sys.modules)
        self.assertTrue('module' not in sys.modules)
        self.assertTrue(isinstance(sys.modules['chisel.tests.test_app_files'], types.ModuleType))
        self.assertTrue(isinstance(sys.modules['chisel.tests.test_app_files.module'], types.ModuleType))


    def test_app_loadRequests_importError(self):
        sys_path = sys.path
        try:
            sys.path = []
            self.app.loadRequests(os.path.join(os.path.dirname(__file__), 'test_app_files'))
        except ImportError as e:
            self.assertEqual(str(e), "'/home/craig/src/chisel/chisel/tests/test_app_files' not found on system path")
        else:
            self.fail()
        finally:
            sys.path = sys_path


    def test_app_call(self):

        # Test WSGI environment
        environ = {
            'SCRIPT_FILENAME': os.path.join(__file__),
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/myAction',
            'wsgi.errors': StringIO()
            }
        startResponseData = {
            'status': [],
            'headers': []
            }
        def startResponse(status, headers):
            startResponseData['status'].append(status)
            startResponseData['headers'].append(headers)

        # Successfully create and call the application
        responseParts = self.app(environ, startResponse)
        self.assertEqual(startResponseData['status'], ['200 OK'])
        self.assertEqual(startResponseData['headers'], [[('Content-Type', 'application/json'), ('Content-Length', '2')]])
        self.assertEqual(list(responseParts), ['{}'.encode('utf-8')])
        self.assertTrue('Some info' not in environ['wsgi.errors'].getvalue())
        self.assertTrue('A warning...' in environ['wsgi.errors'].getvalue())


    def test_app_call_generator(self):

        # Test WSGI environment
        environ = {
            'SCRIPT_FILENAME': os.path.join(__file__),
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/generatorResponse',
            'wsgi.errors': StringIO()
            }
        startResponseData = {
            'status': [],
            'headers': []
            }
        def startResponse(status, headers):
            startResponseData['status'].append(status)
            startResponseData['headers'].append(headers)

        # Request that returns a generator
        def generatorResponse(environ, startResponse):
            def response():
                yield 'Hello'.encode('utf-8')
                yield 'World'.encode('utf-8')
            ctx = environ[Application.ENVIRON_APP]
            return ctx.response('200 OK', 'text/plain', response())

        self.app.addRequest(generatorResponse)

        # Successfully create and call the application
        responseParts = self.app(environ, startResponse)
        self.assertEqual(startResponseData['status'], ['200 OK'])
        self.assertEqual(startResponseData['headers'], [[('Content-Type', 'text/plain')]])
        self.assertEqual(list(responseParts), ['Hello'.encode('utf-8'), 'World'.encode('utf-8')])


    def test_app_call_stringResponse(self):

        # Test WSGI environment
        environ = {
            'SCRIPT_FILENAME': os.path.join(__file__),
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/stringResponse',
            'wsgi.errors': StringIO()
            }
        startResponseData = {
            'status': [],
            'headers': []
            }
        def startResponse(status, headers):
            startResponseData['status'].append(status)
            startResponseData['headers'].append(headers)

        # Request that returns a generator
        def stringResponse(environ, startResponse):
            ctx = environ[Application.ENVIRON_APP]
            return ctx.response('200 OK', 'text/plain', 'Hello World')

        self.app.addRequest(stringResponse)

        # Successfully create and call the application
        responseParts = self.app(environ, startResponse)
        self.assertEqual(startResponseData['status'], ['500 Internal Server Error'])
        self.assertEqual(startResponseData['headers'], [[('Content-Type', 'text/plain'), ('Content-Length', '16')]])
        self.assertEqual(list(responseParts), ['Unexpected Error'.encode('utf-8')])
        self.assertTrue('Response of type str, unicode, or bytes received' in environ['wsgi.errors'].getvalue())


    def test_app_request(self):

        # POST
        logStream = StringIO()
        self.app.logFormat = '%(message)s'
        status, headers, response = self.app.request('POST', '/myAction2', wsgiInput = '{"value": 7}', environ = {'wsgi.errors': logStream})
        self.assertEqual(response.decode('utf-8'), '{"result":14}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(logStream.getvalue(), 'In myAction2\n')

        # GET
        status, headers, response = self.app.request('GET', '/myAction2', queryString = 'value=8')
        self.assertEqual(response.decode('utf-8'), '{"result":16}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # HTTP error
        status, headers, response = self.app.request('GET', '/unknownAction')
        self.assertEqual(response.decode('utf-8'), 'Not Found')
        self.assertEqual(status, '404 Not Found')
        self.assertTrue(('Content-Type', 'text/plain') in headers)

        # Request with environ
        status, headers, response = self.app.request('POST', '/myAction2', wsgiInput = '{"value": 9}',
                                                     environ = { 'MYENVIRON': '10' })
        self.assertEqual(response.decode('utf-8'), '{"result":90}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex
        status, headers, response = self.app.request('GET', '/myAction3/123')
        self.assertEqual(response.decode('utf-8'), '{"myArg":"123"}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex - POST
        status, headers, response = self.app.request('POST', '/myAction3/123', wsgiInput = '{}')
        self.assertEqual(response.decode('utf-8'), '{"myArg":"123"}')
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex - duplicate member error
        status, headers, response = self.app.request('GET', '/myAction3/123', queryString = 'myArg=321')
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Duplicate URL argument member \'myArg\'"}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'application/json') in headers)


    def test_app_logFormat_callable(self):

        def myWsgi(environ, start_response):
            ctx = environ[Application.ENVIRON_APP]
            ctx.log.warning('Hello log')
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return ['Hello'.encode('utf-8')]

        class MyFormatter(object):
            def __init__(self, app):
                assert isinstance(app, Application)
            def format(self, record):
                return record.getMessage()
            def formatTime(self, record, datefmt = None):
                return record.getMessage()
            def formatException(self, exc_info):
                return 'Bad'

        app = Application()
        app.addRequest(myWsgi)
        app.logFormat = MyFormatter

        logStream = StringIO()
        status, headers, response = app.request('GET', '/myWsgi', environ = {'wsgi.errors': logStream})
        self.assertEqual(response, 'Hello'.encode('utf-8'))
        self.assertEqual(status, '200 OK')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(logStream.getvalue(), 'Hello log\n')


    def test_app_nested_requests(self):

        def request1(environ, start_response):
            app = environ[Application.ENVIRON_APP]
            return app.responseText('200 OK', '7')

        def request2(environ, start_response):
            app = environ[Application.ENVIRON_APP]
            status, headers, response = app.request('GET', '/request1')
            return app.responseText('200 OK', str(5 + int(response)))

        app = Application()
        app.addRequest(request1)
        app.addRequest(request2)

        status, headers, response = app.request('GET', '/request2')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response, b'12')
        self.assertTrue(app.environ is None) # Make sure thread state was deleted


    def test_app_request_exception(self):

        def request1(environ, start_response):
            raise Exception('')

        app = Application()
        app.addRequest(request1)

        status, headers, response = app.request('GET', '/request1')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(response, b'Unexpected Error')
