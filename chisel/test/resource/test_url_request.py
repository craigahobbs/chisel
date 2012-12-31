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
class TestLoadModules(unittest.TestCase):

    # Test UrlRequestResource setup and send
    def test_send(self):

        # Create the resource type
        urlRequestType = UrlRequestResourceType()
        self.assertEqual(urlRequestType.name, "url_request")

        # GET
        request = urlRequestType.open("http://myhost.com")
        response = request.send("/myurl")
        self.assertEqual(response, """\
http://myhost.com/myurl""")

        # POST
        request.add_data("My POST data.")
        response = request.send("/myurl")
        self.assertEqual(response, """\
http://myhost.com/myurl
My POST data.""")

        # POST with headers
        request.add_data("My other POST data.")
        request.add_header("MyHeader", "MyValue")
        request.add_unredirected_header("MyUnredirectedHeader", "MyUnredirectedValue")
        response = request.send("/myotherurl")
        self.assertEqual(response, """\
http://myhost.com/myotherurl
('MyHeader', 'MyValue')
('MyUnredirectedHeader', 'MyUnredirectedValue')
My other POST data.""")
