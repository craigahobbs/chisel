#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Struct

import unittest


# Tests for Struct class
class TestStruct(unittest.TestCase):

    # Test basic Struct functionality
    def test_struct_basic(self):

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

    # Test key/value pair initialization
    def test_struct_set_struct(self):

        s = Struct(a = 17,
                   b = Struct(c = "foo"),
                   c = { "c": "bar" },
                   d = [1,2,3],
                   e = (1,2,3))

        self.assertEqual(s.a, 17)
        self.assertTrue(isinstance(s.b, Struct))
        self.assertTrue(isinstance(s.b(), dict))
        self.assertEqual(s.b.c, "foo")
        self.assertTrue(isinstance(s.c, Struct))
        self.assertTrue(isinstance(s.c(), dict))
        self.assertEqual(s.c.c, "bar")
        self.assertTrue(isinstance(s.d, Struct))
        self.assertTrue(isinstance(s.d(), list))
        self.assertEqual(len(s.d), 3)
        self.assertEqual(s.d, [1,2,3])
        self.assertTrue(isinstance(s.e, Struct))
        self.assertTrue(isinstance(s.e(), tuple))
        self.assertEqual(len(s.e), 3)
        self.assertEqual(s.e, (1,2,3))

    # Test callable behavior - gets the wrapped container
    def test_struct_dict(self):

        s = Struct(a = 17, b = 19, c = { "a": 14 })
        self.assertTrue(isinstance(s(), dict))
        self.assertEqual(s(), { "a": 17, "b": 19, "c": { "a": 14 } })
        self.assertTrue(isinstance(s.c, Struct))
        self.assertTrue(isinstance(s()["c"], dict))

    # Test container comparison
    def test_struct_cmp(self):

        s1 = { "a": 17, "b": 19, "c": { "d": 20 },  "d": [1,2,3], "e": (1,2,3) }
        s2 = Struct(**s1)

        self.assertTrue(s1 == s2)
        self.assertTrue(s2 == s1)
        self.assertTrue(s2, Struct(**s1))

        s2.b = 20
        self.assertFalse(s1 == s2)
        self.assertFalse(s2 == s1)
        self.assertTrue(s2, Struct(**s1))

        self.assertTrue(s2.d, [1,2,3])
        self.assertTrue([1,2,3], s2.d)
        self.assertTrue(s2.d, Struct(a = [1,2,3]).a)

        self.assertTrue(s2.e, (1,2,3))
        self.assertTrue((1,2,3), s2.e)
        self.assertTrue(s2.e, Struct(a = (1,2,3)).a)

    # Test indexed-container syntax access
    def test_struct_index_access(self):

        s = Struct(a = 17, b = 19, c = [1,2,3], d = (1,2,3))

        self.assertEqual(s["a"], 17)
        self.assertEqual(s["b"], 19)
        self.assertEqual(s["c"], [1,2,3])
        self.assertEqual(s["c"][0], 1)
        self.assertEqual(s["c"][1], 2)
        self.assertEqual(s["c"][2], 3)
        self.assertEqual(s["c"][3], None)
        self.assertEqual(s["c"][-1], None)
        self.assertEqual(s["d"], (1,2,3))
        self.assertEqual(s["d"][0], 1)
        self.assertEqual(s["d"][1], 2)
        self.assertEqual(s["d"][2], 3)
        self.assertEqual(s["d"][3], None)
        self.assertEqual(s["d"][-1], None)
        self.assertEqual(s["e"], None)

        s["b"] = 20
        self.assertEqual(s["b"], 20)

        s["c"][1] = 20
        self.assertEqual(s["c"][1], 20)

        try:
            s["d"][1] = 20
            self.fail()
        except TypeError:
            pass
        except:
            self.fail()

    # Test "contained" behavior
    def test_struct_contains(self):

        s = Struct(a = 17, b = Struct(a = "foo", b = "bar"), c = [1,2,3], d = (1,2,3))
        self.assertTrue("a" in s)
        self.assertTrue("b" in s)
        self.assertTrue("a" in s.b)
        self.assertTrue("b" in s.b)
        self.assertFalse("c" in s.b)
        self.assertTrue(1 in s.c)
        self.assertFalse(4 in s.c)
        self.assertTrue("d" in s)
        self.assertTrue(1 in s.d)
        self.assertFalse(4 in s.d)
        self.assertFalse("e" in s)

    # Test iterator behavior
    def test_struct_iter(self):

        s = Struct(a = 17, b = 19, c = [{ "a": 1 }, {"b": 2}], d = [1,2,3], e = (1,2,3))

        m = [ k for k in s ]
        self.assertEqual(len(m), 5)
        self.assertTrue("a" in m)
        self.assertTrue("b" in m)
        self.assertTrue("c" in m)
        self.assertTrue("d" in m)
        self.assertTrue("e" in m)

        mc = [v for v in s.c]
        self.assertEqual(mc, [{"a": 1}, {"b": 2}])

        md = [v for v in s.d]
        self.assertEqual(md, [1,2,3])

        me = [v for v in s.e]
        self.assertEqual(me, [1,2,3])

    # Test that set to None does del
    def test_struct_none(self):

        s = Struct(a = 17, b = 19, c = [1,2,3], d = (1,2,3))

        self.assertEqual(s.a, 17)
        s.a = None
        self.assertEqual(s.a, None)
        self.assertFalse("a" in s)

        self.assertEqual(s.b, 19)
        s["b"] = None
        self.assertEqual(s.b, None)
        self.assertFalse("b" in s)

        self.assertEqual(len(s.c), 3)
        self.assertEqual(s.c[1], 2)
        s.c[1] = None
        self.assertEqual(len(s.c), 2)
        self.assertEqual(s.c[1], 3)

        try:
            s.d[1] = None
            self.fail()
        except TypeError:
            pass
        except:
            self.fail()

    # Test non-dict attribute get/set
    def test_struct_non_dict_container_attr(self):

        s = Struct(a = [1, 2, 3])

        # Test list attribute get
        self.assertEqual(s.a.count(2), 1)
        s.a.append(2)
        self.assertEqual(s.a.count(2), 2)

        # Test list attribute set (not likely to ever occur)
        try:
            s.a.foo = 19
            self.fail()
        except Exception as e:
            self.assertEqual(str(e), "'list' object has no attribute 'foo'")
