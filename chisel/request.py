#
# Copyright (C) 2012-2015 Craig Hobbs
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

from .compat import func_name, iteritems

import hashlib
import posixpath
from pkg_resources import resource_string


def request(_wsgi_callback=None, **kwargs):
    """
    Chisel request decorator
    """
    return Request(_wsgi_callback, **kwargs) if _wsgi_callback is not None else lambda fn: Request(fn, **kwargs)


class Request(object):
    """
    Chisel request
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc')

    def __init__(self, wsgi_callback=None, name=None, urls=None, doc=None):
        self.wsgi_callback = wsgi_callback
        self.name = name if name is not None else func_name(wsgi_callback)
        self.urls = tuple(((url[0].upper(), url[1]) if isinstance(url, tuple) else (None, url)) for url in urls) \
                    if urls is not None \
                    else ((None, '/' + self.name),)
        self.doc = [] if doc is None else doc

    def onload(self, dummy_app):
        pass

    def __call__(self, environ, start_response):
        assert self.wsgi_callback is not None, 'must specify wsgi_callback when using Request directly'
        return self.wsgi_callback(environ, start_response)


class StaticRequest(Request):
    __slots__ = ('package', 'resource_name', 'content_type', 'headers', 'content', 'etag')

    EXT_TO_CONTENT_TYPE = {
        '.css': 'text/css',
        '.html': 'text/html',
        '.js': 'application/javascript',
        '.png': 'image/png',
        '.txt': 'text/plain',
    }

    def __init__(self, package, resource_name, content_type=None, headers=None, name=None, urls=None, doc=None):
        if name is None:
            name = resource_name
        if urls is None:
            urls = (('GET', '/' + posixpath.join(*resource_name.split(posixpath.sep)[1:])),)
        if doc is None:
            doc = ('The "{0}" package\'s static resource, "{1}".'.format(package, resource_name),)
        if content_type is None:
            content_type = self.EXT_TO_CONTENT_TYPE.get(posixpath.splitext(resource_name)[1].lower(), 'application/octet-stream')

        Request.__init__(self, name=name, urls=urls, doc=doc)

        self.package = package
        self.resource_name = resource_name
        self.headers = [(k, v) for k, v in iteritems(headers)] if (headers is not None) else []
        self.headers.append(('Content-Type', content_type))
        self.content = None
        self.etag = None

    def __call__(self, environ, start_response):
        ctx = environ['chisel.ctx']

        if ctx.app.validate_output or self.content is None:
            self.content = resource_string(self.package, self.resource_name)
            md5 = hashlib.md5()
            md5.update(self.content)
            self.etag = md5.hexdigest()

        etag = environ.get('HTTP_IF_NONE_MATCH')
        if not ctx.app.validate_output and etag == self.etag:
            start_response('304 Not Modified', [])
            return []

        headers = list(self.headers)
        headers.append(('ETag', self.etag))
        start_response('200 OK', headers)
        return [self.content]
