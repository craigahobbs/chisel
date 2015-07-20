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

import sys

_PY3 = (sys.version_info >= (3, 0))

# types
if _PY3:
    basestring_ = str
    long_ = int
    unichr_ = chr
    unicode_ = str
    xrange_ = range
else: # pragma: no cover
    basestring_ = basestring            # pylint: disable=undefined-variable
    long_ = long                        # pylint: disable=undefined-variable
    unichr_ = unichr                    # pylint: disable=undefined-variable
    unicode_ = unicode                  # pylint: disable=undefined-variable
    xrange_ = xrange                    # pylint: disable=undefined-variable

# dict
if _PY3:
    def iteritems(d):
        return iter(d.items())

    def itervalues(d):
        return iter(d.values())
else: # pragma: no cover
    def iteritems(d):
        return d.iteritems()

    def itervalues(d):
        return d.itervalues()

# function
if _PY3:
    def func_name(f):
        return f.__name__
else: # pragma: no cover
    def func_name(f):
        return f.func_name

# string
if _PY3:
    string_isidentifier = str.isidentifier
else: # pragma: no cover
    import re as _re

    _rePythonIdentifier = _re.compile(r'^[a-zA-Z_]\w*$')

    def string_isidentifier(s):
        return _rePythonIdentifier.search(s) is not None

# html
if _PY3:
    from html import escape as html_escape # pylint: disable=unused-import
    from html.parser import HTMLParser # pylint: disable=unused-import
else: # pragma: no cover
    from cgi import escape as html_escape
    from HTMLParser import HTMLParser # pylint: disable=import-error

# io
if _PY3:
    from io import StringIO # pylint: disable=unused-import
else: # pragma: no cover
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO # pylint: disable=import-error

# urllib
if _PY3:
    from urllib.parse import quote as urllib_parse_quote, unquote as urllib_parse_unquote # pylint: disable=unused-import
else: # pragma: no cover
    from urllib import quote as _urllib_quote, unquote as _urllib_unquote # pylint: disable=no-name-in-module

    def urllib_parse_quote(string, encoding='utf-8'):
        return _urllib_quote(string.encode(encoding))

    def urllib_parse_unquote(string, encoding='utf-8'):
        return _urllib_unquote(string).decode(encoding)
