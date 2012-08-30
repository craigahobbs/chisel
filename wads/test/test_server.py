#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from wads import encodeQueryString, Application, SpecParser, Struct

import json
import logging
import os
import re
from StringIO import StringIO
import unittest


# Test logging handler
class TestLoggerHandler:

    records = []

    def __init__(self, app):

        self.level = logging.NOTSET
        del TestLoggerHandler.records[:]

        # Add this as the only logger handler
        logger = app.getLogger()
        del logger.handlers[:]
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self)

    def handle(self, record):
        TestLoggerHandler.records.append(record)

    @staticmethod
    def assertRegex(u, msg, levelno):
        u.assertEqual(1, len([x for x in TestLoggerHandler.records if
                              x.levelno == levelno and re.search(msg, x.msg)]))


# Server module loading tests
class TestLoadModules(unittest.TestCase):

    def setUp(self):

        self.app = Application()
        TestLoggerHandler(self.app)

    def test_loadModules(self):

        app = self.app
        app.loadModules(os.path.join(os.path.dirname(__file__), "test_server_modules"))
        self.assertEqual(len(TestLoggerHandler.records), 0)
        self.assertEqual(len(app._actionCallbacks), 3)
        self.assertEqual(app._actionCallbacks["myAction1"].callback.func_name, "myAction1")
        self.assertEqual(app._actionCallbacks["myAction2"].callback.func_name, "myAction2")
        self.assertEqual(app._actionCallbacks["myAction3"].callback.func_name, "myAction3")

    def test_loadModules_badModulePath(self):

        app = self.app
        with self.assertRaises(Exception):
            app.loadModules("_DIRECTORY_DOES_NOT_EXIST_")
        self.assertEqual(len(TestLoggerHandler.records), 1)
        TestLoggerHandler.assertRegex(self, "No such file or directory: '_DIRECTORY_DOES_NOT_EXIST_'", logging.ERROR)


# Server application object tests
class TestRequest(unittest.TestCase):

    def setUp(self):

        self.app = Application()
        TestLoggerHandler(self.app)

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

        # WSGI start_response
        status = None
        responseHeaders = None
        def start_response(_status, _responseHeaders):
            status = _status
            responseHeaders = _responseHeaders

        # Make the WSGI call
        response = "".join(app(environ, start_response))
        if decodeJSON:
            return Struct(json.loads("".join(response)))
        return response

    def test_success(self):

        # Application instance
        app = self.app
        def myActionPost(ctx, input):
            return { "c": input.a + input.b }
        def myActionGet(ctx, input):
            self.assertEqual(len(input()), 0)
            return { "d": "OK" }
        app.addActionCallback(myActionPost)
        app.addActionCallback(myActionGet)
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

        # Requests
        request = '{ "a": 5, "b": 7 }'

        # GET
        response = self.sendRequest(app, "GET", "/myActionGet", None, "")
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.d, "OK")

        # POST
        response = self.sendRequest(app, "POST", "/myActionPost", len(request), request)
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.c, 12)

        # Non-root POST
        response = self.sendRequest(app, "POST", "/api/myActionPost", len(request), request)
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.c, 12)

    def test_complex_response(self):

        # Request handler
        app = self.app
        def myAction(ctx, input):
            return { "a": { "b": [1, 2, 3] } }
        app.addActionCallback(myAction)
        app.loadSpecs(StringIO("""\
struct MyStruct
    int[] b

action myAction
    output
        MyStruct a
"""))

        # Get the complex response
        response = self.sendRequest(app, "GET", "/myAction", None, "")
        self.assertEqual(len(response()), 1)
        self.assertTrue(isinstance(response.a, Struct))
        self.assertTrue(isinstance(response.a.b, list))
        self.assertTrue(isinstance(response.a.b[0], int))
        self.assertEqual(response.a.b[0], 1)
        self.assertEqual(response.a.b[1], 2)
        self.assertEqual(response.a.b[2], 3)

    def test_fail(self):

        # Request handler
        app = Application()
        def myActionRaise(ctx, input):
            raise Exception("Barf")
        app.addActionCallback(myActionRaise)
        app.loadSpecs(StringIO("""\
action myActionRaise
    input
        int a
        int b
"""))

        # Requests
        request = '{ "a": 5, "b": 7 }'
        requestInvalid = '{ "a: 5, "b": 7 }'

        # Unknown action
        response = self.sendRequest(app, "POST", "/myActionUnknown", len(request), request)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "UnknownAction")
        self.assertTrue(isinstance(response.message, unicode))

        # Unknown request method
        response = self.sendRequest(app, "UNKNOWN", "/myActionRaise", len(request), request)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "UnknownRequestMethod")
        self.assertTrue(isinstance(response.message, unicode))

        # Invalid content length
        response = self.sendRequest(app, "POST", "/myActionRaise", None, request)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidContentLength")
        self.assertTrue(isinstance(response.message, unicode))

        # Invalid content length (2)
        response = self.sendRequest(app, "POST", "/myActionRaise", "asdf", request)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidContentLength")
        self.assertTrue(isinstance(response.message, unicode))

        # Invalid content length (3)
        response = self.sendRequest(app, "POST", "/myActionRaise", "", request)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidContentLength")
        self.assertTrue(isinstance(response.message, unicode))

        # Invalid input
        response = self.sendRequest(app, "POST", "/myActionRaise", len(requestInvalid), requestInvalid)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "InvalidInput")
        self.assertTrue(isinstance(response.message, unicode))

        # Unexpected error
        response = self.sendRequest(app, "POST", "/myActionRaise", len(request), request)
        self.assertEqual(len(response()), 2)
        self.assertEqual(response.error, "UnexpectedError")
        self.assertTrue(isinstance(response.message, unicode))

    def test_query(self):

        # Request handler
        app = Application()
        def myAction(ctx, input):
            numSum = 0
            for num in input.nums:
                numSum += int(num)
            return { "sum": numSum }
        app.addActionCallback(myAction)
        app.loadSpecs(StringIO("""\
action myAction
    input
        int[] nums
    output
        int sum
"""))

        # Execute the request
        request = { "nums": [ 1, 2, 3, 4, 5 ] }
        queryString = encodeQueryString(request)
        response = self.sendRequest(app, "GET", "/myAction", None, "", queryString = queryString)
        self.assertEqual(len(response()), 1)
        self.assertEqual(response.sum, 15)

    def test_jsonp(self):

        # Request handler
        app = Application()
        def myAction(ctx, input):
            numSum = 0
            for num in input.nums:
                numSum += int(num)
            return { "sum": numSum }
        app.addActionCallback(myAction)
        app.loadSpecs(StringIO("""\
action myAction
    input
        int[] nums
    output
        int sum
"""))

        # Execute the request
        request = { "jsonp": "myfunc", "nums": [ 1, 2, 3, 4, 5 ] }
        queryString = encodeQueryString(request)
        response = self.sendRequest(app, "GET", "/myAction", None, "", queryString = queryString, decodeJSON = False)
        self.assertEqual(response, 'myfunc({"sum":15});')
