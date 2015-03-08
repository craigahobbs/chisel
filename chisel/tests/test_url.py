#
# Copyright (C) 2012-2014 Craig Hobbs
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

from chisel import decodeQueryString, encodeQueryString, tzutc
from chisel.compat import PY3

from datetime import date, datetime
import unittest
from uuid import UUID


# Tests for URL utilities
class TestUrl(unittest.TestCase):

    def test_url_decodeQueryString(self):

        # Complex dict
        s = '_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6'
        o = {'a': '7', '_a': '7', 'b': {'c': '+x y + z', 'd': ['2', '-4', '6']}}
        self.assertEqual(decodeQueryString(s), o)

        # Array of dicts
        s = 'foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear'
        o = {'foo': [{'bar': '17', 'thud': 'blue'}, {'boo': 'bear'}]}
        self.assertEqual(decodeQueryString(s), o)

        # Top-level array
        s = '0=1&1=2&2=3'
        o = ['1', '2', '3']
        self.assertEqual(decodeQueryString(s), o)

        # Empty query string
        s = ''
        o = {}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value
        s = 'b='
        o = {'b': ''}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value at end
        s = 'a=7&b='
        o = {'a': '7', 'b': ''}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value at start
        s = 'b=&a=7'
        o = {'a': '7', 'b': ''}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value in middle
        s = 'a=7&b=&c=9'
        o = {'a': '7', 'b': '', 'c': '9'}
        self.assertEqual(decodeQueryString(s), o)

        # Decode keys and values
        s = 'a%2eb.c=7%20+%207%20%3d%2014'
        o = {'a.b': {'c': '7 + 7 = 14'}}
        self.assertEqual(decodeQueryString(s), o)

        # Decode unicode string
        unicode_ = str if PY3 else unicode
        unichr_ = chr if PY3 else unichr
        s = 'a=abc%EA%80%80&b.0=c&b.1=d'
        o = {unicode_('a'): unicode_('abc') + unichr_(40960), unicode_('b'): [unicode_('c'), 'd']}
        self.assertEqual(decodeQueryString(s), o)

        # Keys and values with special characters
        s = 'a%26b%3Dc%2ed=a%26b%3Dc.d'
        o = {'a&b=c.d': 'a&b=c.d'}
        self.assertEqual(decodeQueryString(s), o)

        # Non-initial-zero array-looking index
        s = 'a.1=0'
        o = {'a': {'1': '0'}}
        self.assertEqual(decodeQueryString(s), o)

        # Dictionary first, then array-looking zero index
        s = 'a.b=0&a.0=0'
        o = {'a': {'b': '0', '0': '0'}}
        self.assertEqual(decodeQueryString(s), o)

    def test_url_decodeQueryStringDegenerate(self):

        def assertDecodeError(s, err):
            try:
                decodeQueryString(s)
            except ValueError as e:
                self.assertEqual(str(e), err)
            else:
                self.fail()

        # Key with no equal - assume empty string
        s = 'a=7&b'
        assertDecodeError(s, "Invalid key/value pair 'b'")

        # Empty string key
        s = 'a=7&=b'
        o = {'a': '7', '': 'b'}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string key and value
        s = 'a=7&='
        o = {'a': '7', '': ''}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string key and value with space
        s = 'a=7& = '
        o = {'a': '7', ' ': ' '}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string key with no equal
        s = 'a=7&'
        o = {'a': '7'}
        self.assertEqual(decodeQueryString(s), o)

        # Multiple empty string key with no equal
        s = 'a&b'
        assertDecodeError(s, "Invalid key/value pair 'a'")

        # Multiple empty string key with no equal
        s = 'a&b&c'
        assertDecodeError(s, "Invalid key/value pair 'a'")

        # Multiple empty string key/value
        s = '&'
        o = {}
        self.assertEqual(decodeQueryString(s), o)

        # Multiple empty string key/value
        s = '&&'
        o = {}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string sub-key
        s = 'a.=5'
        o = {'a': {'': '5'}}
        self.assertEqual(decodeQueryString(s), o)

        # Duplicate keys
        s = 'abc=21&ab=19&abc=17'
        assertDecodeError(s, "Duplicate key 'abc=17'")

        # Duplicate index
        s = 'a.0=0&a.1=1&a.0=2'
        assertDecodeError(s, "Duplicate key 'a.0=2'")

        # Index too large
        s = 'a.0=0&a.1=1&a.3=3'
        assertDecodeError(s, "Invalid key/value pair 'a.3=3'")

        # Negative index
        s = 'a.0=0&a.1=1&a.-3=3'
        assertDecodeError(s, "Invalid key/value pair 'a.-3=3'")

        # First list, then dict
        s = 'a.0=0&a.b=0'
        assertDecodeError(s, "Invalid key/value pair 'a.b=0'")

    def test_url_encodeQueryString(self):

        # Complex dict
        o = {'a': 7, '_a': '7', 'b': {'c': '+x y + z', 'd': [2, -4, 6]}}
        s = '_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6'
        self.assertEqual(encodeQueryString(o), s)

        # List of dicts
        o = {'foo': [{'bar': '17', 'thud': 'blue'}, {'boo': 'bear'}]}
        s = 'foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear'
        self.assertEqual(encodeQueryString(o), s)

        # Top-level array
        o = [1, 2, 3]
        s = '0=1&1=2&2=3'
        self.assertEqual(encodeQueryString(o), s)

        # Empty dict
        o = {}
        s = ''
        self.assertEqual(encodeQueryString(o), s)

        # Empty array
        o = []
        s = ''
        self.assertEqual(encodeQueryString(o), s)

        # Empty dict/dict
        o = {'foo': {}}
        s = 'foo='
        self.assertEqual(encodeQueryString(o), s)

        # Empty dict/array
        o = {'foo': []}
        s = 'foo='
        self.assertEqual(encodeQueryString(o), s)

        # Empty array/array
        o = [[]]
        s = '0='
        self.assertEqual(encodeQueryString(o), s)

        # Empty array/dict
        o = [{}]
        s = '0='
        self.assertEqual(encodeQueryString(o), s)

        # Keys and values with special characters
        o = {'a&b=c.d': 'a&b=c.d'}
        s = 'a%26b%3Dc.d=a%26b%3Dc.d'
        self.assertEqual(encodeQueryString(o), s)

        # Unicode keys and values
        unicode_ = str if PY3 else unicode
        unichr_ = chr if PY3 else unichr
        o = {unicode_('a'): unicode_('abc') + unichr_(40960), unicode_('b'): [unicode_('c'), 'd']}
        s = 'a=abc%EA%80%80&b.0=c&b.1=d'
        self.assertEqual(encodeQueryString(o), s)

    # Test bool query string encoding
    def test_url_encodeQueryString_bool(self):

        o = {'a': True}
        s = 'a=true'
        self.assertEqual(encodeQueryString(o), s)

    # Test date query string encoding
    def test_url_encodeQueryString_date(self):

        o = {'a': date(2013, 7, 18)}
        s = 'a=2013-07-18'
        self.assertEqual(encodeQueryString(o), s)

    # Test datetime query string encoding
    def test_url_encodeQueryString_datetime(self):

        o = {'a': datetime(2013, 7, 18, 12, 31, tzinfo=tzutc)}
        s = 'a=2013-07-18T12%3A31%3A00%2B00%3A00'
        self.assertEqual(encodeQueryString(o), s)

    # Test uuid query string encoding
    def test_url_encodeQueryString_uuid(self):

        o = {'a': UUID('7da81f83-a656-42f1-aeb3-ab207809fb0e')}
        s = 'a=7da81f83-a656-42f1-aeb3-ab207809fb0e'
        self.assertEqual(encodeQueryString(o), s)
