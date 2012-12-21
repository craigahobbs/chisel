#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Struct, ValidationError
from chisel.model import jsonDefault, TypeStruct, TypeArray, TypeDict, TypeEnum, \
    TypeString, TypeInt, TypeFloat, TypeBool, TypeDatetime, TypeUuid

from datetime import datetime, timedelta, tzinfo
from decimal import Decimal
import re
import unittest
from uuid import UUID


# jsonDefault tests
class TestJsonDefault(unittest.TestCase):

    def test_model_jsonDefault(self):

        # Test unwrapping of Struct-wrapped objects
        o = Struct(a = 3, b = 5)
        self.assertTrue(jsonDefault(o) is o())

        # Test formatting of datetime objects with tzinfo
        o = datetime(2012, 11, 16, tzinfo = TypeDatetime.TZUTC())
        self.assertEqual(jsonDefault(o), "2012-11-16T00:00:00+00:00")

        # Test formatting of datetime objects without tzinfo
        o = datetime(2012, 11, 16)
        self.assertTrue(re.search("^2012-11-16T00:00:00[+-]\\d\\d:\\d\\d$", jsonDefault(o)))

        # Test uuid object
        o = UUID("8daeb11e-3c83-11e2-a7aa-20c9d0427a89")
        self.assertEqual(jsonDefault(o), "8daeb11e-3c83-11e2-a7aa-20c9d0427a89")

        # Test unknown class instance
        class MyType:
            pass
        o = MyType()
        self.assertTrue(jsonDefault(o) is o)


# Model validation tests
class TestModelValidation(unittest.TestCase):

    # Helper to assert validation errors
    def assertValidationError(self, m, v, errorStr, acceptString = False):
        try:
            m.validate(v, acceptString = acceptString)
            self.fail()
        except ValidationError as e:
            self.assertEqual(str(e), errorStr)

    # Test successful validation
    def test_model_struct(self):

        # The struct model
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
        m.members.append(TypeStruct.Member("j", TypeArray(m), isOptional = True)) # Recursive struct...
        m.members.append(TypeStruct.Member("k", TypeUuid(), isOptional = True))

        # Success
        s = m.validate({ "a": 5,
                         "b": "Hello",
                         "c": Struct(d = True, e = 5.5),
                         "f": [ "Foo", "Bar" ],
                         "g": Struct(Foo = 5L),
                         "h": "Foo",
                         "i": "2012-09-06T06:49:00-07:00",
                         "k": "8daeb11e-3c83-11e2-a7aa-20c9d0427a89"
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
        self.assertTrue(isinstance(s["k"], UUID))
        self.assertEqual(str(s["k"]), "8daeb11e-3c83-11e2-a7aa-20c9d0427a89")

        # Success - accept strings
        s = m.validate(Struct(a = "5",
                              b = "Hello",
                              c = { "d": "true", "e": "5.5" },
                              f = [ "Foo", "Bar" ]
                              ), acceptString = True)
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
        self.assertTrue(isinstance(s.f, Struct))
        self.assertTrue(isinstance(s.f(), list))
        self.assertTrue(isinstance(s.f[0], basestring))
        self.assertEqual(s.f[0], "Foo")
        self.assertTrue(isinstance(s.f[1], basestring))
        self.assertEqual(s.f[1], "Bar")

        # Failure - invalid type
        self.assertValidationError(m, [1, 2, 3],
                                   "Invalid value [1, 2, 3] (type 'list'), expected type 'struct'")

        # Failure - invalid non-wrapped type
        self.assertValidationError(m, Struct(a = Struct([1, 2, 3])),
                                   "Invalid value [1, 2, 3] (type 'list') for member 'a', expected type 'int'")

        # Failure - invalid type - struct
        self.assertValidationError(m, Struct(a = [1, 2, 3]).a,
                                   "Invalid value [1, 2, 3] (type 'list'), expected type 'struct'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'struct'")

        # Failure - missing member
        self.assertValidationError(m, { "a": 5,
                                        "c": { "d": True, "e": 5.5 },
                                        "f": [ "Foo", "Bar" ]
                                        },
                                   "Required member 'b' missing")

        # Failure - invalid member
        self.assertValidationError(m, { "a": 5,
                                        "b": "Hello",
                                        "c": { "d": True, "e": 5.5, "bad": "bad value" },
                                        "f": [ "Foo", "Bar" ],
                                        },
                                   "Invalid member 'c.bad'")

        # Failure - invalid member type
        self.assertValidationError(m, { "a": "Hello",
                                        "b": "Hello",
                                        "c": { "d": True, "e": 5.5 },
                                        "f": [ "Foo", "Bar" ],
                                        },
                                   "Invalid value 'Hello' (type 'str') for member 'a', expected type 'int'")

        # Failure - invalid nested member type
        self.assertValidationError(m, { "a": 5,
                                        "b": "Hello",
                                        "c": { "d": 1, "e": 5.5 },
                                        "f": [ "Foo", "Bar" ]
                                        },
                                   "Invalid value 1 (type 'int') for member 'c.d', expected type 'bool'")

        # Failure - invalid nested member type
        self.assertValidationError(m, { "a": 5,
                                        "b": "Hello",
                                        "c": { "d": True, "e": 5.5 },
                                        "f": [ "Foo", "Bar" ],
                                        "j": [{ "a": "bad" }]
                                        },
                                   "Invalid value 'bad' (type 'str') for member 'j[0].a', expected type 'int'")

    # array type
    def test_model_array(self):

        # Array models
        mInt = TypeArray(TypeInt())
        mStruct = TypeArray(TypeStruct())
        mStruct.typeInst.members.append(TypeStruct.Member("a", TypeInt()))

        # Success - array of integers
        self.assertEqual(mInt.validate([1, 2, 3]), [1, 2, 3])

        # Success - array of integers - acceptString
        self.assertEqual(mInt.validate([1, "2", 3], acceptString = True), [1, 2, 3])

        # Success - array of struct
        self.assertEqual(mStruct.validate([Struct(a = 1), { "a": 2 }]), [{ "a": 1 }, { "a": 2 }])

        # Success - array of integers - tuple
        self.assertEqual(mInt.validate((1, 2, 3)), (1, 2, 3))

        # Failure - invalid type - string
        self.assertValidationError(mInt, "Hello",
                                   "Invalid value 'Hello' (type 'str'), expected type 'array'")

        # Failure - invalid type - dict
        self.assertValidationError(mInt, {},
                                   "Invalid value {} (type 'dict'), expected type 'array'")

        # Failure - invalid type - struct
        self.assertValidationError(mInt, Struct(),
                                   "Invalid value {} (type 'dict'), expected type 'array'")

        # Failure - None
        self.assertValidationError(mInt, None,
                                   "Invalid value None (type 'NoneType'), expected type 'array'")

        # Failure - Invalid array member
        self.assertValidationError(mInt, [1, "Hello", 3],
                                   "Invalid value 'Hello' (type 'str') for member '[1]', expected type 'int'")

        # Failure - missing struct member
        self.assertValidationError(mStruct, [{ "a": 1 }, {}],
                                   "Required member '[1].a' missing")

        # Failure - invalid struct member
        self.assertValidationError(mStruct, [{ "a": 1 }, { "a": 2, "b": True }],
                                   "Invalid member '[1].b'")

        # Failure - invalid struct member type
        self.assertValidationError(mStruct, [{ "a": True }],
                                   "Invalid value True (type 'bool') for member '[0].a', expected type 'int'")

    # dict type
    def test_model_dict(self):

        # Dictionary model
        mInt = TypeDict(TypeInt())
        mArray = TypeDict(TypeArray(TypeString()))

        # Success - int dict
        self.assertEqual(mInt.validate({ "a": 1, "abc": 17 }), { "a": 1, "abc": 17 })

        # Success - int dict - acceptString
        self.assertEqual(mInt.validate({ "a": "1", "abc": "17" }, acceptString = True), { "a": 1, "abc": 17 })

        # Success - array dict
        self.assertEqual(mArray.validate({ "a": ["foo", "bar"], "abc": [] }), { "a": ["foo", "bar"], "abc": [] })

        # Success - empty int dict
        self.assertEqual(mInt.validate({}), {})

        # Success - empty array dict
        self.assertEqual(mArray.validate({}), {})

        # Success - unicode key
        self.assertEqual(mInt.validate({ unicode("a"): 7 }), { unicode("a"): 7 })

        # Failure - int value
        self.assertValidationError(mInt, 7,
                                   "Invalid value 7 (type 'int'), expected type 'dict'")

        # Failure - None value
        self.assertValidationError(mInt, None,
                                   "Invalid value None (type 'NoneType'), expected type 'dict'")

        # Failure - non-string key
        self.assertValidationError(mInt, { "a": 1, 1: 2 },
                                   "Invalid value 1 (type 'int') for member '[1]', expected type 'string'")

        # Failure - invalid value type
        self.assertValidationError(mInt, { "a": "bad" },
                                   "Invalid value 'bad' (type 'str') for member 'a', expected type 'int'")

        # Failure - invalid contained value type
        self.assertValidationError(mArray, { "a": ["a", 2, "c"] },
                                   "Invalid value 2 (type 'int') for member 'a[1]', expected type 'string'")

    # enum type
    def test_model_enum(self):

        # Enum model
        m = TypeEnum(typeName = "FooBar")
        m.values.append(TypeEnum.Value("Foo"))
        m.values.append(TypeEnum.Value("Bar"))

        # Success
        v = m.validate("Foo")
        self.assertEqual(v, "Foo")
        self.assertTrue(isinstance(v, str))
        v = m.validate("Bar")
        self.assertEqual(v, "Bar")
        self.assertTrue(isinstance(v, str))

        # Success - unicode
        v = m.validate(unicode("Foo"))
        self.assertEqual(v, unicode("Foo"))
        self.assertTrue(isinstance(v, unicode))

        # Failure
        self.assertValidationError(m, "Thud",
                                   "Invalid value 'Thud' (type 'str'), expected type 'FooBar'")

        # Failure - empty string
        self.assertValidationError(m, "",
                                   "Invalid value '' (type 'str'), expected type 'FooBar'")

        # Failure - non-string
        self.assertValidationError(m, 7,
                                   "Invalid value 7 (type 'int'), expected type 'FooBar'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'FooBar'")

    # string type
    def test_model_string(self):

        # String model
        m = TypeString()

        # Success
        v = m.validate("Foo")
        self.assertEqual(v, "Foo")
        self.assertTrue(isinstance(v, str))

        # Success - unicode
        v = m.validate(unicode("Foo"))
        self.assertEqual(v, "Foo")
        self.assertTrue(isinstance(v, unicode))

        # Failure - int
        self.assertValidationError(m, 7,
                                   "Invalid value 7 (type 'int'), expected type 'string'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'string'")

    # string type constraints
    def test_model_string_constraint(self):

        # Length less-than
        m = TypeString()
        m.constraint_len_lt = 5
        self.assertEqual(m.validate("abcd"), "abcd")
        self.assertEqual(m.validate("abc"), "abc")
        self.assertEqual(m.validate(""), "")
        self.assertValidationError(m, "abcde",
                                   "Invalid value 'abcde' (type 'str'), expected type 'string'")

        # Length less-than or equal-to
        m = TypeString()
        m.constraint_len_lte = 5
        self.assertEqual(m.validate("abcde"), "abcde")
        self.assertEqual(m.validate("abcd"), "abcd")
        self.assertEqual(m.validate(""), "")
        self.assertValidationError(m, "abcdef",
                                   "Invalid value 'abcdef' (type 'str'), expected type 'string'")

        # Length greater-than
        m = TypeString()
        m.constraint_len_gt = 5
        self.assertEqual(m.validate("abcdef"), "abcdef")
        self.assertEqual(m.validate("abcdefg"), "abcdefg")
        self.assertValidationError(m, "abcde",
                                   "Invalid value 'abcde' (type 'str'), expected type 'string'")
        self.assertValidationError(m, "",
                                   "Invalid value '' (type 'str'), expected type 'string'")

        # Length greater-than or equal-to
        m = TypeString()
        m.constraint_len_gte = 5
        self.assertEqual(m.validate("abcde"), "abcde")
        self.assertEqual(m.validate("abcdef"), "abcdef")
        self.assertValidationError(m, "abcd",
                                   "Invalid value 'abcd' (type 'str'), expected type 'string'")
        self.assertValidationError(m, "",
                                   "Invalid value '' (type 'str'), expected type 'string'")

        # Length >= and length <=
        m = TypeString()
        m.constraint_len_gte = 5
        m.constraint_len_lte = 8
        self.assertEqual(m.validate("abcde"), "abcde")
        self.assertEqual(m.validate("abcdef"), "abcdef")
        self.assertEqual(m.validate("abcdefgh"), "abcdefgh")
        self.assertEqual(m.validate("abcdefg"), "abcdefg")
        self.assertValidationError(m, "abcd",
                                   "Invalid value 'abcd' (type 'str'), expected type 'string'")
        self.assertValidationError(m, "abcdefghi",
                                   "Invalid value 'abcdefghi' (type 'str'), expected type 'string'")

        # Length > and length <
        m = TypeString()
        m.constraint_len_gt = 5
        m.constraint_len_lt = 8
        self.assertEqual(m.validate("abcdef"), "abcdef")
        self.assertEqual(m.validate("abcdefg"), "abcdefg")
        self.assertValidationError(m, "abcde",
                                   "Invalid value 'abcde' (type 'str'), expected type 'string'")
        self.assertValidationError(m, "abcdefgh",
                                   "Invalid value 'abcdefgh' (type 'str'), expected type 'string'")

    # int type
    def test_model_int(self):

        # Int model
        m = TypeInt()

        # Success
        v = m.validate(5)
        self.assertEqual(v, 5)
        self.assertTrue(isinstance(v, int))

        # Success - long
        v = m.validate(5L)
        self.assertEqual(v, 5L)
        self.assertTrue(isinstance(v, long))

        # Success - float
        v = m.validate(5.)
        self.assertEqual(v, 5.)
        self.assertTrue(isinstance(v, int))

        # Success - Decimal
        v = m.validate(Decimal(5))
        self.assertEqual(v, Decimal(5))
        self.assertTrue(isinstance(v, int))

        # Success - accept string
        v = m.validate("5", acceptString = True)
        self.assertEqual(v, 5)
        self.assertTrue(isinstance(v, int))

        # Success - accept unicode string
        v = m.validate(unicode("7"), acceptString = True)
        self.assertEqual(v, 7)
        self.assertTrue(isinstance(v, int))

        # Failure - invalid float
        self.assertValidationError(m, 5.5,
                                   "Invalid value 5.5 (type 'float'), expected type 'int'")

        # Failure - invalid Decimal
        self.assertValidationError(m, Decimal("5.5"),
                                   "Invalid value 5.5 (type 'Decimal'), expected type 'int'")

        # Failure - string
        self.assertValidationError(m, "5",
                                   "Invalid value '5' (type 'str'), expected type 'int'")

        # Failure - bool
        self.assertValidationError(m, True,
                                   "Invalid value True (type 'bool'), expected type 'int'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'int'")

        # Failure - invalid accept string
        self.assertValidationError(m, "5L",
                                   "Invalid value '5L' (type 'str'), expected type 'int'",
                                   acceptString = True)

    # int type constraints
    def test_model_int_constraint(self):

        # Less-than
        m = TypeInt()
        m.constraint_lt = 5
        self.assertEqual(m.validate(4), 4)
        self.assertEqual(m.validate(0), 0)
        self.assertEqual(m.validate(-4), -4)
        self.assertValidationError(m, 5,
                                   "Invalid value 5 (type 'int'), expected type 'int'")
        self.assertValidationError(m, 50,
                                   "Invalid value 50 (type 'int'), expected type 'int'")

        # Less-than or equal-to
        m = TypeInt()
        m.constraint_lte = 5
        self.assertEqual(m.validate(5), 5)
        self.assertEqual(m.validate(0), 0)
        self.assertEqual(m.validate(-4), -4)
        self.assertValidationError(m, 6,
                                   "Invalid value 6 (type 'int'), expected type 'int'")
        self.assertValidationError(m, 60,
                                   "Invalid value 60 (type 'int'), expected type 'int'")

        # Greater-than
        m = TypeInt()
        m.constraint_gt = 5
        self.assertEqual(m.validate(6), 6)
        self.assertEqual(m.validate(60), 60)
        self.assertValidationError(m, 5,
                                   "Invalid value 5 (type 'int'), expected type 'int'")
        self.assertValidationError(m, 0,
                                   "Invalid value 0 (type 'int'), expected type 'int'")

        # Greater-than or equal-to
        m = TypeInt()
        m.constraint_gte = 5
        self.assertEqual(m.validate(5), 5)
        self.assertEqual(m.validate(50), 50)
        self.assertValidationError(m, 4,
                                   "Invalid value 4 (type 'int'), expected type 'int'")
        self.assertValidationError(m, 0,
                                   "Invalid value 0 (type 'int'), expected type 'int'")

        # >= and <=
        m = TypeInt()
        m.constraint_gte = 5
        m.constraint_lte = 10
        self.assertEqual(m.validate(5), 5)
        self.assertEqual(m.validate(8), 8)
        self.assertEqual(m.validate(10), 10)
        self.assertValidationError(m, 4,
                                   "Invalid value 4 (type 'int'), expected type 'int'")
        self.assertValidationError(m, 11,
                                   "Invalid value 11 (type 'int'), expected type 'int'")

        # > and <
        m = TypeInt()
        m.constraint_gt = 4.5
        m.constraint_lt = 10.5
        self.assertEqual(m.validate(5), 5)
        self.assertEqual(m.validate(8), 8)
        self.assertEqual(m.validate(10), 10)
        self.assertValidationError(m, 4,
                                   "Invalid value 4 (type 'int'), expected type 'int'")
        self.assertValidationError(m, 11,
                                   "Invalid value 11 (type 'int'), expected type 'int'")

    # float type
    def test_model_float(self):

        # Float model
        m = TypeFloat()

        # Success
        v = m.validate(5.5)
        self.assertEqual(v, 5.5)
        self.assertTrue(isinstance(v, float))

        # Success - int
        v = m.validate(6)
        self.assertEqual(v, 6.)
        self.assertTrue(isinstance(v, float))

        # Success - long
        v = m.validate(7L)
        self.assertEqual(v, 7.)
        self.assertTrue(isinstance(v, float))

        # Success - Decimal
        v = m.validate(Decimal("5.5"))
        self.assertEqual(v, 5.5)
        self.assertTrue(isinstance(v, float))

        # Success - accept string
        v = m.validate("8.5", acceptString = True)
        self.assertEqual(v, 8.5)
        self.assertTrue(isinstance(v, float))

        # Success - accept unicode string
        v = m.validate(unicode("8.5"), acceptString = True)
        self.assertEqual(v, 8.5)
        self.assertTrue(isinstance(v, float))

        # Failure - string
        self.assertValidationError(m, "17.5",
                                   "Invalid value '17.5' (type 'str'), expected type 'float'")

        # Failure - bool
        self.assertValidationError(m, False,
                                   "Invalid value False (type 'bool'), expected type 'float'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'float'")

        # Failure - invalid accept string
        self.assertValidationError(m, "asdf",
                                   "Invalid value 'asdf' (type 'str'), expected type 'float'",
                                   acceptString = True)

    # float type constraints
    def test_model_float_constraint(self):

        # Less-than
        m = TypeFloat()
        m.constraint_lt = 5.5
        self.assertEqual(m.validate(5.4), 5.4)
        self.assertEqual(m.validate(0), 0)
        self.assertEqual(m.validate(-4), -4)
        self.assertValidationError(m, 5.5,
                                   "Invalid value 5.5 (type 'float'), expected type 'float'")
        self.assertValidationError(m, 50,
                                   "Invalid value 50 (type 'int'), expected type 'float'")

        # Less-than or equal-to
        m = TypeFloat()
        m.constraint_lte = 5.5
        self.assertEqual(m.validate(5.5), 5.5)
        self.assertEqual(m.validate(0), 0)
        self.assertEqual(m.validate(-4), -4)
        self.assertValidationError(m, 5.6,
                                   "Invalid value 5.6 (type 'float'), expected type 'float'")
        self.assertValidationError(m, 60,
                                   "Invalid value 60 (type 'int'), expected type 'float'")

        # Greater-than
        m = TypeFloat()
        m.constraint_gt = 5.5
        self.assertEqual(m.validate(5.6), 5.6)
        self.assertEqual(m.validate(60), 60)
        self.assertValidationError(m, 5.5,
                                   "Invalid value 5.5 (type 'float'), expected type 'float'")
        self.assertValidationError(m, 0,
                                   "Invalid value 0 (type 'int'), expected type 'float'")
        self.assertValidationError(m, -5,
                                   "Invalid value -5 (type 'int'), expected type 'float'")

        # Greater-than or equal-to
        m = TypeFloat()
        m.constraint_gte = 5.5
        self.assertEqual(m.validate(5.5), 5.5)
        self.assertEqual(m.validate(50), 50)
        self.assertValidationError(m, 5.4,
                                   "Invalid value 5.4 (type 'float'), expected type 'float'")
        self.assertValidationError(m, 0,
                                   "Invalid value 0 (type 'int'), expected type 'float'")
        self.assertValidationError(m, -5,
                                   "Invalid value -5 (type 'int'), expected type 'float'")

        # >= and <=
        m = TypeFloat()
        m.constraint_gte = 4.5
        m.constraint_lte = 10.5
        self.assertEqual(m.validate(4.5), 4.5)
        self.assertEqual(m.validate(8), 8)
        self.assertEqual(m.validate(10.5), 10.5)
        self.assertValidationError(m, 4.4,
                                   "Invalid value 4.4 (type 'float'), expected type 'float'")
        self.assertValidationError(m, 10.6,
                                   "Invalid value 10.6 (type 'float'), expected type 'float'")

        # > and <
        m = TypeFloat()
        m.constraint_gt = 4.5
        m.constraint_lt = 10.5
        self.assertEqual(m.validate(5), 5)
        self.assertEqual(m.validate(8), 8)
        self.assertEqual(m.validate(10), 10)
        self.assertValidationError(m, 4.5,
                                   "Invalid value 4.5 (type 'float'), expected type 'float'")
        self.assertValidationError(m, 4,
                                   "Invalid value 4 (type 'int'), expected type 'float'")
        self.assertValidationError(m, 10.5,
                                   "Invalid value 10.5 (type 'float'), expected type 'float'")

    # bool type
    def test_model_bool(self):

        # Bool model
        m = TypeBool()

        # Success
        v = m.validate(True)
        self.assertEqual(v, True)
        self.assertTrue(isinstance(v, bool))
        v = m.validate(False)
        self.assertEqual(v, False)
        self.assertTrue(isinstance(v, bool))

        # Success - accept string
        v = m.validate("true", acceptString = True)
        self.assertEqual(v, True)
        self.assertTrue(isinstance(v, bool))
        v = m.validate("false", acceptString = True)
        self.assertEqual(v, False)
        self.assertTrue(isinstance(v, bool))

        # Failure - int
        self.assertValidationError(m, 0,
                                   "Invalid value 0 (type 'int'), expected type 'bool'")

        # Failure - string
        self.assertValidationError(m, "true",
                                   "Invalid value 'true' (type 'str'), expected type 'bool'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'bool'")

        # Failure - invalid accept string
        self.assertValidationError(m, "True",
                                   "Invalid value 'True' (type 'str'), expected type 'bool'",
                                   acceptString = True)

    # datetime type
    def test_model_datetime(self):

        # Datetime model
        m = TypeDatetime()

        # Success - "zulu" date/time
        v = m.validate("2012-09-06T07:05:00Z")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T07:05:00+00:00")

        # Success - date string
        v = m.validate("2012-09-06")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T00:00:00+00:00")

        # Success - date/time string with offset
        v = m.validate("2012-09-06T07:05:00-07:00")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T14:05:00+00:00")

        # Success - fractional date/time string with offset
        v = m.validate("2012-09-06T07:05:00.5-07:00")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T14:05:00.500000+00:00")

        # Success - fraction (comma) date/time string with offset
        v = m.validate("2012-09-06T07:05:00,5-07:00")
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T14:05:00.500000+00:00")

        # Success - UTC date/time object
        v = m.validate(datetime(2012, 9, 6, 7, 5, 0, 0, TypeDatetime.TZUTC()))
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(jsonDefault(v), "2012-09-06T07:05:00+00:00")

        # Success - Local date/time object
        v = m.validate(datetime(2012, 9, 6, 7, 5, 0, 0, TypeDatetime.TZLocal()))
        self.assertTrue(isinstance(v, datetime))
        self.assertTrue(isinstance(v.tzinfo, TypeDatetime.TZLocal))
        self.assertTrue(v.isoformat().startswith("2012-09-06T07:05:00"))
        v2 = m.validate(jsonDefault(v))
        self.assertTrue(isinstance(v2, datetime))
        self.assertTrue(isinstance(v2.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(v, v2)

        # Success - date/time object with no TZ
        v = m.validate(datetime(2012, 9, 6, 7, 5))
        self.assertTrue(isinstance(v, datetime))
        self.assertEqual(v.tzinfo, None)
        self.assertTrue(jsonDefault(v).startswith("2012-09-06T07:05:00"))
        v2 = m.validate(jsonDefault(v))
        self.assertTrue(isinstance(v2, datetime))
        self.assertTrue(isinstance(v2.tzinfo, TypeDatetime.TZUTC))
        self.assertEqual(datetime(2012, 9, 6, 7, 5, tzinfo = TypeDatetime.TZLocal()), v2)

        # Failure - empty string
        self.assertValidationError(m, "",
                                   "Invalid value '' (type 'str'), expected type 'datetime'")

        # Failure - garbage string
        self.assertValidationError(m, "asdfasdfasdfasdfasdf",
                                   "Invalid value 'asdfasdfasdfasdfasdf' (type 'str'), expected type 'datetime'")

        # Failure - int
        self.assertValidationError(m, 17,
                                   "Invalid value 17 (type 'int'), expected type 'datetime'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'datetime'")

        # Failure - no offset
        self.assertValidationError(m, "2012-09-06T07:05:00",
                                   "Invalid value '2012-09-06T07:05:00' (type 'str'), expected type 'datetime'")

        # Failure - invalid year
        self.assertValidationError(m, "12-09-06T07:05:00Z",
                                   "Invalid value '12-09-06T07:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid year
        self.assertValidationError(m, "0000-09-06T07:05:00Z",
                                   "Invalid value '0000-09-06T07:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid month
        self.assertValidationError(m, "2012-00-06T07:05:00Z",
                                   "Invalid value '2012-00-06T07:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid month
        self.assertValidationError(m, "2012-13-06T07:05:00Z",
                                   "Invalid value '2012-13-06T07:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid day
        self.assertValidationError(m, "2012-12-00T07:05:00Z",
                                   "Invalid value '2012-12-00T07:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid day
        self.assertValidationError(m, "2012-12-32T07:05:00Z",
                                   "Invalid value '2012-12-32T07:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid hour
        self.assertValidationError(m, "2012-12-30T24:05:00Z",
                                   "Invalid value '2012-12-30T24:05:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid minute
        self.assertValidationError(m, "2012-12-30T23:60:00Z",
                                   "Invalid value '2012-12-30T23:60:00Z' (type 'str'), expected type 'datetime'")

        # Failure - invalid seconds
        self.assertValidationError(m, "2012-12-30T23:59:60Z",
                                   "Invalid value '2012-12-30T23:59:60Z' (type 'str'), expected type 'datetime'")

    # uuid type
    def test_model_uuid(self):

        # Uuid model
        m = TypeUuid()

        # Success - UUID object
        o = UUID("8daeb11e-3c83-11e2-a7aa-20c9d0427a89")
        v = m.validate(o)
        self.assertTrue(v is o)

        # Success - lowercase
        v = m.validate("8daeb11e-3c83-11e2-a7aa-20c9d0427a89")
        self.assertEqual(v, UUID("8daeb11e-3c83-11e2-a7aa-20c9d0427a89"))

        # Success - uppercase
        v = m.validate("8DAEB11E-3C83-11E2-A7AA-20C9D0427A89")
        self.assertEqual(v, UUID("8daeb11e-3c83-11e2-a7aa-20c9d0427a89"))

        # Success - braces
        v = m.validate("{8daeb11e-3c83-11e2-a7aa-20c9d0427a89}")
        self.assertEqual(v, UUID("8daeb11e-3c83-11e2-a7aa-20c9d0427a89"))

        # Success - urn
        v = m.validate("urn:uuid:8daeb11e-3c83-11e2-a7aa-20c9d0427a89")
        self.assertEqual(v, UUID("8daeb11e-3c83-11e2-a7aa-20c9d0427a89"))

        # Failure - int
        self.assertValidationError(m, 0,
                                   "Invalid value 0 (type 'int'), expected type 'uuid'")

        # Failure - bool
        self.assertValidationError(m, True,
                                   "Invalid value True (type 'bool'), expected type 'uuid'")

        # Failure - None
        self.assertValidationError(m, None,
                                   "Invalid value None (type 'NoneType'), expected type 'uuid'")

        # Failure - invalid string
        self.assertValidationError(m, "asdfasdf",
                                   "Invalid value 'asdfasdf' (type 'str'), expected type 'uuid'")
