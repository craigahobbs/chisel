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

from itertools import chain
import sys

from .app_defs import ENVIRON_CTX
from .util import import_submodules


REQUESTS_MODULE_ATTR = '__chisel_requests__'


def request(_wsgi_callback=None, **kwargs):
    """
    Chisel request decorator
    """
    return Request(_wsgi_callback, **kwargs).decorate_module(_wsgi_callback) if _wsgi_callback else lambda fn: request(fn, **kwargs)


class Request(object):
    """
    Chisel request
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc', 'doc_group')

    def __init__(self, wsgi_callback=None, name=None, method=None, urls=None, doc=None, doc_group=None):
        assert wsgi_callback is not None or name is not None, 'must specify either wsgi_callback and/or name'

        methods = (method and method.upper(),) if method is None or isinstance(method, str) else \
                  tuple(method.upper() for method in method)

        self.wsgi_callback = wsgi_callback
        self.name = name or wsgi_callback.__name__
        self.urls = tuple((method, '/' + self.name) for method in methods) if urls is None else \
               tuple((method, urls) for method in methods) if isinstance(urls, str) else \
               tuple(chain.from_iterable(
                   ((method, '/' + self.name) for method in methods) if url is None else \
                   ((method, url) for method in methods) if isinstance(url, str) else \
                   ((url[0] and url[0].upper(), url[1] or '/' + self.name),)
                   for url in urls))
        self.doc = doc
        self.doc_group = doc_group

    def onload(self, app):
        pass

    def __call__(self, environ, start_response):
        assert self.wsgi_callback is not None, 'must specify wsgi_callback when using Request directly'
        ctx = environ.get(ENVIRON_CTX)
        if ctx is not None:
            ctx.add_cache_headers()
        return self.wsgi_callback(environ, start_response)

    def decorate_module(self, callback):
        if callback.__module__:
            module = sys.modules[callback.__module__]
            requests = getattr(module, REQUESTS_MODULE_ATTR, [])
            if not requests:
                setattr(module, REQUESTS_MODULE_ATTR, requests)
            requests.append(self)
        return self

    @staticmethod
    def import_requests(package, parent_package=None):
        for module in import_submodules(package, parent_package):
            requests = getattr(module, REQUESTS_MODULE_ATTR, None)
            if requests:
                yield from iter(requests)
