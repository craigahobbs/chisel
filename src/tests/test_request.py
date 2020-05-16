# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

from http import HTTPStatus
import sys
import unittest.mock

from chisel import request, Application, Request, RedirectRequest, StaticRequest

from . import TestCase


class TestRequest(TestCase):

    def test_reqeust(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
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
            start_response('OK', [])
            return [b'ok']

        req = Request(my_request, name='foo')
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, ((None, '/foo'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        req = Request(my_request, urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), None])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/my_request')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_method_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        req = Request(my_request, urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), None])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/my_request')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_urls_str(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        req = Request(my_request, urls=[(None, '/bar')])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/bar'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

        req = Request(my_request, urls=[('get', '/bar')])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'),))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

        req = Request(my_request, urls=[('get', '/bar'), ('POST', '/bar')])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/bar')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_name_and_urls(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        req = Request(my_request, name='foo', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), None])
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'foo')
        self.assertEqual(req.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/foo')))
        self.assertEqual(req.doc, None)
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_doc(self):

        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        req = Request(my_request, doc=('doc line 1', 'doc line 2'))
        self.assertEqual(req.wsgi_callback, my_request)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, ('doc line 1', 'doc line 2'))
        self.assertEqual(req({}, lambda status, headers: None), [b'ok'])

    def test_request_none(self):

        with self.assertRaises(AssertionError) as cm_exc:
            Request()
        self.assertEqual(str(cm_exc.exception), 'must specify either wsgi_callback and/or name')

        req = Request(name='my_request')
        self.assertEqual(req.wsgi_callback, None)
        self.assertEqual(req.name, 'my_request')
        self.assertEqual(req.urls, ((None, '/my_request'),))
        self.assertEqual(req.doc, None)
        with self.assertRaises(AssertionError) as cm_exc:
            req({}, None)
        self.assertEqual(str(cm_exc.exception), 'wsgi_callback required when using Request directly')

    def test_decorator(self):

        @request
        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request({}, lambda status, headers: None), [b'ok'])
        self.assertEqual(my_request.name, 'my_request')
        self.assertEqual(my_request.urls, ((None, '/my_request'),))
        self.assertEqual(my_request.doc, None)

    def test_decorator_complete(self):

        @request(name='foo', urls=[('GET', '/bar'), ('post', '/thud'), (None, '/bonk'), None], doc=('doc line 1', 'doc line 2'))
        def my_request(environ, start_response):
            assert isinstance(environ, dict)
            assert callable(start_response)
            start_response('OK', [])
            return [b'ok']

        self.assertTrue(isinstance(my_request, Request))
        self.assertEqual(my_request.name, 'foo')
        self.assertEqual(my_request.urls, (('GET', '/bar'), ('POST', '/thud'), (None, '/bonk'), (None, '/foo')))
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
                super().__init__(name=f'MyRequest{index}',
                                 urls=[('GET', f'/my-request-{index}')],
                                 doc=[f'My request number {index}.'])
                self.index = index

            def __call__(self, environ, start_response):
                # Note: Do NOT call Request __call__ method in a subclass
                start_response(HTTPStatus.OK, [('Content-Type', 'text/plain')])
                return [f'This is request # {self.index}'.encode('utf-8')]

        req = MyRequest(1)
        self.assertTrue(isinstance(req, Request))
        self.assertEqual(req.name, 'MyRequest1')
        self.assertEqual(req.urls, (('GET', '/my-request-1'),))
        self.assertEqual(req.doc, ['My request number 1.'])
        self.assertEqual(req({}, lambda status, headers: None), [b'This is request # 1'])


class TestRedirect(TestCase):

    def test_default(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new')
        app = Application()
        app.add_request(redirect)

        self.assertEqual(redirect.name, 'redirect_new')
        self.assertEqual(redirect.doc, 'Redirect to /new.')
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '301 Moved Permanently')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')

    def test_name(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new', name='redirect_old_to_new')
        app = Application()
        app.add_request(redirect)

        self.assertEqual(redirect.name, 'redirect_old_to_new')
        self.assertEqual(redirect.doc, 'Redirect to /new.')
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '301 Moved Permanently')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')

    def test_doc(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new', doc=('Redirect old to new',))
        app = Application()
        app.add_request(redirect)

        self.assertEqual(redirect.name, 'redirect_new')
        self.assertEqual(redirect.doc, ('Redirect old to new',))
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '301 Moved Permanently')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')

    def test_not_permanent(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new', permanent=False)
        app = Application()
        app.add_request(redirect)

        self.assertEqual(redirect.name, 'redirect_new')
        self.assertEqual(redirect.doc, 'Redirect to /new.')
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '302 Found')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')

class TestStatic(TestCase):

    def test_default(self):
        static = StaticRequest('chisel', 'static/doc.html')
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'static_doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/static/doc.html'),))
        self.assertEqual(static.doc, 'The "chisel" package\'s static resource, "static/doc.html".')
        status, headers, response = app.request('GET', '/static/doc.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/html'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))

    def test_name(self):
        static = StaticRequest('chisel', 'static/doc.html', name='doc_html')
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/static/doc.html'),))
        self.assertEqual(static.doc, 'The "chisel" package\'s static resource, "static/doc.html".')
        status, headers, response = app.request('GET', '/static/doc.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/html'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))

    def test_urls(self):
        static = StaticRequest('chisel', 'static/doc.html', urls=(('GET', '/doc.html'),))
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'static_doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/doc.html'),))
        self.assertEqual(static.doc, 'The "chisel" package\'s static resource, "static/doc.html".')
        status, headers, response = app.request('GET', '/doc.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/html'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))

    def test_doc(self):
        static = StaticRequest('chisel', 'static/doc.html', doc=('doc.html',))
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'static_doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/static/doc.html'),))
        self.assertEqual(static.doc, ('doc.html',))
        status, headers, response = app.request('GET', '/static/doc.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/html'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))

    def test_content_type(self):
        static = StaticRequest('chisel', 'static/doc.html', content_type='text/plain')
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'static_doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/static/doc.html'),))
        self.assertEqual(static.doc, 'The "chisel" package\'s static resource, "static/doc.html".')
        status, headers, response = app.request('GET', '/static/doc.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))

    def test_cache(self):
        static = StaticRequest('chisel', 'static/doc.html', cache=False)
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'static_doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/static/doc.html'),))
        self.assertEqual(static.doc, 'The "chisel" package\'s static resource, "static/doc.html".')
        status, headers, response = app.request('GET', '/static/doc.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/html'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))

    def test_etag(self):
        static = StaticRequest('chisel', 'static/doc.html')
        app = Application()
        app.add_request(static)

        self.assertEqual(static.name, 'static_doc_html')
        self.assertTupleEqual(static.urls, (('GET', '/static/doc.html'),))
        self.assertEqual(static.doc, 'The "chisel" package\'s static resource, "static/doc.html".')
        status, headers, response = app.request('GET', '/static/doc.html',
                                                environ={'HTTP_IF_NONE_MATCH': '5c5f258e0e96d9bb4d283a46d06926d4'})
        self.assertEqual(status, '304 Not Modified')
        self.assertListEqual(headers, [])
        self.assertEqual(response, b'')
        status, headers, response = app.request('GET', '/static/doc.html', environ={'HTTP_IF_NONE_MATCH': 'wrong'})
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/html'),
            ('ETag', '5c5f258e0e96d9bb4d283a46d06926d4')
        ])
        self.assertTrue(response.startswith(b'<!DOCTYPE html>'))
