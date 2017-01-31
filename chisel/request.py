# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from itertools import chain
import sys

from .util import import_submodules


REQUESTS_MODULE_ATTR = '__chisel_requests__'


def request(_wsgi_callback=None, **kwargs):
    """
    Chisel request decorator
    """
    if _wsgi_callback is None:
        return lambda fn: request(fn, **kwargs)
    else:
        return Request(_wsgi_callback, **kwargs).decorate_module(_wsgi_callback)


class Request(object):
    """
    Chisel request
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc', 'doc_group')

    def __init__(self, wsgi_callback=None, name=None, method=None, urls=None, doc=None, doc_group=None):
        assert wsgi_callback is not None or name is not None, 'must specify either wsgi_callback and/or name'

        self.wsgi_callback = wsgi_callback
        self.name = name or wsgi_callback.__name__
        self.doc = doc
        self.doc_group = doc_group

        # Normalize methods into list of uppercase strings (or None)
        if method is None:
            methods = (None,)
        elif isinstance(method, str):
            methods = (method.upper(),)
        else:
            methods = tuple(method.upper() for method in method)

        # Normalize urls into list of uppercase-method/url tuple pairs
        if urls is None:
            self.urls = tuple((method, '/' + self.name) for method in methods)
        elif isinstance(urls, str):
            self.urls = tuple((method, urls) for method in methods)
        else:
            self.urls = tuple(chain.from_iterable(
                ((method, '/' + self.name) for method in methods) if url is None else \
                ((method, url) for method in methods) if isinstance(url, str) else \
                ((url[0] and url[0].upper(), url[1] or '/' + self.name),)
                for url in urls
            ))

    def onload(self, app):
        pass

    def __call__(self, environ, start_response):
        assert self.wsgi_callback is not None, 'must specify wsgi_callback when using Request directly'
        return self.wsgi_callback(environ, start_response)

    def decorate_module(self, callback):
        if callback.__module__:
            module = sys.modules[callback.__module__]
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is None:
                requests = {}
                setattr(module, REQUESTS_MODULE_ATTR, requests)
            requests[self.name] = self
        return self

    @staticmethod
    def import_requests(package, parent_package=None):
        for module in import_submodules(package, parent_package):
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests is not None:
                yield from iter(requests.values())
