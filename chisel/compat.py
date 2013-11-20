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

PY3 = (sys.version_info >= (3, 0))
_PY27 = (sys.version_info >= (2, 7))
_PY32 = (sys.version_info >= (3, 2))

# types
if PY3: # pragma: no cover
    basestring_ = str
    long_ = int
    xrange_ = range
else:
    basestring_ = basestring
    long_ = long
    xrange_ = xrange

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

# cgi
if _PY32: # pragma: no cover
    import html as _html
    class cgi(object):
        __slots__ = ()
        escape = _html.escape
else:
    import cgi as _cgi
    cgi = _cgi

# json
if _PY27:
    import json as _json
else: # pragma: no cover
    try:
        import simplejson as _json
    except:
        import json as _json
json = _json

# StringIO
if PY3: # pragma: no cover
    import io as _io
    StringIO = _io.StringIO
else:
    try:
        import cStringIO as _StringIO
    except: # pragma: no cover
        import StringIO as _StringIO
    StringIO = _StringIO.StringIO

# urllib, urlparse
if PY3: # pragma: no cover
    import urllib.parse as _urllib_parse
    class urllib(object):
        __slots__ = ()
        quote = _urllib_parse.quote
        unquote = _urllib_parse.unquote
else:
    import urllib as _urllib
    urllib = _urllib

# HTMLParser
if PY3: # pragma: no cover
    import html.parser as _html_parser
    HTMLParser = _html_parser.HTMLParser
else:
    import HTMLParser as _HTMLParser
    HTMLParser = _HTMLParser.HTMLParser
