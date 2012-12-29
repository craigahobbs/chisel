#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import decodeQueryString, encodeQueryString, Struct

import unittest


# Tests for URL utilities
class TestUrl(unittest.TestCase):

    def test_url_decodeQueryString(self):

        # Complex dict
        s = "_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6"
        o = { "a": "7", "_a": "7", "b": { "c": "+x y + z", "d": ["2", "-4", "6"] } }
        self.assertEqual(decodeQueryString(s), o)

        # Array of dicts
        s = "foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear"
        o = { "foo": [{ "bar": "17", "thud": "blue" }, { "boo": "bear" }] }
        self.assertEqual(decodeQueryString(s), o)

        # Top-level array
        s = "0=1&1=2&2=3"
        o = ["1", "2", "3"]
        self.assertEqual(decodeQueryString(s), o)

        # Empty query string
        s = ""
        o = {}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value
        s = "b="
        o = { "b": "" }
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value at end
        s = "a=7&b="
        o = { "a": "7", "b": "" }
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value at start
        s = "b=&a=7"
        o = { "a": "7", "b": "" }
        self.assertEqual(decodeQueryString(s), o)

        # Empty string value in middle
        s = "a=7&b=&c=9"
        o = { "a": "7", "b": "", "c": "9" }
        self.assertEqual(decodeQueryString(s), o)

        # Decode keys and values
        s = "a%2eb.c=7%20+%207%20%3d%2014"
        o = { "a.b": { "c": "7 + 7 = 14" } }
        self.assertEqual(decodeQueryString(s), o)

        # Decode unicode string
        s = "a=abc%EA%80%80&b.0=c&b.1=d"
        o = { u"a": u"abc" + unichr(40960), u"b": [u"c", "d"] }
        self.assertEqual(decodeQueryString(s), o)

        # Keys and values with special characters
        s = "a%26b%3Dc%2ed=a%26b%3Dc.d"
        o = { "a&b=c.d": "a&b=c.d" }
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
        s = "a=7&b"
        assertDecodeError(s, "Invalid key/value pair 'b'")

        # Empty string key
        s = "a=7&=b"
        o = { "a": "7", "": "b" }
        self.assertEqual(decodeQueryString(s), o)

        # Empty string key and value
        s = "a=7&="
        o = { "a": "7", "": "" }
        self.assertEqual(decodeQueryString(s), o)

        # Empty string key and value with space
        s = "a=7& = "
        o = { "a": "7", " ": " " }
        self.assertEqual(decodeQueryString(s), o)

        # Empty string key with no equal
        s = "a=7&"
        o = { "a": "7" }
        self.assertEqual(decodeQueryString(s), o)

        # Multiple empty string key with no equal
        s = "a&b"
        assertDecodeError(s, "Invalid key/value pair 'a'")

        # Multiple empty string key with no equal
        s = "a&b&c"
        assertDecodeError(s, "Invalid key/value pair 'a'")

        # Multiple empty string key/value
        s = "&"
        o = {}
        self.assertEqual(decodeQueryString(s), o)

        # Multiple empty string key/value
        s = "&&"
        o = {}
        self.assertEqual(decodeQueryString(s), o)

        # Empty string sub-key
        s = "a.=5"
        o = { "a": { "": "5" } }
        self.assertEqual(decodeQueryString(s), o)

        # Duplicate keys
        s = "abc=21&ab=19&abc=17"
        o = { "abc": "17", "ab": "19" }
        self.assertEqual(decodeQueryString(s), o)

        # Duplicate keys - reverse value order - should be stable
        s = "abc=17&ab=19&abc=21"
        o = { "abc": "21", "ab": "19" }
        self.assertEqual(decodeQueryString(s), o)

        # Duplicate index
        s = "a.0=0&a.1=1&a.0=2"
        o = { "a": ["2", "1"] }
        self.assertEqual(decodeQueryString(s), o)

        # Index too large
        s = "a.0=0&a.1=1&a.3=3"
        assertDecodeError(s, "Invalid key/value pair 'a.3=3'")

        # Initial index too large
        s = "a.1=0"
        assertDecodeError(s, "Invalid key/value pair 'a.1=0'")

        # Negative index
        s = "a.0=0&a.1=1&a.-3=3"
        assertDecodeError(s, "Invalid key/value pair 'a.-3=3'")

        # First dict, then list
        s = "a.b=0&a.0=0"
        assertDecodeError(s, "Invalid key/value pair 'a.0=0'")

        # First list, then dict
        s = "a.0=0&a.b=0"
        assertDecodeError(s, "Invalid key/value pair 'a.b=0'")

    def test_url_encodeQueryString(self):

        # Complex dict
        o = { "a": 7, "_a": "7", "b": { "c": "+x y + z", "d": [2, -4, 6] } }
        s = "_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6"
        self.assertEqual(encodeQueryString(o), s)

        # Complex Struct
        o = Struct(a = 7, _a = "7", b = Struct(c = "+x y + z", d = [2, -4, 6]))
        s = "_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6"
        self.assertEqual(encodeQueryString(o), s)

        # List of dicts
        o = { "foo": [{ "bar": "17", "thud": "blue" }, { "boo": "bear" }] }
        s = "foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear"
        self.assertEqual(encodeQueryString(o), s)

        # Top-level array
        o = [1, 2, 3]
        s = "0=1&1=2&2=3"
        self.assertEqual(encodeQueryString(o), s)

        # Empty dict
        o = {}
        s = ""
        self.assertEqual(encodeQueryString(o), s)

        # Empty array (won't round trip)
        o = []
        s = ""
        self.assertEqual(encodeQueryString(o), s)

        # Keys and values with special characters
        o = { "a&b=c.d": "a&b=c.d" }
        s = "a%26b%3Dc.d=a%26b%3Dc.d"
        self.assertEqual(encodeQueryString(o), s)

        # Unicode keys and values
        o = { u"a": u"abc" + unichr(40960), u"b": [u"c", "d"] }
        s = "a=abc%EA%80%80&b.0=c&b.1=d"
        self.assertEqual(encodeQueryString(o), s)
