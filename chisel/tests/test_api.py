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

from chisel import action, ActionError, decodeQueryString, encodeQueryString, SpecParser, Struct
from chisel.api import Application
from chisel.compat import func_name, long_, PY3, StringIO, unichr_, unicode_, urllib

import json
import logging
import os
import re
import unittest
import wsgiref.util


# Server module loading tests
class TestApiLoadModules(unittest.TestCase):

    # Test succussful module directory load
    def test_api_loadModules(self):

        app = Application()
        app.loadSpecs(os.path.join(os.path.dirname(__file__), "test_api_files"))
        app.loadModules(os.path.join(os.path.dirname(__file__), "test_api_files"))
        self.assertEqual(len(app._actionCallbacks), 3)
        self.assertEqual(func_name(app._actionCallbacks["myAction1"].fn), "myAction1")
        self.assertEqual(app._actionCallbacks["myAction2"].name, "myAction2")
        self.assertEqual(func_name(app._actionCallbacks["myAction3"].fn), "myAction3")
        self.assertEqual(app._actionCallbacks["myAction1"].name, "myAction1")
        self.assertEqual(func_name(app._actionCallbacks["myAction2"].fn), "myAction2")
        self.assertEqual(app._actionCallbacks["myAction3"].name, "myAction3")

    # Verify that exception is raised when invalid module path is loaded
    def test_api_loadModules_badModulePath(self):

        app = Application()

        try:
            app.loadModules("_DIRECTORY_DOES_NOT_EXIST_")
        except Exception as e:
            self.assertEqual(str(e), "'_DIRECTORY_DOES_NOT_EXIST_' not found or is not a directory")
        else:
            self.fail()

        try:
            app.loadSpecs("_DIRECTORY_DOES_NOT_EXIST_")
        except Exception as e:
            self.assertEqual(str(e), "'_DIRECTORY_DOES_NOT_EXIST_' not found or is not a directory")
        else:
            self.fail()


# Server application object tests
class TestApiRequest(unittest.TestCase):

    # Request/response helper
    def sendRequest(self, app, method, pathInfo, contentLength, request = None, queryString = None, decodeJSON = True):

        # WSGI environment
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": pathInfo,
            "wsgi.input": StringIO("" if request is None else request)
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
        self.assertTrue(isinstance(responseList, (list, tuple)))
        self.assertFalse([responsePart for responsePart in responseList if not isinstance(responsePart, str)])
        response = "".join(responseList)
        if decodeJSON:
            response = Struct(json.loads(response))

        return status[0], responseHeaders[0], response

    # Test successful action handling
    def test_api_success(self):

        # Application instance
        app = Application()
        app.loadSpecString("""\
action myActionPost
    input
        int a
        int b
    output
        int c

action myActionGet
    output
        string d
""")
        def myActionPost(ctx, request):
            return { "c": request.a + request.b }
        def myActionGet(ctx, request):
            self.assertEqual(len(request()), 0)
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
        app.loadSpecString("""\
action myAction
    input
        int a
    output
        int b
        [optional] string c
    errors
        MyError

action myActionError
    input
        int a
    output
        int b
    errors
        MyError
""")

        def myAction(ctx, request):
            if request.a == 0:
                return { "error": "MyError", "message": "My message" }
            elif request.a == 1:
                return { "error": "MyError" }
            elif request.a == 2:
                return { "error": "BadError", "message": "My bad message" }
            elif request.a == 10:
                return { "b": 0, "c": chr(0xf1) } # c is invalid utf-8 string in Python 2.x
            else:
                return { "b": request.a * 2 }

        def myActionError(ctx, request):
            if request.a == 0:
                raise ActionError("MyError", "My message")
            elif request.a == 1:
                raise ActionError("MyError")
            elif request.a == 2:
                raise ActionError("BadError", "My bad message")
            else:
                return { "b": request.a * 2 }

        app.addActionCallback(myAction)
        app.addActionCallback(myActionError)

        # Requests
        requestErrorMessage = '{ "a": 0 }'
        requestError = '{ "a": 1 }'
        requestBadError = '{ "a": 2 }'
        requestInvalidUtf8 = '{ "a": 10 }'
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

        # Bad error enum value
        if not PY3:
            status, headers, response = self.sendRequest(app, "POST", "/myAction", len(requestInvalidUtf8), requestInvalidUtf8)
            self.assertEqual(status, "500 Internal Server Error")
            self.assertEqual(len(response()), 3)
            self.assertEqual(response.error, "InvalidOutput")
            self.assertEqual(response.message, "Invalid value '\\xf1' (type 'str') for member 'c', expected type 'string'")
            self.assertEqual(response.member, "c")

        # Non-error
        status, headers, response = self.sendRequest(app, "POST", "/myAction", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.b, 6)

        # Error with message (raise ActionError)
        status, headers, response = self.sendRequest(app, "POST", "/myActionError", len(requestErrorMessage), requestErrorMessage)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "MyError")
        self.assertEqual(response.message, "My message")

        # Error with NO message (raise ActionError)
        status, headers, response = self.sendRequest(app, "POST", "/myActionError", len(requestError), requestError)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.error, "MyError")

        # Bad error enum value (raise ActionError)
        status, headers, response = self.sendRequest(app, "POST", "/myActionError", len(requestBadError), requestBadError)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 3)
        self.assertEqual(response.error, "InvalidOutput")
        self.assertEqual(response.message, "Invalid value 'BadError' (type 'str') for member 'error', expected type 'myActionError_Error'")
        self.assertEqual(response.member, "error")

        # Non-error (raise ActionError)
        status, headers, response = self.sendRequest(app, "POST", "/myActionError", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.b, 6)

    # Test complex (nested) container response
    def test_api_complex_response(self):

        # Request handler
        app = Application()
        app.loadSpecString("""\
struct MyStruct
    int[] b

action myAction
    output
        MyStruct a
""")
        def myAction(ctx, request):
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
        app.loadSpecString("""\
action myActionRaise
    input
        int a
        int b
""")
        def myActionRaise(ctx, request):
            if request.a == 1 and request.b == 2:
                return {"c": "invalid"}
            elif request.a == 1 and request.b == 3:
                return None
            raise Exception("Barf")
        app.addActionCallback(myActionRaise)

        # Requests
        request = '{ "a": 5, "b": 7 }'
        requestResponse = '{ "a": 1, "b": 2 }'
        requestNoneResponse = '{ "a": 1, "b": 3 }'
        requestInvalid = '{ "a: 5, "b": 7 }'

        # Unknown action
        status, headers, response = self.sendRequest(app, "POST", "/myActionUnknown", len(request), request, decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

        # Unknown request method
        status, headers, response = self.sendRequest(app, "UNKNOWN", "/myActionRaise", len(request), request, decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

        # Invalid content length
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", None, request, decodeJSON = False)
        self.assertEqual(status, "411 Length Required")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Length Required")

        # Invalid content length (2)
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", "asdf", request, decodeJSON = False)
        self.assertEqual(status, "411 Length Required")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Length Required")

        # Invalid content length (3)
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", "", request, decodeJSON = False)
        self.assertEqual(status, "411 Length Required")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Length Required")

        # Invalid input
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", len(requestInvalid), requestInvalid)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidInput")
        self.assertTrue(isinstance(response.message, unicode_))
        self.assertTrue(response.message.startswith("Invalid request JSON:"))

        # Unexpected error
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", len(request), request)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "UnexpectedError")
        self.assertTrue(isinstance(response.message, unicode_))
        self.assertTrue(re.search("^test_api\\.py:\\d+: Barf$", response.message))

        # Invalid response
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", len(requestResponse), requestResponse)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidOutput")
        self.assertTrue(isinstance(response.message, unicode_))
        self.assertEqual(response.message, "Invalid member 'c'")

        # None (non-dict) response
        status, headers, response = self.sendRequest(app, "POST", "/myActionRaise", len(requestNoneResponse), requestNoneResponse)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidOutput")
        self.assertTrue(isinstance(response.message, unicode_))
        self.assertEqual(response.message, "Invalid value None (type 'NoneType'), expected type 'myActionRaise_Output'")

        # Invalid query string
        queryString = "a=7&b&c=9"
        status, headers, response = self.sendRequest(app, "GET", "/myActionRaise", None, "", queryString = queryString)
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidInput")
        self.assertTrue(isinstance(response.message, unicode_))
        self.assertEqual(response.message, "Invalid key/value pair 'b'")

    # Test passing complex struct as query string
    def test_api_query(self):

        # Request handler
        app = Application()
        app.loadSpecString("""\
action myAction
    input
        int[] nums
    output
        int sum
""")
        def myAction(ctx, request):
            numSum = 0
            for num in request.nums:
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
        app.loadSpecString("""\
action myAction
    input
        int[] nums
    output
        int sum
""")
        def myAction(ctx, request):
            numSum = 0
            for num in request.nums:
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

    def test_api_response_callback(self):

        # Action with custom response
        def myActionRespose(environ, start_response, ctx, request, response):
            if request.value == 2:
                raise Exception("Barf")
            content = "The integer %d times two is %d." % (request.value, response.valueTimesTwo)
            responseHeaders = [
                ("Content-Type", "text/plain"),
                ("Content-Length", str(len(content)))
                ]
            start_response("200 OK", responseHeaders)
            return [content]

        @action(responseCallback = myActionRespose)
        def myAction(ctx, request):
            if request.value == 1:
                return {} # invalid response
            else:
                return { "valueTimesTwo": request.value * 2 }

        # Test application
        app = Application()
        app.loadSpecString("""\
action myAction
    input
        int value
    output
        int valueTimesTwo
""")
        app.addActionCallback(myAction)

        # Successful request
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, queryString = "value=3", decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers, [("Content-Type", "text/plain"),
                                   ("Content-Length", '29')])
        self.assertEqual(response, "The integer 3 times two is 6.")

        # Invalid action response
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, queryString = "value=1")
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidOutput")
        self.assertEqual(response.message, "Required member 'valueTimesTwo' missing")

        # Exception raised in response callback
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, queryString = "value=2")
        self.assertEqual(status, "500 Internal Server Error")
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "UnexpectedError")
        self.assertTrue(re.search("^test_api\\.py:\\d+: Barf$", response.message))

        # Headers callback
        app._headersCallback = lambda ctx: [("X-Bar", "Foo")]
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, queryString = "value=3", decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers, [("Content-Type", "text/plain"),
                                   ("Content-Length", '29'),
                                   ("X-Bar", "Foo")])
        self.assertEqual(response, "The integer 3 times two is 6.")

    def test_api_non_default_path(self):

        # Action with non-default path
        @action(path = [("GET", "/foo/myAction"),
                        ("POST", "/bar/thud")])
        def myAction(ctx, request):
            return { "valueTimesTwo": request.value * 2 }

        # Test application
        app = Application()
        app.loadSpecString("""\
action myAction
    input
        int value
    output
        int valueTimesTwo
""")
        app.addActionCallback(myAction)

        # Successful request
        status, headers, response = self.sendRequest(app, "GET", "/foo/myAction", None, queryString = "value=3")
        self.assertEqual(status, "200 OK")
        self.assertEqual(response, {"valueTimesTwo": 6})

        # Successful request 2
        request = '{"value": 3}'
        status, headers, response = self.sendRequest(app, "POST", "/bar/thud", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertEqual(response, {"valueTimesTwo": 6})

        # Failed request - method not in path
        request = '{"value": 3}'
        status, headers, response = self.sendRequest(app, "POST", "/foo/myAction", len(request), request, decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertEqual(response, "Not Found")

        # Failed request - method not in path 2
        status, headers, response = self.sendRequest(app, "GET", "/bar/thud", None, queryString = "value=3", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertEqual(response, "Not Found")

        # Failed request - default path
        status, headers, response = self.sendRequest(app, "GET", "/myAction", None, queryString = "value=3", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertEqual(response, "Not Found")

    def test_api_fail_init(self):

        # Verify that exception is raised when action is added with no model
        app = Application()
        def myAction(ctx, request):
            return {}
        try:
            app.addActionCallback(myAction)
        except Exception as e:
            self.assertEqual(str(e), "No model defined for action callback 'myAction'")
        else:
            self.fail()

        # Verify that exception is raised when action callback is redefined
        app = Application()
        app.loadSpecString("""\
action myAction
""")
        def myAction(ctx, request):
            return {}
        app.addActionCallback(myAction)
        try:
            app.addActionCallback(myAction)
        except Exception as e:
            self.assertEqual(str(e), "Redefinition of action callback 'myAction'")
        else:
            self.fail()

        # Verify that exception is raised when action model is redefined
        app = Application()
        app.loadSpecString("""\
action myAction
""")
        try:
            app.loadSpecString("""\
action myAction
""")
        except Exception as e:
            self.assertEqual(str(e), ":1: error: Redefinition of action 'myAction'")
        else:
            self.fail()

        # Verify that exception is raised when action spec has errors
        app = Application()
        try:
            app.loadSpecString("""\
action myAction
    int a
    string b
""")
        except Exception as e:
            self.assertEqual(str(e), ":2: error: Member definition outside of struct scope\n:3: error: Member definition outside of struct scope")
        else:
            self.fail()

    # Test context callback and header callback functionality
    def test_api_context(self):

        # Action context callback
        def myContext(environ):
            ctx = Struct()
            ctx.foo = 19
            return ctx

        # Action header callback
        def myHeaders(ctx):
            return [("X-Bar", "Foo bar %d" % (ctx.foo,))]

        # Request handler
        app = Application(contextCallback = myContext, headersCallback = myHeaders)
        app.loadSpecString("""\
action myAction1
    input
        int a
    output
        int b
""")
        def myAction1(ctx, request):
            return { "b": request.a * ctx.foo }
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
        app.loadSpecString("""\
action myAction
    input
        int a
    output
        int b
""")
        def myAction(ctx, request):
            return { "b": request.a * ctx.foo }
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

        # Test doc action request (trailing slash)
        status, headers, response = self.sendRequest(app, "POST", "/doc/myAction/", None, "", decodeJSON = False)
        self.assertEqual(status, "405 Method Not Allowed")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Method Not Allowed")

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

        # App with docs disabled
        app = Application(docUriDir = None)
        app.loadSpecString("""\
action myAction
    input
        int a
    output
        int b
""")
        def myAction(ctx, request):
            return { "b": request.a * ctx.foo }
        app.addActionCallback(myAction)

        # Test doc index request with docs disabled
        status, headers, response = self.sendRequest(app, "GET", "/doc", None, "", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

        # Test doc action request  with docs disabled
        status, headers, response = self.sendRequest(app, "POST", "/doc/myAction", None, "", decodeJSON = False)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Not Found")

    # Test wrapped application
    def test_api_wrapped(self):

        # Wrapped WSGI application
        def myApp(environ, start_response):
            content = "Hello!"
            responseHeaders = [
                ("Content-Type", "text/plain"),
                ("Content-Length", str(len(content)))
                ]
            start_response("200 OK", responseHeaders)
            return [content]

        # Request handler
        app = Application(wrapApplication = myApp)
        app.loadSpecString("""\
action myAction
    input
        int a
    output
        int b
""")
        def myAction(ctx, request):
            return { "b": request.a * 2 }
        app.addActionCallback(myAction)

        # Requests
        request = '{ "a": 5 }'

        # API request
        status, headers, response = self.sendRequest(app, "POST", "/myAction", len(request), request)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "application/json") in headers)
        self.assertEqual(response, { "b": 10 })

        # Non-API request
        status, headers, response = self.sendRequest(app, "GET", "/wrapped", None, None, decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Hello!")

        # Non-doc request
        status, headers, response = self.sendRequest(app, "GET", "/doc/wrapped", None, None, decodeJSON = False)
        self.assertEqual(status, "200 OK")
        self.assertTrue(("Content-Type", "text/plain") in headers)
        self.assertEqual(response, "Hello!")
