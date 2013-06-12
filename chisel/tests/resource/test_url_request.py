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

# Replace urllib2 with mock
import sys
from . import chisel_compat
sys.modules['chisel.compat'] = chisel_compat

from chisel.resource.url_request import UrlRequestResourceType

# Restore urllib2
del sys.modules['chisel.compat']

import unittest


# Test UrlRequestResource functionality
class TestResourceUrlRequest(unittest.TestCase):

    # Test UrlRequestResource setup and send
    def test_resource_url_request(self):

        # Create the resource type
        urlRequestType = UrlRequestResourceType()

        request = urlRequestType.open('http://myhost.com/mypath/')

        # GET (trailing slash, append to URL)
        response = request.send('myurl')
        self.assertEqual(response, '''\
http://myhost.com/mypath/myurl''')

        # GET (trailing slash, append to URL - non-default timeout)
        response = request.send('myurl', timeout = 10)
        self.assertEqual(response, '''\
http://myhost.com/mypath/myurl''')

        # GET (trailing slash, replace URL)
        response = request.send('/myurl')
        self.assertEqual(response, '''\
http://myhost.com/myurl''')

        # GET (trailing slash, no URL)
        response = request.send()
        self.assertEqual(response, '''\
http://myhost.com/mypath/''')

        # GET (trailing slash, params only)
        response = request.send('?a=1&b=2')
        self.assertEqual(response, '''\
http://myhost.com/mypath/?a=1&b=2''')

        request = urlRequestType.open('http://myhost.com/mypath/myresource')

        # GET (no trailing slash, replace resource)
        response = request.send('myurl')
        self.assertEqual(response, '''\
http://myhost.com/mypath/myurl''')

        # GET (no trailing slash, replace URL)
        response = request.send('/myurl')
        self.assertEqual(response, '''\
http://myhost.com/myurl''')

        # GET (no trailing slash, empty URL)
        response = request.send()
        self.assertEqual(response, '''\
http://myhost.com/mypath/myresource''')

        # GET (no trailing slash, params only)
        response = request.send('?a=1&b=2')
        self.assertEqual(response, '''\
http://myhost.com/mypath/myresource?a=1&b=2''')

        request = urlRequestType.open('http://myhost.com/mypath/')

        # POST
        request.add_data('My POST data.')
        response = request.send()
        self.assertEqual(response, '''\
http://myhost.com/mypath/
My POST data.''')

        # POST with headers
        request.add_data('My other POST data.')
        request.add_header('MyHeader', 'MyValue')
        request.add_unredirected_header('MyUnredirectedHeader', 'MyUnredirectedValue')
        response = request.send()
        self.assertEqual(response, '''\
http://myhost.com/mypath/
('MyHeader', 'MyValue')
('MyUnredirectedHeader', 'MyUnredirectedValue')
My other POST data.''')
