#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel.resource.url_request_mock import UrlRequestResourceTypeMock, RecordingSendCallback

import unittest


# Test UrlRequestResourceMock functionality
class TestResourceUrlRequestMock(unittest.TestCase):

    # Test UrlRequestResourceMock setup and send
    def test_resource_url_request_mock(self):

        # Create the resource type
        urlRequests = RecordingSendCallback()
        urlRequestType = UrlRequestResourceTypeMock(urlRequests)
        self.assertEqual(urlRequestType.name, "url_request")

        # Setup the mock responses
        urlRequests.addResponse("/myurl", "response1")
        urlRequests.addResponse("/myurl", "response2")
        urlRequests.addResponse("/myotherurl", "response3")
        urlRequests.addResponse("/myotherurl", "response4", isSuccess = False)

        # GET
        request = urlRequestType.open("http://myhost.com")
        response = request.send("/myurl")
        self.assertEqual(response, "response1")

        # POST
        request.add_data("My POST data.")
        response = request.send("/myurl")
        self.assertEqual(response, "response2")

        # POST with headers
        request.add_data("My other POST data.")
        request.add_header("MyHeader", "MyValue")
        request.add_unredirected_header("MyUnredirectedHeader", "MyUnredirectedValue")
        response = request.send("/myotherurl")
        self.assertEqual(response, "response3")

        # Failure response
        try:
            request.send("/myotherurl")
        except Exception as e:
            self.assertEqual(str(e), "HTTP Error 500: Internal Server Error")
        else:
            self.fail()

        # No mock response available
        try:
            request.send("/myotherurl")
        except Exception as e:
            self.assertEqual(str(e), "HTTP Error 500: Internal Server Error")
        else:
            self.fail()

        # Check recorded requests
        self.assertEqual(len(urlRequests), 2)
        self.assertEqual(len(urlRequests["/myurl"]), 2)
        self.assertEqual(len(urlRequests["/myotherurl"]), 2)

        request = urlRequests["/myurl"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response1")

        request = urlRequests["/myurl"][1]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, ["My POST data."])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response2")

        request = urlRequests["/myotherurl"][0]
        self.assertEqual(request.headers, [("MyHeader", "MyValue")])
        self.assertEqual(request.unredirected_headers, [("MyUnredirectedHeader", "MyUnredirectedValue")])
        self.assertEqual(request.requestData, ["My other POST data."])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response3")

        request = urlRequests["/myotherurl"][1]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertFalse(request.isSuccess)
        self.assertEqual(request.responseData, "response4")
