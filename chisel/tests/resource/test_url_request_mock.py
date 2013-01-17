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

from chisel.resource.url_request_mock import UrlRequestResourceTypeMock, SimpleSendCallback

import unittest


# Test UrlRequestResourceMock functionality
class TestResourceUrlRequestMock(unittest.TestCase):

    # Test UrlRequestResourceMock setup and send
    def test_resource_url_request_mock(self):

        # Create the resource type
        urlRequests = SimpleSendCallback()
        urlRequestType = UrlRequestResourceTypeMock(urlRequests)
        self.assertEqual(urlRequestType.name, "url_request")

        request = urlRequestType.open("http://myhost.com/mypath/")

        # GET (trailing slash, append to URL)
        urlRequests.addResponse("http://myhost.com/mypath/myurl", "response1")
        response = request.send("myurl")
        self.assertEqual(response, "response1")

        # GET (trailing slash, replace URL)
        urlRequests.addResponse("http://myhost.com/myurl", "response2")
        response = request.send("/myurl")
        self.assertEqual(response, "response2")

        # GET (trailing slash, no URL)
        urlRequests.addResponse("http://myhost.com/mypath/", "response3")
        response = request.send()
        self.assertEqual(response, "response3")

        # GET (trailing slash, params only)
        urlRequests.addResponse("http://myhost.com/mypath/?a=1&b=2", "response3.5")
        response = request.send("?a=1&b=2")
        self.assertEqual(response, "response3.5")

        # Close the request (does nothing)
        urlRequestType.close(request)

        request = urlRequestType.open("http://myhost.com/mypath/myresource")

        # GET (no trailing slash, replace resource)
        urlRequests.addResponse("http://myhost.com/mypath/myurl", "response4")
        response = request.send("myurl")
        self.assertEqual(response, "response4")

        # GET (no trailing slash, replace URL)
        urlRequests.addResponse("http://myhost.com/myurl", "response5")
        response = request.send("/myurl")
        self.assertEqual(response, "response5")

        # GET (no trailing slash, empty URL)
        urlRequests.addResponse("http://myhost.com/mypath/myresource", "response6")
        response = request.send()
        self.assertEqual(response, "response6")

        # GET (no trailing slash, empty URL)
        urlRequests.addResponse("http://myhost.com/mypath/myresource?a=1&b=2", "response6.5")
        response = request.send("?a=1&b=2")
        self.assertEqual(response, "response6.5")

        # Close the request (does nothing)
        urlRequestType.close(request)

        request = urlRequestType.open("http://myhost.com/mypath/")

        # POST with headers
        urlRequests.addResponse("http://myhost.com/mypath/", "response7")
        request.add_data("My other POST data.")
        request.add_header("MyHeader", "MyValue")
        request.add_unredirected_header("MyUnredirectedHeader", "MyUnredirectedValue")
        response = request.send()
        self.assertEqual(response, "response7")

        # Failure response
        try:
            request.send()
        except request.URLError as e:
            self.assertEqual(str(e), "<urlopen error HTTP Error 500: Internal Server Error>")
        else:
            self.fail()

        # No mock response available
        try:
            request.send("/myotherurl")
        except request.URLError as e:
            self.assertEqual(str(e), "<urlopen error HTTP Error 500: Internal Server Error>")
        else:
            self.fail()

        # Check recorded requests
        self.assertEqual(len(urlRequests), 6)
        self.assertEqual(len(urlRequests["http://myhost.com/mypath/myurl"]), 2)
        self.assertEqual(len(urlRequests["http://myhost.com/myurl"]), 2)
        self.assertEqual(len(urlRequests["http://myhost.com/mypath/"]), 2)
        self.assertEqual(len(urlRequests["http://myhost.com/mypath/?a=1&b=2"]), 1)
        self.assertEqual(len(urlRequests["http://myhost.com/mypath/myresource"]), 1)
        self.assertEqual(len(urlRequests["http://myhost.com/mypath/myresource?a=1&b=2"]), 1)

        # Close the request (does nothing)
        urlRequestType.close(request)

        request = urlRequests["http://myhost.com/mypath/myurl"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response1")

        request = urlRequests["http://myhost.com/mypath/myurl"][1]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response4")

        request = urlRequests["http://myhost.com/myurl"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response2")

        request = urlRequests["http://myhost.com/myurl"][1]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response5")

        request = urlRequests["http://myhost.com/mypath/"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response3")

        request = urlRequests["http://myhost.com/mypath/"][1]
        self.assertEqual(request.headers, [('MyHeader', 'MyValue')])
        self.assertEqual(request.unredirected_headers, [('MyUnredirectedHeader', 'MyUnredirectedValue')])
        self.assertEqual(request.requestData, ['My other POST data.'])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response7")

        request = urlRequests["http://myhost.com/mypath/?a=1&b=2"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response3.5")

        request = urlRequests["http://myhost.com/mypath/myresource"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response6")

        request = urlRequests["http://myhost.com/mypath/myresource?a=1&b=2"][0]
        self.assertEqual(request.headers, [])
        self.assertEqual(request.unredirected_headers, [])
        self.assertEqual(request.requestData, [])
        self.assertTrue(request.isSuccess)
        self.assertEqual(request.responseData, "response6.5")
