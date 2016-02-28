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

# pylint: disable=ungrouped-imports
# pylint: disable=unused-import
# pylint: disable=wrong-import-order
# pylint: disable=wrong-import-position

import sys

PY3 = (sys.version_info >= (3, 0))
PY3_3 = (sys.version_info >= (3, 3))

# types
if PY3:
    basestring_ = str                   # pylint: disable=invalid-name
    long_ = int                         # pylint: disable=invalid-name
    unichr_ = chr                       # pylint: disable=invalid-name
    unicode_ = str                      # pylint: disable=invalid-name
    xrange_ = range                     # pylint: disable=invalid-name
else: # pragma: no cover
    basestring_ = basestring            # pylint: disable=invalid-name, undefined-variable
    long_ = long                        # pylint: disable=invalid-name, undefined-variable
    unichr_ = unichr                    # pylint: disable=invalid-name, undefined-variable
    unicode_ = unicode                  # pylint: disable=invalid-name, undefined-variable
    xrange_ = xrange                    # pylint: disable=invalid-name, undefined-variable

# dict
if PY3:
    def iteritems(dict_):
        return iter(dict_.items())

    def itervalues(dict_):
        return iter(dict_.values())
else: # pragma: no cover
    def iteritems(dict_):
        return dict_.iteritems()

    def itervalues(dict_):
        return dict_.itervalues()

# function
if PY3:
    def func_name(func):
        return func.__name__
else: # pragma: no cover
    def func_name(func):
        return func.func_name

# string
if PY3:
    string_isidentifier = str.isidentifier # pylint: disable=invalid-name
else: # pragma: no cover
    import re as _re

    _REGEX_IDENTIFIER = _re.compile(r'^[a-zA-Z_]\w*$')

    def string_isidentifier(string):
        return _REGEX_IDENTIFIER.search(string) is not None

# html
if PY3:
    from html import escape as html_escape
    from html.parser import HTMLParser
else: # pragma: no cover
    from cgi import escape as html_escape
    from HTMLParser import HTMLParser # pylint: disable=import-error

# io
if PY3:
    from io import StringIO
else: # pragma: no cover
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO # pylint: disable=import-error

# re
if PY3_3:
    from re import escape as re_escape
else: # pragma: no cover
    # Backport of Python 3.5 re.escape - https://bugs.python.org/issue2650

    # --- BACKPORT BEGIN ---

    # Copyright (C) 1995-2001 Corporation for National Research Initiatives; All Rights Reserved

    # Python 1.6.1 is made available subject to the terms and conditions in
    # CNRI's License Agreement. This Agreement together with Python 1.6.1 may be
    # located on the Internet using the following unique, persistent identifier
    # (known as a handle): 1895.22/1013. This Agreement may also be obtained
    # from a proxy server on the Internet using the following URL:
    # http://hdl.handle.net/1895.22/1013.

    _alphanum_str = frozenset( # pylint: disable=invalid-name
        "_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890")
    _alphanum_bytes = frozenset( # pylint: disable=invalid-name
        b"_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890")

    def re_escape(pattern):
        """
        Escape all the characters in pattern except ASCII letters, numbers and '_'.
        """
        if isinstance(pattern, str):
            alphanum = _alphanum_str
            s = list(pattern) # pylint: disable=invalid-name
            for i, c in enumerate(pattern): # pylint: disable=invalid-name
                if c not in alphanum:
                    if c == "\000":
                        s[i] = "\\000"
                    else:
                        s[i] = "\\" + c
            return "".join(s)
        else:
            alphanum = _alphanum_bytes
            s = [] # pylint: disable=invalid-name
            esc = ord(b"\\")
            for c in pattern: # pylint: disable=invalid-name
                if c in alphanum:
                    s.append(c)
                else:
                    if c == 0:
                        s.extend(b"\\000")
                    else:
                        s.append(esc)
                        s.append(c)
            return bytes(s)

    # --- BACKPORT END ---

# urllib
if PY3:
    from urllib.parse import quote as urllib_parse_quote, unquote as urllib_parse_unquote
else: # pragma: no cover
    from urllib import quote as _urllib_quote, unquote as _urllib_unquote # pylint: disable=no-name-in-module

    def urllib_parse_quote(string, encoding='utf-8'):
        return _urllib_quote(string.encode(encoding))

    def urllib_parse_unquote(string, encoding='utf-8'):
        return _urllib_unquote(string).decode(encoding)
