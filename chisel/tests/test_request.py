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
        self.assertEqual(req.doc, None)
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
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_method(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, method='Get')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/my_request'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_method_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, method='Get', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), ('GET', '/bonk'), ('GET', '/thud')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_name_and_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        req = Request(my_request, name='foo', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), ['ok'])

    def test_request_doc(self):

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
        self.assertEqual(req.doc, None)
        req.onload(None) # called by application
        try:
            req({}, lambda status, headers: None)
        except AssertionError as exc:
            self.assertEqual(str(exc), 'must specify wsgi_callback when using Request directly')
        else:
            self.fail()

    def test_decorator(self):

        @request
        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request({}, lambda status, headers: None), ['ok'])
        self.assertEqual(my_request.name, 'my_request')
        self.assertEqual(my_request.urls, ((None, '/my_request'),))
        self.assertEqual(my_request.doc, None)

    def test_request_subclass(self):

        class MyRequest(Request):
            __slots__ = ('index',)

            def __init__(self, index):
                Request.__init__(self, name='MyRequest{0}'.format(index),
                                 urls=[('GET', '/my-request-{0}'.format(index))],
                                 doc=['My request number {0}.'.format(index)])
                self.index = index

            def __call__(self, environ, start_response):
                # Note: Do NOT call Request __call__ method in a subclass
                start_response('200 OK', [('Content-Type', 'text/plain')])
                return ['This is request # {0}'.format(self.index)]

        req = MyRequest(1)
        self.assertTrue(isinstance(req, Request))
        self.assertEqual(req.name, 'MyRequest1')
        self.assertEqual(req.urls, (('GET', '/my-request-1'),))
        self.assertEqual(req.doc, ['My request number 1.'])
        req.onload(None) # called by application
        self.assertEqual(req({}, lambda status, headers: None), ['This is request # 1'])

    def test_decorator_complete(self):

        @request(name='foo', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'], doc=('doc line 1', 'doc line 2'))
        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert hasattr(start_response, '__call__')
            return ['ok']
        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request.name, 'foo')
        self.assertEqual(my_request.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(my_request.doc, ('doc line 1', 'doc line 2'))
        self.assertEqual(my_request({}, lambda status, headers: None), ['ok'])
