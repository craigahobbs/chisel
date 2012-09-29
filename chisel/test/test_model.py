#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Struct, ValidationError
from chisel.model import jsonDefault, TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool, TypeDatetime

from datetime import datetime, timedelta, tzinfo
import re
import unittest


# Model validation tests
class TestStructValidation(unittest.TestCase):

    def test_struct(self):

        # Build a type model
        m = TypeStruct()
        m.members.append(TypeStruct.Member("a", TypeInt()))
        m.members.append(TypeStruct.Member("b", TypeString()))
        mc = TypeStruct()
        mc.members.append(TypeStruct.Member("d", TypeBool()))
        mc.members.append(TypeStruct.Member("e", TypeFloat()))
        m.members.append(TypeStruct.Member("c", mc))
        m.members.append(TypeStruct.Member("f", TypeArray(TypeString())))
        m.members.append(TypeStruct.Member("g", TypeDict(TypeInt()), isOptional = True))
        me = TypeEnum()
        me.values.append(TypeEnum.Value("Foo"))
        me.values.append(TypeEnum.Value("Bar"))
        m.members.append(TypeStruct.Member("h", me, isOptional = True))
        m.members.append(TypeStruct.Member("i", TypeDatetime(), isOptional = True))

        # Validate success
        s = m.validate({ "a": 5,
                         "b": "Hello",
                         "c": Struct({ "d": True, "e": 5.5 }),
                         "f": [ "Foo", "Bar" ],
                         "g": { "Foo": 5 },
                         "h": "Foo",
                         "i": "2012-09-06T06:49:00-07:00"
                         })
        self.assertTrue(isinstance(s, dict))
        self.assertTrue(isinstance(s["a"], int))
        self.assertEqual(s["a"], 5)
        self.assertTrue(isinstance(s["b"], basestring))
        self.assertEqual(s["b"], "Hello")
        self.assertTrue(isinstance(s["c"], Struct))
        self.assertTrue(isinstance(s["c"].d, bool))
        self.assertEqual(s["c"].d, True)
        self.assertTrue(isinstance(s["c"].e, float))
        self.assertEqual(s["c"].e, 5.5)
        self.assertTrue(isinstance(s["f"], list))
        self.assertTrue(isinstance(s["f"][0], basestring))
        self.assertEqual(s["f"][0], "Foo")
        self.assertTrue(isinstance(s["f"][1], basestring))
        self.assertEqual(s["f"][1], "Bar")
        self.assertEqual(s["g"]["Foo"], 5)
        self.assertEqual(s["h"], "Foo")
        self.assertTrue(isinstance(s["i"], datetime))
        self.assertEqual(s["i"].year, 2012)
        self.assertEqual(s["i"].month, 9)
        self.assertEqual(s["i"].day, 6)
        self.assertEqual(s["i"].hour, 13)
        self.assertEqual(s["i"].minute, 49)
        self.assertEqual(s["i"].second, 0)
        self.assertEqual(s["i"].microsecond, 0)
        self.assertEqual(s["i"].tzinfo.utcoffset(s["i"]), timedelta(0))
        self.assertEqual(s["i"].tzinfo.dst(s["i"]), timedelta(0))

        # Validate success - accept strings
        s = m.validate(Struct({ "a": "5",
                                "b": "Hello",
                                "c": { "d": "true", "e": "5.5" },
                                "f": [ "Foo", "Bar" ]
                                }), acceptString = True)
        self.assertTrue(isinstance(s, Struct))
        self.assertTrue(isinstance(s.a, int))
        self.assertEqual(s.a, 5)
        self.assertTrue(isinstance(s.b, basestring))
        self.assertEqual(s.b, "Hello")
        self.assertTrue(isinstance(s.c, Struct))
        self.assertTrue(isinstance(s.c.d, bool))
        self.assertEqual(s.c.d, True)
        self.assertTrue(isinstance(s.c.e, float))
        self.assertEqual(s.c.e, 5.5)
        self.assertTrue(isinstance(s.f, list))
        self.assertTrue(isinstance(s.f[0], basestring))
        self.assertEqual(s.f[0], "Foo")
        self.assertTrue(isinstance(s.f[1], basestring))
        self.assertEqual(s.f[1], "Bar")

        # Validate failure - missing member
        try:
            s = m.validate({ "a": 5,
                             "c": { "d": True, "e": 5.5 },
                             "f": [ "Foo", "Bar" ]
                             })
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Required member 'b' missing")

        # Validate failure - invalid member
        try:
            s = m.validate(Struct({ "a": 5,
                                    "b": "Hello",
                                    "c": { "d": True, "e": 5.5, "bad": "bad value" },
                                    "f": [ "Foo", "Bar" ],
                                    }))
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Invalid member 'c.bad'")

        # Validate failure - invalid int member type
        try:
            s = m.validate({ "a": "5",
                             "b": "Hello",
                             "c": { "d": True, "e": 5.5 },
                             "f": [ "Foo", "Bar" ]
                             })
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Invalid value '5' (type 'str') for member 'a', expected type 'int'")

        # Validate failure - invalid array member type
        try:
            s = m.validate({ "a": 5,
                             "b": "Hello",
                             "c": { "d": True, "e": 5.5 },
                             "f": [ 5, "Bar" ]
                             })
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Invalid value 5 (type 'int') for member 'f.0', expected type 'string'")

        # Validate failure - invalid dict member key
        try:
            s = m.validate({ "a": 5,
                             "b": "Hello",
                             "c": { "d": True, "e": 5.5 },
                             "f": [ "Foo", "Bar" ],
                             "g": { 5: 5 }
                             })
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Invalid value 5 (type 'int') for member 'g.5', expected type 'string'")

        # Validate failure - invalid dict member value
        try:
            s = m.validate({ "a": 5,
                             "b": "Hello",
                             "c": { "d": True, "e": 5.5 },
                             "f": [ "Foo", "Bar" ],
                             "g": Struct({ "Foo": "Bar" })
                             })
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Invalid value 'Bar' (type 'str') for member 'g.Foo', expected type 'int'")

        # Validate failure - invalid enum value
        try:
            s = m.validate({ "a": 5,
                             "b": "Hello",
                             "c": { "d": True, "e": 5.5 },
                             "f": [ "Foo", "Bar" ],
                             "h": "Bonk"
                             })
            self.assertTrue(False)
        except ValidationError, e:
            self.assertEqual(str(e), "Invalid value 'Bonk' (type 'str') for member 'h', expected type 'enum'")

    def test_int_constraint(self):

        t = TypeInt()
        t.constraint_lt = 5
        self.assertEqual(t.validate(4), 4)
        self.assertEqual(t.validate(0), 0)
        self.assertEqual(t.validate(-4), -4)
        with self.assertRaises(ValidationError):
            t.validate(5)
        with self.assertRaises(ValidationError):
            t.validate(50)

        t = TypeInt()
        t.constraint_lte = 5
        self.assertEqual(t.validate(5), 5)
        self.assertEqual(t.validate(0), 0)
        self.assertEqual(t.validate(-4), -4)
        with self.assertRaises(ValidationError):
            t.validate(6)
        with self.assertRaises(ValidationError):
            t.validate(60)

        t = TypeInt()
        t.constraint_gt = 5
        self.assertEqual(t.validate(6), 6)
        self.assertEqual(t.validate(60), 60)
        with self.assertRaises(ValidationError):
            t.validate(5)
        with self.assertRaises(ValidationError):
            t.validate(0)
        with self.assertRaises(ValidationError):
            t.validate(-5)

        t = TypeInt()
        t.constraint_gte = 5
        self.assertEqual(t.validate(5), 5)
        self.assertEqual(t.validate(50), 50)
        with self.assertRaises(ValidationError):
            t.validate(4)
        with self.assertRaises(ValidationError):
            t.validate(0)
        with self.assertRaises(ValidationError):
            t.validate(-5)

        t = TypeInt()
        t.constraint_gte = 5
        t.constraint_lte = 10
        self.assertEqual(t.validate(5), 5)
        self.assertEqual(t.validate(8), 8)
        self.assertEqual(t.validate(10), 10)
        with self.assertRaises(ValidationError):
            t.validate(4)
        with self.assertRaises(ValidationError):
            t.validate(11)

        t = TypeInt()
        t.constraint_gt = 4.5
        t.constraint_lt = 10.5
        self.assertEqual(t.validate(5), 5)
        self.assertEqual(t.validate(8), 8)
        self.assertEqual(t.validate(10), 10)
        with self.assertRaises(ValidationError):
            t.validate(4)
        with self.assertRaises(ValidationError):
            t.validate(11)

    def test_float_constraint(self):

        t = TypeFloat()
        t.constraint_lt = 5.5
        self.assertEqual(t.validate(5.4), 5.4)
        self.assertEqual(t.validate(0), 0)
        self.assertEqual(t.validate(-4), -4)
        with self.assertRaises(ValidationError):
            t.validate(5.5)
        with self.assertRaises(ValidationError):
            t.validate(50)

        t = TypeFloat()
        t.constraint_lte = 5.5
        self.assertEqual(t.validate(5.5), 5.5)
        self.assertEqual(t.validate(0), 0)
        self.assertEqual(t.validate(-4), -4)
        with self.assertRaises(ValidationError):
            t.validate(5.6)
        with self.assertRaises(ValidationError):
            t.validate(60)

        t = TypeFloat()
        t.constraint_gt = 5.5
        self.assertEqual(t.validate(5.6), 5.6)
        self.assertEqual(t.validate(60), 60)
        with self.assertRaises(ValidationError):
            t.validate(5.5)
        with self.assertRaises(ValidationError):
            t.validate(0)
        with self.assertRaises(ValidationError):
            t.validate(-5)

        t = TypeFloat()
        t.constraint_gte = 5.5
        self.assertEqual(t.validate(5.5), 5.5)
        self.assertEqual(t.validate(50), 50)
        with self.assertRaises(ValidationError):
            t.validate(5.4)
        with self.assertRaises(ValidationError):
            t.validate(0)
        with self.assertRaises(ValidationError):
            t.validate(-5)

        t = TypeFloat()
        t.constraint_gte = 4.5
        t.constraint_lte = 10.5
        self.assertEqual(t.validate(4.5), 4.5)
        self.assertEqual(t.validate(8), 8)
        self.assertEqual(t.validate(10.5), 10.5)
        with self.assertRaises(ValidationError):
            t.validate(4.4)
        with self.assertRaises(ValidationError):
            t.validate(10.6)

    def test_string_constraint(self):

        t = TypeString()
        t.constraint_len_lt = 5
        self.assertEqual(t.validate("abcd"), "abcd")
        self.assertEqual(t.validate("abc"), "abc")
        self.assertEqual(t.validate(""), "")
        with self.assertRaises(ValidationError):
            t.validate("abcde")

        t = TypeString()
        t.constraint_len_lte = 5
        self.assertEqual(t.validate("abcde"), "abcde")
        self.assertEqual(t.validate("abcd"), "abcd")
        self.assertEqual(t.validate(""), "")
        with self.assertRaises(ValidationError):
            t.validate("abcdef")

        t = TypeString()
        t.constraint_len_gt = 5
        self.assertEqual(t.validate("abcdef"), "abcdef")
        self.assertEqual(t.validate("abcdefg"), "abcdefg")
        with self.assertRaises(ValidationError):
            t.validate("abcde")
        with self.assertRaises(ValidationError):
            t.validate("")

        t = TypeString()
        t.constraint_len_gte = 5
        self.assertEqual(t.validate("abcde"), "abcde")
        self.assertEqual(t.validate("abcdef"), "abcdef")
        with self.assertRaises(ValidationError):
            t.validate("abcd")
        with self.assertRaises(ValidationError):
            t.validate("")

        t = TypeString()
        t.constraint_len_gte = 5
        t.constraint_len_lte = 8
        self.assertEqual(t.validate("abcde"), "abcde")
        self.assertEqual(t.validate("abcdef"), "abcdef")
        self.assertEqual(t.validate("abcdefgh"), "abcdefgh")
        self.assertEqual(t.validate("abcdefg"), "abcdefg")
        with self.assertRaises(ValidationError):
            t.validate("abcd")
        with self.assertRaises(ValidationError):
            t.validate("abcdefghi")

        t = TypeString()
        t.constraint_regex = re.compile("^[A-Za-z]\w+$")
        self.assertEqual(t.validate("abcde"), "abcde")
        self.assertEqual(t.validate("abc1_2"), "abc1_2")
        with self.assertRaises(ValidationError):
            t.validate(" abc1_2")
        with self.assertRaises(ValidationError):
            t.validate("99")

        t = TypeString()
        t.constraint_regex = re.compile("abc")
        self.assertEqual(t.validate("abcde"), "abcde")
        self.assertEqual(t.validate("__abcde__"), "__abcde__")
        with self.assertRaises(ValidationError):
            t.validate(" ab_c1_2")
        with self.assertRaises(ValidationError):
            t.validate("99")

    def test_datetime(self):

        t = TypeDatetime()

        v = t.validate("2012-09-06T07:05:00Z")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T07:05:00+00:00")

        v = t.validate("2012-09-06")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T00:00:00+00:00")

        v = t.validate("2012-09-06T07:05:00-07:00")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T14:05:00+00:00")

        v = t.validate("2012-09-06T07:05:00.5-07:00")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T14:05:00.500000+00:00")

        v = t.validate("2012-09-06T07:05:00,5-07:00")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T14:05:00.500000+00:00")

        v = t.validate(datetime(2012, 9, 6, 7, 5, 0, 0, TypeDatetime.TZUTC()))
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T07:05:00+00:00")

        v = t.validate(datetime(2012, 9, 6, 7, 5, 0, 0, TypeDatetime.TZLocal()))
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZLocal))
        self.assertTrue(v.isoformat().startswith("2012-09-06T07:05:00"))
        v2 = t.validate(jsonDefault(v))
        self.assertTrue(isinstance(v2, datetime))
        self.assertTrue(isinstance(v2.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(v, v2)

        v = t.validate(datetime(2012, 9, 6, 7, 5))
        self.assertTrue(isinstance(v, datetime))
        self.assertEqual(v.tzinfo, None)
        self.assertTrue(jsonDefault(v).startswith("2012-09-06T07:05:00"))
        v2 = t.validate(jsonDefault(v))
        self.assertTrue(isinstance(v2, datetime))
        self.assertTrue(isinstance(v2.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(datetime(2012, 9, 6, 7, 5, tzinfo = TypeDatetime.TZLocal()), v2)

        with self.assertRaises(ValidationError):
            t.validate(17)

        with self.assertRaises(ValueError):
            t.validate("2012-09-06T07:05:00")

        with self.assertRaises(ValueError):
            t.validate("12-09-06T07:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("0000-09-06T07:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-00-06T07:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-13-06T07:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-12-00T07:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-12-32T07:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-12-30T24:05:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-12-30T23:60:00Z")

        with self.assertRaises(ValueError):
            t.validate("2012-12-30T23:59:60Z")
