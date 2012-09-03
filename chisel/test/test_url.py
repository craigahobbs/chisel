#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import decodeQueryString, encodeQueryString, Struct

import unittest


# Tests for URL utilities
class TestStruct(unittest.TestCase):

    def test_simple(self):

        s = { "a": 7, "_a": "7", "b": { "c": "+x y + z", "d": [ 2, -4, 6 ] } }
        queryString = encodeQueryString(s)
        self.assertEqual(queryString, encodeQueryString(Struct(dict(s))))
        self.assertEqual(queryString, "_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6")
        s2 = decodeQueryString(queryString)
        self.assertEqual(s2, { "a": "7", "_a": "7", "b": { "c": "+x y + z", "d": [ "2", "-4", "6" ] } })

    def test_array(self):

        a = [1, 2, 3]
        queryString = encodeQueryString(a)
        self.assertEqual(queryString, "0=1&1=2&2=3")
        a2 = decodeQueryString(queryString)
        self.assertEqual(a2, ['1', '2', '3'])
