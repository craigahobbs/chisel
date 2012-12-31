#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel.resource.url_request_mock import UrlRequestResourceTypeMock

import unittest


# Test UrlRequestResourceMock functionality
class TestLoadModules(unittest.TestCase):

    # Test UrlRequestResourceMock setup and send
    def test_send(self):

        # Create the resource type
        urlRequestType = UrlRequestResourceTypeMock()
        self.assertEqual(urlRequestType.name, "url_request")

        # Setup the mock responses
        urlRequestType.addResponse("/myurl", "response1")
        urlRequestType.addResponse("/myurl", "response2")
        urlRequestType.addResponse("/myotherurl", "response3")

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

        # No mock response available
        try:
            request.send("/myotherurl")
        except Exception as e:
            self.assertEqual(str(e), "No mock response found for '/myotherurl'")
        else:
            self.fail()

        # Check recorded requests
        self.assertEqual(urlRequestType.requests, [
                ("/myurl",
                 [],
                 [],
                 [],
                 "response1"),
                ("/myurl",
                 [],
                 [],
                 ["My POST data."],
                 "response2"),
                ("/myotherurl",
                 [("MyHeader", "MyValue")],
                 [("MyUnredirectedHeader", "MyUnredirectedValue")],
                 ["My other POST data."],
                 "response3")
                ])
