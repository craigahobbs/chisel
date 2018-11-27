# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from http import HTTPStatus
import unittest.mock
import sys

from chisel import request, Request

from . import TestCase


class TestRequest(TestCase):

    def test_reqeust(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request)
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_name(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, name='foo')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, ((None, '/foo'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_method(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, method='Get')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/my_request'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_method_multiple(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, method=('Get', 'POST'), urls=[None, '/other', ('PUT', None), ('DELETE', '/delete'), (None, '/all')])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (
            ('GET', '/my_request'),
            ('POST', '/my_request'),
            ('GET', '/other'),
            ('POST', '/other'),
            ('PUT', '/my_request'),
            ('DELETE', '/delete'),
            (None, '/all'),
        ))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_method_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, method='Get', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), ('GET', '/thud')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_urls_str(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, urls='/bar')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/bar'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

        req = Request(my_request, method='get', urls='/bar')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

        req = Request(my_request, method=('get', 'POST'), urls='/bar')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/bar')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_name_and_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, name='foo', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_doc(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        req = Request(my_request, doc=('doc line 1', 'doc line 2'))
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, ('doc line 1', 'doc line 2'))
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

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
            assert callable(start_response)
            return [b'ok']

        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request({}, lambda status, headers: None), [b'ok'])
        self.assertEqual(my_request.name, 'my_request')
        self.assertEqual(my_request.urls, ((None, '/my_request'),))
        self.assertEqual(my_request.doc, None)

    def test_decorator_complete(self):

        @request(name='foo', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), '/thud'], doc=('doc line 1', 'doc line 2'))
        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            return [b'ok']

        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request.name, 'foo')
        self.assertEqual(my_request.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/thud')))
        self.assertEqual(my_request.doc, ('doc line 1', 'doc line 2'))
        self.assertEqual(my_request({}, lambda status, headers: None), [b'ok'])

    def test_import_requests(self):

        test_files = (
            (
                ('__init__.py',),
                ''
            ),
            (
                ('test_package', '__init__.py',),
                ''
            ),
            (
                ('test_package', 'module.py',),
                '''\
from chisel import request

@request
def request1(environ, start_response):
    return [b'request1']

@request
def request2(environ, start_response):
    return [b'request2']
'''
            ),
            (
                ('test_package', 'module2.py',),
                ''
            ),
            (
                ('test_package', 'sub', '__init__.py'),
                ''
            ),
            (
                ('test_package', 'sub', 'subsub', '__init__.py'),
                ''
            ),
            (
                ('test_package', 'sub', 'subsub', 'submodule.py'),
                '''\
from chisel import request

@request
def request3(environ, start_response):
    return [b'request3']
'''
            )
        )
        with self.create_test_files(test_files) as requests_dir:
            with unittest.mock.patch('sys.path', [requests_dir] + sys.path):
                self.assertListEqual(
                    sorted(request.name for request in Request.import_requests('test_package')),
                    [
                        'request1',
                        'request2',
                        'request3'
                    ]
                )

    def test_request_subclass(self):

        class MyRequest(Request):
            __slots__ = ('index',)

            def __init__(self, index):
                super().__init__(name='MyRequest{0}'.format(index),
                                 urls=[('GET', '/my-request-{0}'.format(index))],
                                 doc=['My request number {0}.'.format(index)])
                self.index = index

            def __call__(self, environ, start_response):
                # Note: Do NOT call Request __call__ method in a subclass
                start_response(HTTPStatus.OK, [('Content-Type', 'text/plain')])
                return ['This is request # {0}'.format(self.index).encode('utf-8')]

        req = MyRequest(1)
        self.assertTrue(isinstance(req, Request))
        self.assertEqual(req.name, 'MyRequest1')
        self.assertEqual(req.urls, (('GET', '/my-request-1'),))
        self.assertEqual(req.doc, ['My request number 1.'])
        self.assertEqual(req({}, lambda status, headers: None), [b'This is request # 1'])
