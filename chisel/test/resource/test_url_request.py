#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Replace Python's urllib2 with mock
import sys
import urllib2
sys.modules["urllib2"] = urllib2

from chisel.resource.url_request import UrlRequestResourceType

# Restore Python's urllib2
del sys.modules["urllib2"]

import unittest


# Test UrlRequestResource functionality
class TestResourceUrlRequest(unittest.TestCase):

    # Test UrlRequestResource setup and send
    def test_resource_url_request(self):

        # Create the resource type
        urlRequestType = UrlRequestResourceType()
        self.assertEqual(urlRequestType.name, "url_request")

        request = urlRequestType.open("http://myhost.com/mypath/")

        # GET (trailing slash, append to URL)
        response = request.send("myurl")
        self.assertEqual(response, """\
http://myhost.com/mypath/myurl""")

        # GET (trailing slash, replace URL)
        response = request.send("/myurl")
        self.assertEqual(response, """\
http://myhost.com/myurl""")

        # GET (trailing slash, no URL)
        response = request.send()
        self.assertEqual(response, """\
http://myhost.com/mypath/""")

        request = urlRequestType.open("http://myhost.com/mypath/myresource")

        # GET (no trailing slash, replace resource)
        response = request.send("myurl")
        self.assertEqual(response, """\
http://myhost.com/mypath/myurl""")

        # GET (no trailing slash, replace URL)
        response = request.send("/myurl")
        self.assertEqual(response, """\
http://myhost.com/myurl""")

        # GET (no trailing slash, empty URL)
        response = request.send()
        self.assertEqual(response, """\
http://myhost.com/mypath/myresource""")

        request = urlRequestType.open("http://myhost.com/mypath/")

        # POST
        request.add_data("My POST data.")
        response = request.send()
        self.assertEqual(response, """\
http://myhost.com/mypath/
My POST data.""")

        # POST with headers
        request.add_data("My other POST data.")
        request.add_header("MyHeader", "MyValue")
        request.add_unredirected_header("MyUnredirectedHeader", "MyUnredirectedValue")
        response = request.send()
        self.assertEqual(response, """\
http://myhost.com/mypath/
('MyHeader', 'MyValue')
('MyUnredirectedHeader', 'MyUnredirectedValue')
My other POST data.""")
