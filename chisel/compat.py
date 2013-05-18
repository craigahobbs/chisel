#
# Copyright (C) 2012-2013 Craig Hobbs
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

import sys

PY27 = (sys.version_info == (2, 7))
PY3 = (sys.version_info >= (3, 0))
PY32 = (sys.version_info >= (3, 2))

# cgi
if PY32: # pragma: no cover
    import html as _html
    class cgi(object):
        escape = _html.escape
else:
    import cgi

# json
if PY27:
    import json
else:
    try:
        import simplejson as json
    except:
        import json

# pickle
if PY3: # pragma: no cover
    import pickle
else:
    try:
        import cPickle as pickle
    except: # pragma: no cover
        import pickle

# StringIO
if PY3: # pragma: no cover
    from io import StringIO
else:
    try:
        from cStringIO import StringIO
    except: # pragma: no cover
        from StringIO import StringIO

# urllib, urllib2, urlparse
if PY3: # pragma: no cover
    import urllib as _urllib
    import urllib.error as _urllib_error
    import urllib.parse as _urllib_parse
    class urllib(object):
        quote = _urllib_parse.quote
        unquote = _urllib_parse.unquote
    class urllib2(object):
        URLError = _urllib_error.URLError
    class urlparse(object):
        urljoin = _urllib_parse.urljoin
else:
    import urllib
    import urllib2
    import urlparse

# HTMLParser
if PY3: # pragma: no cover
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser

# types
if PY3: # pragma: no cover
    basestring_ = str
    long_ = int
    unichr_ = chr
    unicode_ = str
    xrange_ = range
else:
    basestring_ = basestring
    long_ = long
    unichr_ = unichr
    unicode_ = unicode
    xrange_ = xrange

# WSGI
if PY3: # pragma: no cover
    wsgistr_ = bytes
    def wsgistr_new(s):
        return s.encode("utf-8") if not isinstance(s, bytes) else s
    def wsgistr_str(s):
        return s.decode("utf-8")
else:
    wsgistr_ = str
    def wsgistr_new(s):
        return s
    def wsgistr_str(s):
        return s

# dict
if PY3: # pragma: no cover
    def iteritems(d):
        return d.items()
    def itervalues(d):
        return d.values()
else:
    def iteritems(d):
        return d.iteritems()
    def itervalues(d):
        return d.itervalues()

# function
if PY3: # pragma: no cover
    def func_name(f):
        return f.__name__
else:
    def func_name(f):
        return f.func_name
