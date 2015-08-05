#
# Copyright (C) 2012-2015 Craig Hobbs
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

import chisel

import unittest


# Tests for the request decorator
class TestRequest(unittest.TestCase):

    def setUp(self):
        self.app = chisel.Application()

    # Default request decorator
    def test_request_decorator(self):

        @chisel.request
        def myRequest(dummy_environ, dummy_start_response):
            return []
        self.assertTrue(isinstance(myRequest, chisel.Request))
        self.app.add_request(myRequest)
        self.assertEqual(myRequest({}, lambda x, y: None), [])
        self.assertEqual(myRequest.name, 'myRequest')
        self.assertEqual(myRequest.urls, ('/myRequest',))

    # Request decorator with name
    def test_request_decorator_name(self):

        @chisel.request(name='foo')
        def myRequest(dummy_environ, dummy_start_response):
            return []
        self.assertTrue(isinstance(myRequest, chisel.Request))
        self.app.add_request(myRequest)
        self.assertEqual(myRequest({}, lambda x, y: None), [])
        self.assertEqual(myRequest.name, 'foo')
        self.assertEqual(myRequest.urls, ('/foo',))

    # Request decorator with URLs
    def test_request_decorator_urls(self):

        @chisel.request(urls=('/bar', '/thud',))
        def myRequest(dummy_environ, dummy_start_response):
            return []
        self.assertTrue(isinstance(myRequest, chisel.Request))
        self.app.add_request(myRequest)
        self.assertEqual(myRequest({}, lambda x, y: None), [])
        self.assertEqual(myRequest.name, 'myRequest')
        self.assertEqual(myRequest.urls, ('/bar', '/thud'))

    # Decorator with name and URLs
    def test_request_decorator_name_and_urls(self):

        @chisel.request(name='foo', urls=('/bar', '/thud'))
        def myRequest(dummy_environ, dummy_start_response):
            return []
        self.assertTrue(isinstance(myRequest, chisel.Request))
        self.app.add_request(myRequest)
        self.assertEqual(myRequest({}, lambda x, y: None), [])
        self.assertEqual(myRequest.name, 'foo')
        self.assertEqual(myRequest.urls, ('/bar', '/thud'))

    # Request headers
    def test_request_headers(self):

        @chisel.request(name='foo')
        def myRequest(environ, start_response):
            ctx = environ[chisel.Application.ENVIRON_CTX]
            ctx.add_header('OtherHeader', 'Other Value')
            start_response('200 OK', (('MyHeader', 'MyValue'),))
            return ['OK'.encode('utf-8')]
        self.app.add_request(myRequest)
        status, headers, response = self.app.request('GET', '/foo')
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers, [('MyHeader', 'MyValue'), ('OtherHeader', 'Other Value')])
        self.assertEqual(response.decode('utf-8'), 'OK')
