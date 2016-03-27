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

from .compat import basestring_, func_name


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

    def __init__(self, wsgi_callback=None, name=None, method=None, urls=None, doc=None):
        assert wsgi_callback is not None or name is not None, 'must specify either wsgi_callback and/or name'
        method = method and method.upper()
        self.wsgi_callback = wsgi_callback
        self.name = name if name is not None else func_name(wsgi_callback)
        self.urls = ((method, '/' + self.name),) if urls is None else \
                    tuple((method, url) if isinstance(url, basestring_) else ((url[0] and url[0].upper()) or method, url[1])
                          for url in urls)
        self.doc = doc

    def onload(self, app):
        pass

    def __call__(self, environ, start_response):
        assert self.wsgi_callback is not None, 'must specify wsgi_callback when using Request directly'
        return self.wsgi_callback(environ, start_response)
