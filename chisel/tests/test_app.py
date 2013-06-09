#
# Copyright (C) 2012-2013 Craig Hobbs
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
from chisel.compat import StringIO, wsgistr_new

import logging
import os
import unittest


# Main WSGI application callable-object tests
class TestAppApplication(unittest.TestCase):

    def setUp(self):

        self.resourceData = {
            "open": [],
            "close": []
            }
        def resourceTypeOpen(resourceString):
            self.resourceData["open"].append(resourceString)
            return len(self.resourceData["open"])
        def resourceTypeClose(resource):
            self.resourceData["close"].append(resource)

        class MyApplication(Application):
            def init(self):
                self.loadSpecs(os.path.join(os.path.dirname(__file__), "test_app_files"))
                self.loadRequests(os.path.join(os.path.dirname(__file__), "test_app_files"))
                self.addResource("testResource", resourceTypeOpen, resourceTypeClose, "Hello")
                self.addResource("myresource", lambda resourceString: 9, lambda resource: None, "mystring")
                self.logLevel = logging.INFO
                Application.init(self)

        self.app = MyApplication()

    # Test default application functionality
    def test_app_default(self):

        # Test WSGI environment
        environ = {
            "SCRIPT_FILENAME": os.path.join(__file__),
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/myAction",
            "wsgi.errors": StringIO()
            }
        startResponseData = {
            "status": [],
            "responseHeaders": []
            }
        def startResponse(status, responseHeaders):
            startResponseData["status"].append(status)
            startResponseData["responseHeaders"].append(responseHeaders)

        # Successfully create and call the application
        responseParts = self.app(environ, startResponse)
        self.assertEqual(responseParts, [wsgistr_new("{}")])
        self.assertEqual(startResponseData["status"], ["200 OK"])
        self.assertEqual(self.resourceData["open"], ["Hello"])
        self.assertEqual(self.resourceData["close"], [1])
        self.assertTrue("Some info" not in environ["wsgi.errors"].getvalue())
        self.assertTrue("A warning..." in environ["wsgi.errors"].getvalue())

        # Call the application again (skips reloading)
        responseParts = self.app(environ, startResponse)
        self.assertEqual(responseParts, [wsgistr_new("{}")])
        self.assertEqual(startResponseData["status"], ["200 OK", "200 OK"])
        self.assertEqual(self.resourceData["open"], ["Hello", "Hello"])
        self.assertEqual(self.resourceData["close"], [1, 2])
        self.assertTrue("Some info" not in environ["wsgi.errors"].getvalue())
        self.assertTrue("A warning..." in environ["wsgi.errors"].getvalue())

    # Test callAction method
    def test_app_request(self):

        # POST
        logStream = StringIO()
        status, headers, response = self.app.request("POST", "/myAction2", wsgiInput = '{"value": 7}', environ = {"wsgi.errors": logStream})
        self.assertEqual(response, '{"result":63}')
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(logStream.getvalue(), "In myAction2\n")

        # GET
        status, headers, response = self.app.request("GET", "/myAction2", queryString = "value=8")
        self.assertEqual(response, '{"result":72}')
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # HTTP error
        status, headers, response = self.app.request("GET", "/unknownAction")
        self.assertEqual(response, "Not Found")
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(('Content-Type', 'text/plain') in headers)

        # Request with environ
        status, headers, response = self.app.request("POST", "/myAction2", wsgiInput = '{"value": 9}',
                                                     environ = { "MYENVIRON": "10" })
        self.assertEqual(response, '{"result":90}')
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex
        status, headers, response = self.app.request("GET", "/myAction3/123")
        self.assertEqual(response, '{"myArg":"123"}')
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex - POST
        status, headers, response = self.app.request("POST", "/myAction3/123", wsgiInput = '{}')
        self.assertEqual(response, '{"myArg":"123"}')
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)

        # Request action matched by regex - duplicate member error
        status, headers, response = self.app.request("GET", "/myAction3/123", queryString = "myArg=321")
        self.assertEqual(response, '{"error":"InvalidInput","message":"Duplicate member URL argument \'myArg\'"}')
        self.assertEqual(status, "500 Internal Server Error")
        self.assertTrue(('Content-Type', 'application/json') in headers)
