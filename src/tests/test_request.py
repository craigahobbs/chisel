# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring

from http import HTTPStatus
from unittest import TestCase

from chisel import request, Application, Request, RedirectRequest, StaticRequest


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
                start_response(HTTPStatus.OK, [('Content-Type', 'text/plain; charset=utf-8')])
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
        self.assertEqual(redirect.doc, ('Redirect to /new',))
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '301 Moved Permanently')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')


    def test_name(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new', name='redirect_old_to_new')
        app = Application()
        app.add_request(redirect)

        self.assertEqual(redirect.name, 'redirect_old_to_new')
        self.assertEqual(redirect.doc, ('Redirect to /new',))
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '301 Moved Permanently')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain; charset=utf-8'),
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
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')


    def test_not_permanent(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new', permanent=False)
        app = Application()
        app.add_request(redirect)

        self.assertEqual(redirect.name, 'redirect_new')
        self.assertEqual(redirect.doc, ('Redirect to /new',))
        status, headers, response = app.request('GET', '/old')
        self.assertEqual(status, '302 Found')
        self.assertListEqual(headers, [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Location', '/new')
        ])
        self.assertEqual(response, b'/new')


    def test_raw_wsgi(self):
        redirect = RedirectRequest((('GET', '/old'),), '/new', permanent=False)

        start_response_calls = []
        def start_response(status, headers):
            start_response_calls.append((status, headers))

        environ = {}
        result = redirect(environ, start_response)
        self.assertListEqual(start_response_calls, [
            ('302 Found', [('Content-Type', 'text/plain; charset=utf-8'), ('Location', '/new')])
        ])
        self.assertListEqual(list(result), [b'/new'])


class TestStatic(TestCase):

    def test_init(self):
        static = StaticRequest('index.html', b'<!DOCTYPE html>')
        self.assertEqual(static.name, 'index.html')
        self.assertEqual(static.urls, (('GET', '/index.html'),))
        self.assertEqual(static.doc, ('The static resource "index.html"',))
        self.assertEqual(static.content, b'<!DOCTYPE html>')
        self.assertEqual(static.content_type, 'text/html; charset=utf-8')
        self.assertEqual(static.etag, 'fe364450e1391215f596d043488f989f')


    def test_init_doc(self):
        static = StaticRequest('index.html', b'<!DOCTYPE html>', doc=('This is the doc!',))
        self.assertEqual(static.name, 'index.html')
        self.assertEqual(static.urls, (('GET', '/index.html'),))
        self.assertEqual(static.doc, ('This is the doc!',))
        self.assertEqual(static.content, b'<!DOCTYPE html>')
        self.assertEqual(static.content_type, 'text/html; charset=utf-8')
        self.assertEqual(static.etag, 'fe364450e1391215f596d043488f989f')


    def test_init_urls(self):
        static = StaticRequest('index', b'<!DOCTYPE html>', urls=(('GET', '/index.html'),))
        self.assertEqual(static.name, 'index')
        self.assertEqual(static.urls, (('GET', '/index.html'),))
        self.assertEqual(static.doc, ('The static resource "index"',))
        self.assertEqual(static.content, b'<!DOCTYPE html>')
        self.assertEqual(static.content_type, 'text/html; charset=utf-8')
        self.assertEqual(static.etag, 'fe364450e1391215f596d043488f989f')


    def test_content_type(self):
        static = StaticRequest('index', b'<!DOCTYPE html>', content_type='text/html; charset=utf-8')
        self.assertEqual(static.name, 'index')
        self.assertEqual(static.urls, (('GET', '/index'),))
        self.assertEqual(static.doc, ('The static resource "index"',))
        self.assertEqual(static.content, b'<!DOCTYPE html>')
        self.assertEqual(static.content_type, 'text/html; charset=utf-8')
        self.assertEqual(static.etag, 'fe364450e1391215f596d043488f989f')


    def test_content_type_unknown(self):
        with self.assertRaises(AssertionError) as cm_exc:
            StaticRequest('index.unknown', b'<!DOCTYPE html>')
        self.assertEqual(str(cm_exc.exception), 'Unknown content type for static resource "index.unknown"')


    def test_request(self):
        app = Application()
        static = StaticRequest('chisel-doc', b'<!DOCTYPE html>', urls=(('GET', '/doc/index.html'),))
        app.add_request(static)
        status, headers, response = app.request('GET', '/doc/index.html')
        self.assertEqual(status, '200 OK')
        self.assertListEqual(headers, [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'fe364450e1391215f596d043488f989f')])
        self.assertEqual(response, b'<!DOCTYPE html>')


    def test_request_not_modified(self):
        app = Application()
        static = StaticRequest('chisel-doc', b'<!DOCTYPE html>', urls=(('GET', '/doc/index.html'),))
        app.add_request(static)
        status, headers, response = app.request(
            'GET',
            '/doc/index.html',
            environ={'HTTP_IF_NONE_MATCH': 'fe364450e1391215f596d043488f989f'}
        )
        self.assertEqual(status, '304 Not Modified')
        self.assertListEqual(headers, [])
        self.assertEqual(response, b'')


    def test_raw_wsgi(self):
        redirect = StaticRequest('test.txt', b'Hello!')

        start_response_calls = []
        def start_response(status, headers):
            start_response_calls.append((status, headers))

        environ = {}
        result = redirect(environ, start_response)
        self.assertListEqual(start_response_calls, [
            ('200 OK', [('Content-Type', 'text/plain; charset=utf-8'), ('ETag', '952d2c56d0485958336747bcdd98590d')])
        ])
        self.assertListEqual(list(result), [b'Hello!'])


    def test_raw_wsgi_not_modified(self):
        redirect = StaticRequest('test.txt', b'Hello!')

        start_response_calls = []
        def start_response(status, headers):
            start_response_calls.append((status, headers))

        environ = {'HTTP_IF_NONE_MATCH': '952d2c56d0485958336747bcdd98590d'}
        result = redirect(environ, start_response)
        self.assertListEqual(start_response_calls, [
            ('304 Not Modified', [])
        ])
        self.assertListEqual(list(result), [])
