#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from wads import Struct, parseSpec, ValidationError
from wads.model import TypeStruct, TypeArray, TypeString, TypeInt, TypeFloat, TypeBool

import unittest


# Struct validation tests
class TestParseSpec(unittest.TestCase):

    def test_simple(self):

        m, errors = parseSpec("""
# This is the struct
struct MyStruct

    # The "a" member
    string a

    # The "b" member
    int b

# This is the second struct
struct MyStruct2
    int a
    [optional] \
        float b
    string c
    bool d
    int[] e
    [optional] MyStruct[] f

# The action
action MyAction
    input
        int a
        [optional] string b
    output
        bool c
""")

        # Check errors
        self.assertEqual(len(errors), 0)

        # Check types
        self.assertEqual(len(errors), 0)
        self.assertTrue("MyStruct" in m.types)
        self.assertTrue("MyStruct2" in m.types)
        self.assertTrue(isinstance(m.types["MyStruct"], TypeStruct))
        self.assertEqual(m.types["MyStruct"].typeName, "MyStruct")
        self.assertEqual(len(m.types["MyStruct"].members), 2)
        self.assertEqual(m.types["MyStruct"].members[0].name, "a")
        self.assertTrue(isinstance(m.types["MyStruct"].members[0].type, TypeString))
        self.assertFalse(m.types["MyStruct"].members[0].isOptional)
        self.assertEqual(m.types["MyStruct"].members[1].name, "b")
        self.assertTrue(isinstance(m.types["MyStruct"].members[1].type, TypeInt))
        self.assertFalse(m.types["MyStruct"].members[1].isOptional)
        self.assertTrue(isinstance(m.types["MyStruct2"], TypeStruct))
        self.assertEqual(m.types["MyStruct2"].typeName, "MyStruct2")
        self.assertEqual(len(m.types["MyStruct2"].members), 6)
        self.assertEqual(m.types["MyStruct2"].members[0].name, "a")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[0].type, TypeInt))
        self.assertFalse(m.types["MyStruct2"].members[0].isOptional)
        self.assertEqual(m.types["MyStruct2"].members[1].name, "b")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[1].type, TypeFloat))
        self.assertTrue(m.types["MyStruct2"].members[1].isOptional)
        self.assertEqual(m.types["MyStruct2"].members[2].name, "c")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[2].type, TypeString))
        self.assertFalse(m.types["MyStruct2"].members[2].isOptional)
        self.assertEqual(m.types["MyStruct2"].members[3].name, "d")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[3].type, TypeBool))
        self.assertFalse(m.types["MyStruct2"].members[3].isOptional)
        self.assertEqual(m.types["MyStruct2"].members[4].name, "e")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[4].type, TypeArray))
        self.assertTrue(isinstance(m.types["MyStruct2"].members[4].type.type, TypeInt))
        self.assertFalse(m.types["MyStruct2"].members[4].isOptional)
        self.assertEqual(m.types["MyStruct2"].members[5].name, "f")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[5].type, TypeArray))
        self.assertTrue(isinstance(m.types["MyStruct2"].members[5].type.type, TypeStruct))
        self.assertEqual(m.types["MyStruct2"].members[5].type.type.typeName, "MyStruct")
        self.assertTrue(m.types["MyStruct2"].members[5].isOptional)

        # Check actions
        self.assertEqual(len(m.actions), 1)
        self.assertTrue("MyAction" in m.actions)
        self.assertTrue(isinstance(m.actions["MyAction"].inputType, TypeStruct))
        self.assertEqual(m.actions["MyAction"].inputType.typeName, "struct")
        self.assertEqual(len(m.actions["MyAction"].inputType.members), 2)
        self.assertEqual(m.actions["MyAction"].inputType.members[0].name, "a")
        self.assertTrue(isinstance(m.actions["MyAction"].inputType.members[0].type, TypeInt))
        self.assertFalse(m.actions["MyAction"].inputType.members[0].isOptional)
        self.assertEqual(m.actions["MyAction"].inputType.members[1].name, "b")
        self.assertTrue(isinstance(m.actions["MyAction"].inputType.members[1].type, TypeString))
        self.assertTrue(m.actions["MyAction"].inputType.members[1].isOptional)
        self.assertTrue(isinstance(m.actions["MyAction"].outputType, TypeStruct))
        self.assertEqual(m.actions["MyAction"].outputType.typeName, "struct")
        self.assertEqual(len(m.actions["MyAction"].outputType.members), 1)
        self.assertEqual(m.actions["MyAction"].outputType.members[0].name, "c")
        self.assertTrue(isinstance(m.actions["MyAction"].outputType.members[0].type, TypeBool))
        self.assertFalse(m.actions["MyAction"].outputType.members[0].isOptional)
