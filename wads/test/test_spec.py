#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from wads import Struct, parseSpec, ValidationError
from wads.model import TypeStruct, TypeArray, TypeDict, TypeString, TypeInt, TypeFloat, TypeBool

import unittest


# Struct validation tests
class TestParseSpec(unittest.TestCase):

    def assertMembers(self, struct, members):
        self.assertEqual(len(struct.members), len(members))
        for ixMember in xrange(0, len(members)):
            name, type, isOptional = members[ixMember]
            self.assertTrue(isinstance(struct, TypeStruct))
            self.assertEqual(struct.members[ixMember].name, name)
            self.assertTrue(isinstance(struct.members[ixMember].type, type))
            self.assertEqual(struct.members[ixMember].isOptional, isOptional)

    def assertStructMembers(self, model, typeName, members):
        self.assertEqual(model.types[typeName].typeName, typeName)
        self.assertMembers(model.types[typeName], members)

    def assertActionMembers(self, model, actionName, inputMembers, outputMembers):
        self.assertEqual(model.actions[actionName].inputType.typeName, "struct")
        self.assertEqual(model.actions[actionName].outputType.typeName, "struct")
        self.assertMembers(model.actions[actionName].inputType, inputMembers)
        self.assertMembers(model.actions[actionName].outputType, outputMembers)

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
    [optional] float{} g

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
        self.assertStructMembers(m, "MyStruct",
                                 (("a", TypeString, False),
                                  ("b", TypeInt, False)))
        self.assertStructMembers(m, "MyStruct2",
                                 (("a", TypeInt, False),
                                  ("b", TypeFloat, True),
                                  ("c", TypeString, False),
                                  ("d", TypeBool, False),
                                  ("e", TypeArray, False),
                                  ("f", TypeArray, True),
                                  ("g", TypeDict, True)))
        self.assertTrue(isinstance(m.types["MyStruct2"].members[4].type.type, TypeInt))
        self.assertTrue(isinstance(m.types["MyStruct2"].members[5].type.type, TypeStruct))
        self.assertEqual(m.types["MyStruct2"].members[5].type.type.typeName, "MyStruct")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[6].type.type, TypeFloat))

        # Check actions
        self.assertEqual(len(m.actions), 1)
        self.assertTrue("MyAction" in m.actions)
        self.assertActionMembers(m, "MyAction",
                                (("a", TypeInt, False),
                                 ("b", TypeString, True)),
                                (("c", TypeBool, False),))
