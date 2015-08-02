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

from .compat import func_name


def request(_wsgi_callback=None, name=None, urls=None, doc=None):
    """
    Chisel application request decorator
    """

    if _wsgi_callback is None:
        return lambda fn: Request(fn, name=name, urls=urls, doc=doc)
    return Request(_wsgi_callback, name=name, urls=urls, doc=doc)


class Request(object):
    """
    Chisel application request object
    """

    __slots__ = ('wsgi_callback', 'name', 'urls', 'doc', 'app')

    def __init__(self, wsgi_callback, name=None, urls=None, doc=None):
        self.wsgi_callback = wsgi_callback
        self.name = name if name is not None else func_name(wsgi_callback)
        self.urls = urls if urls is not None else ('/' + self.name,)
        self.doc = [] if doc is None else doc
        self.app = None

    def onload(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.wsgi_callback(environ, start_response)
