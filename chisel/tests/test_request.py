#
# Copyright (C) 2012-2016 Craig Hobbs
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

import unittest

from chisel import request, Request


class TestRequest(unittest.TestCase):

    def test_reqeust(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request)
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, ())
        req.onload(None) # called by application
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_name(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, name='foo')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, ((None, '/foo'),))
        self.assertEqual(req.doc, ())
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, urls=(('GET', '/bar'), (None, '/bonk'), '/thud'))
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(req.doc, ())
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_name_and_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, name='foo', urls=(('GET', '/bar'), (None, '/bonk'), '/thud'))
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, (('GET', '/bar'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(req.doc, ())
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_decorator_doc(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, doc=('doc line 1', 'doc line 2'))
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, ('doc line 1', 'doc line 2'))
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_none(self):

        try:
            Request()
        except AssertionError as exc:
            self.assertEqual(str(exc), 'must specify either wsgi_callback and/or name')
        else:
            self.fail()

        req = Request(name='my_request')
        self.assertEqual(req.wsgi_callback, None)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, ())
        req.onload(None) # called by application
        try:
            req({}, lambda status, headers: None)
        except AssertionError as exc:
            self.assertEqual(str(exc), 'must specify wsgi_callback when using Request directly')
        else:
            self.fail()

    def test_decorator(self):

        @request
        def my_request(dummy_environ, dummy_start_response):
            return ['ok']
        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request({}, lambda status, headers: None), ['ok'])
        self.assertEqual(my_request.name, 'my_request')
        self.assertEqual(my_request.urls, ((None, '/my_request'),))
        self.assertEqual(my_request.doc, ())

    def test_decorator_complete(self):

        @request(name='foo', urls=(('GET', '/bar'), (None, '/bonk'), '/thud'), doc=('doc line 1', 'doc line 2'))
        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request.name, 'foo')
        self.assertEqual(my_request.urls, (('GET', '/bar'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(my_request.doc, ('doc line 1', 'doc line 2'))
        self.assertEqual(my_request({}, lambda status, headers: None), ['ok'])
