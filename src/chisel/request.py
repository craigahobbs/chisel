# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

"""
Chisel request base class and common request classes
"""

from functools import partial
import hashlib
from http import HTTPStatus
from itertools import chain
import posixpath
import re


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
    return Request(wsgi_callback, **kwargs)


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

    __slots__ = ('status', 'redirect_url', 'content')

    def __init__(self, urls, redirect_url, permanent=True, name=None, doc=None, doc_group='Redirects'):
        if name is None:
            name = re.sub(r'([^\w]|_)+', '_', f'redirect_{redirect_url}').rstrip('_')
        if doc is None:
            doc = (f'Redirect to {redirect_url}',)
        super().__init__(name=name, urls=urls, doc=doc, doc_group=doc_group)
        status = HTTPStatus.MOVED_PERMANENTLY if permanent else HTTPStatus.FOUND
        self.status = f'{status.value} {status.phrase}'
        self.redirect_url = redirect_url
        self.content = redirect_url.encode('utf-8')

    def __call__(self, environ, start_response):
        start_response(self.status, [('Content-Type', 'text/plain; charset=utf-8'), ('Location', self.redirect_url)])
        return [self.content]


class StaticRequest(Request):
    """
    A static resource request

    :param str name: The request name. The default name is the callback function's name.
    :param bytes content: The static content
    :param str content_type: Optional content type string. If None, the content type is auto-determined.
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    :param doc: The documentation markdown text lines
    :type doc: str or list(str)
    :param str doc_group: The documentation group
    """

    __slots__ = ('content', 'content_type', 'etag')

    EXT_TO_CONTENT_TYPE = {
        '.bare': 'text/plain; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.csv': 'text/csv; charset=utf-8',
        '.gif': 'image/gif',
        '.htm': 'text/html; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.jpeg': 'image/jpeg',
        '.jpg': 'image/jpeg',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.markdown': 'text/markdown; charset=utf-8',
        '.md': 'text/markdown; charset=utf-8',
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.smd': 'text/plain; charset=utf-8',
        '.svg': 'image/svg+xml; charset=utf-8',
        '.tif': 'image/tiff',
        '.tiff': 'image/tiff',
        '.txt': 'text/plain; charset=utf-8',
        '.webp': 'image/webp'
    }
    STATUS_OK = f'{HTTPStatus.OK.value} {HTTPStatus.OK.phrase}'
    STATUS_NOT_MODIFIED = f'{HTTPStatus.NOT_MODIFIED.value} {HTTPStatus.NOT_MODIFIED.phrase}'

    def __init__(self, name, content, content_type=None, urls=None, doc=None, doc_group='Statics'):
        if doc is None:
            doc = (f'The static resource "{name}"',)
        if urls is None:
            urls = (('GET', f'/{name}'),)
        super().__init__(name=name, urls=urls, doc=doc, doc_group=doc_group)
        self.content = content

        # Compute the content type
        if content_type is None:
            content_ext = next(
                (ext for ext in (posixpath.splitext(path)[1] for _, path in self.urls) if ext in self.EXT_TO_CONTENT_TYPE),
                ''
            )
            content_type = self.EXT_TO_CONTENT_TYPE.get(content_ext)
            assert content_type, f'Unknown content type for static resource "{name}"'
        self.content_type = content_type

        # Compute the etag
        md5 = hashlib.md5()
        md5.update(self.content)
        self.etag = md5.hexdigest()

    def __call__(self, environ, start_response):

        # Check the etag - is the resource modified?
        if self.etag == environ.get('HTTP_IF_NONE_MATCH'):
            start_response(self.STATUS_NOT_MODIFIED, [])
            return []

        start_response(self.STATUS_OK, [('Content-Type', self.content_type), ('ETag', self.etag)])
        return [self.content]
