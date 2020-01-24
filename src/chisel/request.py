# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from functools import partial
import importlib
from itertools import chain
import pkgutil
import sys


REQUESTS_MODULE_ATTR = '__chisel_requests__'


def request(request_callback=None, **kwargs):
    """
    Chisel request decorator
    """

    if request_callback is None:
        return partial(request, **kwargs)
    else:
        return Request(request_callback, **kwargs).decorate_module(request_callback)


class Request:
    """
    Chisel request
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc', 'doc_group')

    def __init__(self, wsgi_callback=None, name=None, urls=None, doc=None, doc_group=None):
        assert wsgi_callback is not None or name is not None, 'must specify either wsgi_callback and/or name'

        self.wsgi_callback = wsgi_callback
        self.name = name or wsgi_callback.__name__
        self.doc = doc
        self.doc_group = doc_group

        # Normalize urls into list of uppercase-method/path tuple pairs
        if urls is None:
            self.urls = ((None, '/' + self.name),)
        else:
            self.urls = tuple(chain.from_iterable(
                ((None, '/' + self.name),) if url is None else \
                ((url[0] and url[0].upper(), url[1] or '/' + self.name),)
                for url in urls
            ))

    def __call__(self, environ, start_response):
        assert self.wsgi_callback is not None, 'must specify wsgi_callback when using Request directly'
        return self.wsgi_callback(environ, start_response)

    def decorate_module(self, callback):
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
        package = importlib.import_module(package, parent_package)
        for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            module = importlib.import_module(name)
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is not None:
                yield from iter(requests.values())
