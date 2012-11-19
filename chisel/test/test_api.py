#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import encodeQueryString, SpecParser, Struct
from chisel.api import Application

import json
import logging
import os
import re
from StringIO import StringIO
import unittest
import wsgiref.util


# Server module loading tests
class TestLoadModules(unittest.TestCase):

    # Test succussful module directory load
    def test_api_loadModules(self):

        app = Application()
        app.loadSpecs(os.path.join(os.path.dirname(__file__), "test_api_files"))
        app.loadModules(os.path.join(os.path.dirname(__file__), "test_api_files"))
        self.assertEqual(len(app._actionCallbacks), 3)
        self.assertEqual(app._actionCallbacks["myAction1"].func_name, "myAction1")
        self.assertEqual(app._actionCallbacks["myAction2"].func_name, "myAction2")
        self.assertEqual(app._actionCallbacks["myAction3"].func_name, "myAction3")

    # Verify that exception is raised when invalid module path is loaded
    def test_api_loadModules_badModulePath(self):

        app = Application
        with self.assertRaises(Exception):
            app.loadModules("_DIRECTORY_DOES_NOT_EXIST_")


# Server application object tests
class TestRequest(unittest.TestCase):

    # Request/response helper
    @staticmethod
    def sendRequest(app, method, pathInfo, contentLength, request, queryString = None, decodeJSON = True):

        # WSGI environment
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": pathInfo,
            "wsgi.input": StringIO(request)
            }
        if queryString is not None:
            environ["QUERY_STRING"] = queryString
        if contentLength is not None:
            environ["CONTENT_LENGTH"] = str(contentLength)
        wsgiref.util.setup_testing_defaults(environ)

        # WSGI start_response
        status = []
        responseHeaders = []
        def start_response(_status, _responseHeaders):
            status.append(_status)
            responseHeaders.append(_responseHeaders)

        # Make the WSGI call
        responseList = app(environ, start_response)
        assert isinstance(responseList, (list, tuple))
        response = "".join(responseList)
        if decodeJSON:
            response = Struct(json.loads(response))
        return status[0], responseHeaders[0], response

    # Test successful action handling
    def test_api_success(self):

        # Application instance
        app = Application()
        app.loadSpecs(StringIO("""\
action myActionPost
    input
        int a
        int b
    output
        int c

action myActionGet
    output
        string d
"""))
        def myActionPost(ctx, input):
            return { "c": input.a + input.b }
        def myActionGet(ctx, input):
            self.assertEqual(len(input()), 0)
            return { "d": "OK" }
        app.addActionCallback(myActionPost)
        app.addActionCallback(myActionGet)

        # Requests
        request = '{ "a": 5, "b": 7 }'

        # GET
        status, headers, response = self.sendRequest(app, "GET", "/myActionGet", None, "")
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.d, "OK")

        # POST
        status, headers, response = self.sendRequest(app, "POST", "/myActionPost", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.c, 12)

        # Non-root POST
        status, headers, response = self.sendRequest(app, "POST", "/api/myActionPost", len(request), request, decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

    # Test action-level error handling
    def test_api_error(self):

        # Application instance
        app = Application()
        app.loadSpecs(StringIO("""\
action myAction
    input
        int a
    output
        int b
    errors
        MyError
"""))
        def myAction(ctx, input):
            output = Struct()
            if input.a == 0:
                output.error = "MyError"
                output.message = "My message"
            elif input.a == 1:
                output.error = "MyError"
            elif input.a == 2:
                output.error = "BadError"
                output.message = "My bad message"
            else:
                output.b = input.a * 2
            return output
        app.addActionCallback(myAction)

        # Requests
        requestErrorMessage = '{ "a": 0 }'
        requestError = '{ "a": 1 }'
        requestBadError = '{ "a": 2 }'
        request = '{ "a": 3 }'

        # Error with message
        status, headers, response = self.sendRequest(app, "POST", "/myAction", len(requestErrorMessage), requestErrorMessage)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "MyError")
        self.assertEqual(response.message, "My message")

        # Error with NO message
        status, headers, response = self.sendRequest(app, "POST", "/myAction", len(requestError), requestError)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.error, "MyError")

        # Bad error enum value
        status, headers, response = self.sendRequest(app, "POST", "/myAction", len(requestBadError), requestBadError)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 3)
        self.assertEqual(response.error, "InvalidOutput")
        self.assertEqual(response.message, "Invalid value 'BadError' (type 'str') for member 'error', expected type 'myAction_Error'")
        self.assertEqual(response.member, "error")

        # Non-error
        status, headers, response = self.sendRequest(app, "POST", "/myAction", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.b, 6)

    # Test complex (nested) container response
    def test_api_complex_response(self):

        # Request handler
        app = Application()
        app.loadSpecs(StringIO("""\
struct MyStruct
    int[] b

action myAction
    output
        MyStruct a
"""))
        def myAction(ctx, input):
            return { "a": { "b": [1, 2, 3] } }
        app.addActionCallback(myAction)

        # Get the complex response
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, "")
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertTrue(isinstance(response.a, Struct))
        self.assertTrue(isinstance(response.a.b, Struct))
        self.assertTrue(isinstance(response.a.b(), list))
        self.assertTrue(isinstance(response.a.b[0], int))
        self.assertEqual(response.a.b[0], 1)
        self.assertEqual(response.a.b[1], 2)
        self.assertEqual(response.a.b[2], 3)

    # Test server-level error handling
    def test_api_fail(self):

        # Request handler
        app = Application()
        app.loadSpecs(StringIO("""\
action myActionRaise
    input
        int a
        int b
"""))
        def myActionRaise(ctx, input):
            raise Exception("Barf")
        app.addActionCallback(myActionRaise)

        # Requests
        request = '{ "a": 5, "b": 7 }'
        requestInvalid = '{ "a: 5, "b": 7 }'

        # Unknown action
        status, headers, response = self.sendRequest(app, "POST", "/myActionUnknown", len(request), request, decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

        # Unknown request method
        status, headers, response = self.sendRequest(app, "UNKNOWN", "/myActionRaise", len(request), request, decodeJSON = False)
        self.assertEqual(status, "405 Method Not Allowed")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Method Not Allowed")

        # Invalid content length
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", None, request)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidContentLength")
        self.assertTrue(isinstance(response.message, unicode))
        self.assertEqual(response.message, "Invalid content length 'None'")

        # Invalid content length (2)
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", "asdf", request)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidContentLength")
        self.assertTrue(isinstance(response.message, unicode))
        self.assertEqual(response.message, "Invalid content length 'asdf'")

        # Invalid content length (3)
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", "", request)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidContentLength")
        self.assertTrue(isinstance(response.message, unicode))
        self.assertEqual(response.message, "Invalid content length ''")

        # Invalid input
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", len(requestInvalid), requestInvalid)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidInput")
        self.assertTrue(isinstance(response.message, unicode))
        self.assertTrue(response.message.startswith("Invalid request JSON:"))

        # Unexpected error
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", len(request), request)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "UnexpectedError")
        self.assertTrue(isinstance(response.message, unicode))
        self.assertEqual(response.message, "Barf")

        # Invalid query string
        queryString = "a=7&b&c=9"
        status, headers, response = self.sendRequest(app, "GET", "/myActionRaise", None, "", queryString = queryString)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidInput")
        self.assertTrue(isinstance(response.message, unicode))
        self.assertEqual(response.message, "Invalid key/value pair 'b'")

    # Test passing complex struct as query string
    def test_api_query(self):

        # Request handler
        app = Application()
        app.loadSpecs(StringIO("""\
action myAction
    input
        int[] nums
    output
        int sum
"""))
        def myAction(ctx, input):
            numSum = 0
            for num in input.nums:
                numSum += int(num)
            return { "sum": numSum }
        app.addActionCallback(myAction)

        # Execute the request
        request = { "nums": [ 1, 2, 3, 4, 5 ] }
        queryString = encodeQueryString(request)
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, "", queryString = queryString)
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.sum, 15)

    # Test JSONP response
    def test_api_jsonp(self):

        # Request handler
        app = Application()
        app.loadSpecs(StringIO("""\
action myAction
    input
        int[] nums
    output
        int sum
"""))
        def myAction(ctx, input):
            numSum = 0
            for num in input.nums:
                numSum += int(num)
            return { "sum": numSum }
        app.addActionCallback(myAction)

        # Execute the request
        request = { "jsonp": "myfunc", "nums": [ 1, 2, 3, 4, 5 ] }
        queryString = encodeQueryString(request)
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, "", queryString = queryString, decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertEqual(response, 'myfunc({"sum":15});')

        # JSONP error request
        request = { "jsonp": "myfunc", "nums": "bad" }
        queryString = encodeQueryString(request)
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, "", queryString = queryString, decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue('"error":"InvalidInput"' in response)
        self.assertTrue('"member":"nums"' in response)

    def test_api_fail_init(self):

        # Verify that exception is raised when action is added with no model
        app = Application()
        def myAction(ctx, input):
            return {}
        try:
            app.addActionCallback(myAction)
            self.fail()
        except Exception, e:
            self.assertEqual(str(e), "No model defined for action callback 'myAction'")

        # Verify that exception is raised when action callback is redefined
        app = Application()
        app.loadSpecs(StringIO("""\
action myAction
"""))
        def myAction(ctx, input):
            return {}
        app.addActionCallback(myAction)
        try:
            app.addActionCallback(myAction)
            self.fail()
        except Exception, e:
            self.assertEqual(str(e), "Redefinition of action callback 'myAction'")

        # Verify that exception is raised when action model is redefined
        app = Application()
        app.loadSpecs(StringIO("""\
action myAction
"""))
        try:
            app.loadSpecs(StringIO("""\
action myAction
"""))
            self.fail()
        except Exception, e:
            self.assertEqual(str(e), "Redefinition of action model 'myAction'")

        # Verify that exception is raised when action spec has errors
        app = Application()
        try:
            app.loadSpecs(StringIO("""\
action myAction
    int a
    string b
"""))
            self.fail()
        except Exception, e:
            self.assertEqual(str(e), ":2: error: Member definition outside of struct scope\n:3: error: Member definition outside of struct scope")

    # Test context callback and header callback functionality
    def test_api_context(self):

        # Action context callback
        def myContext(environ):
            ctx = Struct()
            ctx.foo = 19
            return ctx

        # Action header callback
        def myHeaders(ctx):
            return [("X-Bar", "Foo bar %d" % (ctx.foo))]

        # Request handler
        app = Application(contextCallback = myContext, headersCallback = myHeaders)
        app.loadSpecs(StringIO("""\
action myAction1
    input
        int a
    output
        int b
"""))
        def myAction1(ctx, input):
            return { "b": input.a * ctx.foo }
        app.addActionCallback(myAction1)

        # Check context creation
        request = '{ "a": 3 }'
        status, headers, response = self.sendRequest(app, "POST", "/myAction1", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.b, 3 * 19)
        self.assertTrue(("X-Bar", "Foo bar 19") in headers)

    # Test doc URL handling
    def test_api_doc(self):

        # Request handler
        app = Application()
        app.loadSpecs(StringIO("""\
action myAction
    input
        int a
    output
        int b
"""))
        def myAction(ctx, input):
            return { "b": input.a * ctx.foo }
        app.addActionCallback(myAction)

        # Test doc index request
        status, headers, response = self.sendRequest(app, "GET", "/doc", None, "", decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "text/html") in headers)
        self.assertTrue("<!doctype html>" in response)
        self.assertTrue(">myAction</a>" in response)

        # Test doc index request (trailing slash)
        status, headers, response = self.sendRequest(app, "GET", "/doc/", None, "", decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "text/html") in headers)
        self.assertTrue("<!doctype html>" in response)
        self.assertTrue(">myAction</a>" in response)

        # Test doc index request POST
        status, headers, response = self.sendRequest(app, "POST", "/doc", "2", "{}", decodeJSON = False)
        self.assertEqual(status, "405 Method Not Allowed")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Method Not Allowed")

        # Test doc action request
        status, headers, response = self.sendRequest(app, "GET", "/doc/myAction", None, "", decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "text/html") in headers)
        self.assertTrue("<!doctype html>" in response)
        self.assertTrue(">myAction</h1>" in response)

        # Test doc action request (trailing slash)
        status, headers, response = self.sendRequest(app, "GET", "/doc/myAction/", None, "", decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "text/html") in headers)
        self.assertTrue("<!doctype html>" in response)
        self.assertTrue(">myAction</h1>" in response)

        # Test unknown doc action request handling
        status, headers, response = self.sendRequest(app, "GET", "/doc/UnknownAction", None, "", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

        # Test unknown doc action request handling (trailing slash)
        status, headers, response = self.sendRequest(app, "GET", "/doc/UnknownAction/", None, "", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

        # Test non-root doc index request
        status, headers, response = self.sendRequest(app, "GET", "/api/doc/myAction", None, "", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")
