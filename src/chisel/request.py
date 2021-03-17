# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel request base class and common request classes
"""

from functools import partial
import hashlib
from http import HTTPStatus
import importlib
from itertools import chain
import pkgutil
import posixpath
import re
import sys

from .app import Context


REQUESTS_MODULE_ATTR = '__chisel_requests__'


def request(wsgi_callback=None, **kwargs):
    """
    Decorator for creating a :class:`~chisel.Request` object that wraps a WSGI application function. For example:

    >>> @chisel.request
    ... def my_request(environ, start_response):
    ...    start_response('200 OK', [('Content-Type', 'text/plain')])
    ...    return [b'Hello, World!']
    ...
    >>> my_request.name, my_request.urls, my_request.doc, my_request.doc_group
    ...
    ('my_request', ((None, '/my_request'),), None, None)

    You can also pass :class:`~chisel.Request` initialization parameters to the request decorator:

    >>> @chisel.request(urls=[('GET', None)], doc='This is my request')
    ... def my_request(environ, start_response):
    ...    start_response('200 OK', [('Content-Type', 'text/plain')])
    ...    return [b'Hello, World!']
    ...
    >>> my_request.name, my_request.urls, my_request.doc, my_request.doc_group
    ...
    ('my_request', (('GET', '/my_request'),), 'This is my request', None)

    The created :class:`~chisel.Request` object is passed to an application's :meth:`~chisel.add_request` method to host
    it with that applicaton.

    >>> application = chisel.Application()
    >>> application.add_request(my_request)
    >>> application.request('GET', '/my_request')
    ('200 OK', [('Content-Type', 'text/plain')], b'Hello, World!')

    :param ~collections.abc.Callable wsgi_callback: A WSGI application function
    :returns Request: The created Request object
    """

    if wsgi_callback is None:
        return partial(request, **kwargs)
    return Request(wsgi_callback, **kwargs).decorate_module(wsgi_callback)


class Request:
    """The Chisel Request object is a wrapper that associates hosting metadata with a WSGI application function.
    See the :func:`~chisel.request` decorator for a common way to create Request objects.

    :param ~collections.abc.Callable wsgi_callback: A WSGI application function
    :param str name: The request name. The default name is the callback function's name.
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    :param doc: The documentation markdown text lines
    :type doc: str or list(str)
    :param str doc_group: The documentation group
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc', 'doc_group')

    def __init__(self, wsgi_callback=None, name=None, urls=None, doc=None, doc_group=None):
        assert wsgi_callback is not None or name is not None, 'must specify either wsgi_callback and/or name'

        #: The WSGI application function
        self.wsgi_callback = wsgi_callback

        #: The request name
        self.name = name or wsgi_callback.__name__

        #: The documentation markdown text lines
        self.doc = doc

        #: The documentation group
        self.doc_group = doc_group

        # Normalize urls into list of uppercase-method/path tuple pairs
        if urls is None:
            #: The list of URL method/path tuples
            self.urls = ((None, '/' + self.name),)
        else:
            self.urls = tuple(chain.from_iterable(
                ((None, '/' + self.name),) if url is None else \
                ((url[0] and url[0].upper(), url[1] or '/' + self.name),)
                for url in urls
            ))

    def __call__(self, environ, start_response):
        """
        The request WSGI application method. By default the wrapped wsgi_callback is called. Sub-classes may override this
        method without calling this method.

        :param dict environ: The :pep:`WSGI <3333>` environ dictionary.
        :param ~collections.abc.Callable start_response: The :pep:`WSGI <3333>` start-response callable.
        """

        assert self.wsgi_callback is not None, 'wsgi_callback required when using Request directly'
        return self.wsgi_callback(environ, start_response)

    def decorate_module(self, wsgi_callback):
        """
        Helper method to update a collection requests on the request's module. This information is used by
        :meth:`~chisel.Request.import_requests`.

        :param ~collections.abc.Callable wsgi_callback: The wrapped WSGI application function
        """

        if wsgi_callback.__module__: # pragma: no branch
            module = sys.modules[wsgi_callback.__module__]
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is None:
                requests = {}
                setattr(module, REQUESTS_MODULE_ATTR, requests)
            requests[self.name] = self
        return self

    @staticmethod
    def import_requests(package, parent_package=None):
        """
        Import reqeusts from a package.

        :param str package: The package in which to recursively load requests
        :param str parent_package: The parent package
        """

        package = importlib.import_module(package, parent_package)
        for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            module = importlib.import_module(name)
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is not None:
                yield from iter(requests.values())


class RedirectRequest(Request):
    """
    A redirect reqeust

    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    :param str redirect_url: The redirectd URL
    :param bool permanent: If True, this is a permanent redirect
    :param str name: The request name. By default the name is "redirect_<redirect_url>".
    :param doc: The documentation markdown text lines
    :type doc: str or list(str)
    :param str doc_group: The documentation group
    """

    __slots__ = ('_status', '_redirect_url')

    def __init__(self, urls, redirect_url, permanent=True, name=None, doc=None, doc_group='Redirects'):
        if name is None:
            name = re.sub(r'([^\w]|_)+', '_', f'redirect_{redirect_url}').rstrip('_')
        if doc is None:
            doc = f'Redirect to {redirect_url}.'
        super().__init__(name=name, urls=urls, doc=doc, doc_group=doc_group)
        self._status = HTTPStatus.MOVED_PERMANENTLY if permanent else HTTPStatus.FOUND
        self._redirect_url = redirect_url

    def __call__(self, environ, unused_start_response):
        ctx = environ[Context.ENVIRON_CTX]
        ctx.add_header('Location', self._redirect_url)
        return ctx.response_text(self._status, self._redirect_url)


class StaticRequest(Request):
    """
    A static resoruce request

    :param str package: The package containing the static resource
    :param str resource_name: The resource name (path)
    :param bool cache: If True, cache the static content. Otherwise, the content is loaded each request.
    :param str content_type: Optional content type string. If None, the content type is auto-determined.
    :param list(tuple) headers: Optional list of key/value header tuples
    :param str name: The request name. By default the name is "static_<redirect_url>".
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    :param doc: The documentation markdown text lines
    :type doc: str or list(str)
    :param str doc_group: The documentation group
    """

    __slots__ = ('_package', '_resource_name', '_cache', '_headers', '_content', '_etag')

    EXT_TO_CONTENT_TYPE = {
        '.css': 'text/css',
        '.html': 'text/html',
        '.jpg': 'image/jpeg',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.txt': 'text/plain'
    }

    def __init__(
            self,
            package,
            resource_name,
            cache=True,
            content_type=None,
            headers=None,
            name=None,
            urls=None,
            doc=None,
            doc_group='Statics'
    ):
        if name is None:
            name = re.sub(r'[^\w]+', '_', resource_name)
        if urls is None:
            urls = [('GET', f'/{resource_name}')]
        if doc is None:
            doc = f'The "{package}" package\'s static resource, "{resource_name}".'
        super().__init__(name=name, urls=urls, doc=doc, doc_group=doc_group)
        self._package = package
        self._resource_name = resource_name
        self._cache = cache
        if content_type is None:
            content_type = self.EXT_TO_CONTENT_TYPE.get(posixpath.splitext(resource_name)[1].lower())
            assert content_type, f'Unknown content type for "{package}" package\'s "{resource_name}" resource'
        self._headers = tuple(chain(headers or (), [('Content-Type', content_type)]))
        if cache:
            self._content, self._etag = self._load_content()

    def _load_content(self):
        content = pkgutil.get_data(self._package, self._resource_name)
        md5 = hashlib.md5()
        md5.update(content)
        return content, md5.hexdigest()

    def __call__(self, environ, start_response):

        # Check the etag - is the resource modified?
        if self._cache:
            content, etag = self._content, self._etag
        else:
            content, etag = self._load_content()
        if etag == environ.get('HTTP_IF_NONE_MATCH'):
            start_response(HTTPStatus.NOT_MODIFIED, [])
            return []

        start_response(HTTPStatus.OK, list(chain(self._headers, [('ETag', etag)])))
        return [content]
