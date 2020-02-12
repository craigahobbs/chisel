# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
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


def request(request_callback=None, **kwargs):
    """
    TODO
    """

    if request_callback is None:
        return partial(request, **kwargs)
    return Request(request_callback, **kwargs).decorate_module(request_callback)


class Request:
    """
    TODO
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc', 'doc_group')

    def __init__(self, wsgi_callback=None, name=None, urls=None, doc=None, doc_group=None):
        assert wsgi_callback is not None or name is not None, 'must specify either wsgi_callback and/or name'

        #: TODO
        self.wsgi_callback = wsgi_callback

        #: TODO
        self.name = name or wsgi_callback.__name__

        #: TODO
        self.doc = doc

        #: TODO
        self.doc_group = doc_group

        # Normalize urls into list of uppercase-method/path tuple pairs
        if urls is None:
            #: TODO
            self.urls = ((None, '/' + self.name),)
        else:
            self.urls = tuple(chain.from_iterable(
                ((None, '/' + self.name),) if url is None else \
                ((url[0] and url[0].upper(), url[1] or '/' + self.name),)
                for url in urls
            ))

    def __call__(self, environ, start_response):
        """
        TODO
        """

        assert self.wsgi_callback is not None, 'wsgi_callback required when using Request directly'
        return self.wsgi_callback(environ, start_response)

    def decorate_module(self, callback):
        """
        TODO
        """

        if callback.__module__: # pragma: no branch
            module = sys.modules[callback.__module__]
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is None:
                requests = {}
                setattr(module, REQUESTS_MODULE_ATTR, requests)
            requests[self.name] = self
        return self

    @staticmethod
    def import_requests(package, parent_package=None):
        """
        TODO
        """

        package = importlib.import_module(package, parent_package)
        for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            module = importlib.import_module(name)
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is not None:
                yield from iter(requests.values())


class RedirectRequest(Request):
    """
    TODO
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
    TODO
    """

    __slots__ = ('_package', '_resource_name', '_cache', '_headers', '_content', '_etag')

    EXT_TO_CONTENT_TYPE = {
        '.css': 'text/css',
        '.html': 'text/html',
        '.jpg': 'image/jpeg',
        '.js': 'application/javascript',
        '.png': 'image/png',
        '.txt': 'text/plain',
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
            name = re.sub(r'[^\w]+', '_', f'static_{package}_{resource_name}')
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
