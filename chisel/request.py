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


# Request WSGI application decorator
class Request(object):
    __slots__ = ('app', 'fn', 'name', 'urls', 'doc')

    def __init__(self, _fn=None, name=None, urls=None, doc=None):
        self.app = None
        self.fn = _fn
        self.name = name
        self.urls = urls
        self.doc = [] if doc is None else doc
        self._setDefaults()

    def _setDefaults(self):

        # Set the default request name, if necessary
        if self.name is None and self.fn is not None:
            self.name = func_name(self.fn)

        # Set the default urls, if necessary
        if self.urls is None and self.name is not None:
            self.urls = ('/' + self.name,)

    def __call__(self, *args):

        # If not constructed as function decorator, first call must be function decorator...
        if self.fn is None:
            self.fn, = args
            self._setDefaults()
            return self
        else:
            environ, start_response = args
            return self.call(environ, start_response)

    def onload(self, app):
        self.app = app

    def call(self, environ, start_response):
        return self.fn(environ, start_response)
