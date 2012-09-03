#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Struct

import unittest


# Tests for Struct class
class TestStruct(unittest.TestCase):

    def test_struct(self):

        s = Struct()

        self.assertEqual(s.a, None)
        self.assertEqual(s.b, None)

        s.a = 17
        s.b = "hello"
        self.assertEqual(s.a, 17)
        self.assertEqual(s.b, "hello")

        s.c = {
            "d": 19,
            "e": "goodbye",
            "f": {
                "g": 21
                }
            }
        self.assertTrue(isinstance(s.c, Struct))
        self.assertEqual(s.c.d, 19)
        self.assertEqual(s.c.e, "goodbye")
        self.assertTrue(isinstance(s.c.f, Struct))
        self.assertEqual(s.c.f.g, 21)

        s.d = {}
        self.assertTrue(isinstance(s.d, Struct))
        self.assertEqual(s.d.a, None)
        self.assertEqual(s.d.b, None)

    def test_set_struct(self):

        s = Struct()
        s.a = 17
        s.b = {}
        s.b.c = "foo"

        s2 = Struct(s)
        self.assertEqual(s.a, 17)
        self.assertEqual(s.b.c, "foo")
        self.assertEqual(s2.a, 17)
        self.assertEqual(s2.b.c, "foo")

    def test_dict(self):

        s = Struct()
        s.a = 17
        s.b = 19
        self.assertEqual(s(), { "a": 17, "b": 19 })

    def test_cmp(self):

        s1 = { "a": 17, "b": 19, "c": { "d": 20 } }
        s2 = Struct()
        s2.a = 17
        s2.b = 19
        s2.c = {}
        s2.c.d = 20

        self.assertTrue(s1 == s2)
        self.assertTrue(s2 == s1)
        self.assertTrue(isinstance(s1["c"], dict))

        s2.b = 20
        self.assertFalse(s1 == s2)
        self.assertFalse(s2 == s1)

    def test_dict_access(self):

        s = Struct()
        s.a = 17
        s.b = 19

        self.assertEqual(s["a"], 17)
        self.assertEqual(s["b"], 19)
        self.assertEqual(s["c"], None)

        s["b"] = 20
        self.assertEqual(s["b"], 20)

        self.assertTrue("a" in s)
        self.assertTrue("b" in s)
        self.assertFalse("c" in s)

    def test_iter(self):

        s = Struct()
        s.a = 17
        s.b = 19

        m = [ k for k in s ]

        self.assertEqual(len(m), 2)
        self.assertTrue("a" in m)
        self.assertTrue("b" in m)

    def test_none(self):

        s = Struct()
        s.a = 17
        s.b = 19

        self.assertEqual(s.a, 17)
        self.assertEqual(s.b, 19)
        self.assertEqual(len(s), 2)
        self.assertTrue("a" in s)
        self.assertTrue("a" in s())
        self.assertTrue("b" in s)
        self.assertTrue("b" in s())

        s.a = None
        self.assertEqual(s.a, None)
        self.assertEqual(s.b, 19)
        self.assertEqual(len(s), 1)
        self.assertFalse("a" in s)
        self.assertFalse("a" in s())
        self.assertTrue("b" in s)
        self.assertTrue("b" in s())

        s["b"] = None
        self.assertEqual(s.a, None)
        self.assertEqual(s.b, None)
        self.assertEqual(len(s), 0)
        self.assertFalse("a" in s)
        self.assertFalse("a" in s())
        self.assertFalse("b" in s)
        self.assertFalse("b" in s())
