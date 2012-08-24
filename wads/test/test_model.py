#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from wads import Struct, ValidationError
from wads.model import Member, TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool

import unittest


# Struct validation tests
class TestStructValidation(unittest.TestCase):

    def test_simple(self):

        # Build a type model
        m = TypeStruct()
        m.members.append(Member("a", TypeInt()))
        m.members.append(Member("b", TypeString()))
        mc = TypeStruct()
        mc.members.append(Member("d", TypeBool()))
        mc.members.append(Member("e", TypeFloat()))
        m.members.append(Member("c", mc))
        m.members.append(Member("f", TypeArray(TypeString())))
        m.members.append(Member("g", TypeDict(TypeInt()), isOptional = True))
        m.members.append(Member("h", TypeEnum(values = ["Foo", "Bar"]), isOptional = True))

        # Validate success
        s = m.validate({ "a": 5,
                         "b": "Hello",
                         "c": Struct({ "d": True, "e": 5.5 }),
                         "f": [ "Foo", "Bar" ],
                         "g": { "Foo": 5 },
                         "h": "Foo"
                         })
        self.assertTrue(isinstance(s, dict))
        self.assertTrue(isinstance(s["a"], int))
        self.assertEqual(s["a"], 5)
        self.assertTrue(isinstance(s["b"], str))
        self.assertEqual(s["b"], "Hello")
        self.assertTrue(isinstance(s["c"], Struct))
        self.assertTrue(isinstance(s["c"].d, bool))
        self.assertEqual(s["c"].d, True)
        self.assertTrue(isinstance(s["c"].e, float))
        self.assertEqual(s["c"].e, 5.5)
        self.assertTrue(isinstance(s["f"], list))
        self.assertTrue(isinstance(s["f"][0], str))
        self.assertEqual(s["f"][0], "Foo")
        self.assertTrue(isinstance(s["f"][1], str))
        self.assertEqual(s["f"][1], "Bar")
        self.assertEqual(s["g"]["Foo"], 5)
        self.assertEqual(s["h"], "Foo")

        # Validate success - loosely
        s = m.validate(Struct({ "a": "5",
                                "b": "Hello",
                                "c": { "d": "true", "e": "5.5" },
                                "f": [ "Foo", "Bar" ]
                                }), isLoose = True)
        self.assertTrue(isinstance(s, Struct))
        self.assertTrue(isinstance(s.a, int))
        self.assertEqual(s.a, 5)
        self.assertTrue(isinstance(s.b, str))
        self.assertEqual(s.b, "Hello")
        self.assertTrue(isinstance(s.c, Struct))
        self.assertTrue(isinstance(s.c.d, bool))
        self.assertEqual(s.c.d, True)
        self.assertTrue(isinstance(s.c.e, float))
        self.assertEqual(s.c.e, 5.5)
        self.assertTrue(isinstance(s.f, list))
        self.assertTrue(isinstance(s.f[0], str))
        self.assertEqual(s.f[0], "Foo")
        self.assertTrue(isinstance(s.f[1], str))
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
            self.assertEqual(str(e), "Invalid enumeration value 'Bonk' for 'enum'")
