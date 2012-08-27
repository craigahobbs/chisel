#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from wads import Struct, SpecParser, ValidationError
from wads.model import TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool

from StringIO import StringIO
import unittest


# Struct validation tests
class TestParseSpec(unittest.TestCase):

    def assertMembers(self, struct, members):
        self.assertEqual(len(struct.members), len(members))
        for ixMember in xrange(0, len(members)):
            name, typeInstOrType, isOptional = members[ixMember]
            self.assertTrue(isinstance(struct, TypeStruct))
            self.assertEqual(struct.members[ixMember].name, name)
            self.assertTrue(struct.members[ixMember].typeInst is typeInstOrType or
                            isinstance(struct.members[ixMember].typeInst, typeInstOrType))
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

        parser = SpecParser()
        parser.parse(StringIO("""\
# This is an enum
enum MyEnum
    Foo
    Bar

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
"""))
        parser.finalize()
        m = parser.model

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(m.types), 3)
        self.assertEqual(len(m.actions), 1)

        # Check enum types
        self.assertTrue(isinstance(m.types["MyEnum"], TypeEnum))
        self.assertEqual(m.types["MyEnum"].typeName, "MyEnum")
        self.assertEqual(m.types["MyEnum"].values, ["Foo", "Bar"])

        # Check struct types
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
        self.assertTrue(isinstance(m.types["MyStruct2"].members[4].typeInst.typeInst, TypeInt))
        self.assertTrue(isinstance(m.types["MyStruct2"].members[5].typeInst.typeInst, TypeStruct))
        self.assertEqual(m.types["MyStruct2"].members[5].typeInst.typeInst.typeName, "MyStruct")
        self.assertTrue(isinstance(m.types["MyStruct2"].members[6].typeInst.typeInst, TypeFloat))

        # Check actions
        self.assertActionMembers(m, "MyAction",
                                (("a", TypeInt, False),
                                 ("b", TypeString, True)),
                                (("c", TypeBool, False),))

    def test_multiple(self):

        parser = SpecParser()
        parser.parse(StringIO("""\
enum MyEnum
    A
    B

action MyAction
    input
        MyStruct2 a
    output
        MyStruct b
        MyEnum2 c

struct MyStruct
    string c
    MyEnum2 d
    MyStruct2 e
"""))
        parser.parse(StringIO("""\
action MyAction2
    input
        MyStruct d
    output
        MyStruct2 e

struct MyStruct2
    string f
    MyEnum2 g

enum MyEnum2
    C
    D
"""))
        parser.finalize()
        m = parser.model

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(m.types), 4)
        self.assertEqual(len(m.actions), 2)

        # Check enum types
        self.assertTrue(isinstance(m.types["MyEnum"], TypeEnum))
        self.assertEqual(m.types["MyEnum"].typeName, "MyEnum")
        self.assertEqual(m.types["MyEnum"].values, ["A", "B"])
        self.assertTrue(isinstance(m.types["MyEnum2"], TypeEnum))
        self.assertEqual(m.types["MyEnum2"].typeName, "MyEnum2")
        self.assertEqual(m.types["MyEnum2"].values, ["C", "D"])

        # Check struct types
        self.assertStructMembers(m, "MyStruct",
                                 (("c", TypeString, False),
                                  ("d", m.types["MyEnum2"], False),
                                  ("e", m.types["MyStruct2"], False)))
        self.assertStructMembers(m, "MyStruct2",
                                 (("f", TypeString, False),
                                  ("g", m.types["MyEnum2"], False)))

        # Check actions
        self.assertActionMembers(m, "MyAction",
                                (("a", TypeStruct, False),),
                                (("b", TypeStruct, False),
                                 ("c", m.types["MyEnum2"], False)))
        self.assertEqual(m.actions["MyAction"].inputType.members[0].typeInst.typeName, "MyStruct2")
        self.assertEqual(m.actions["MyAction"].outputType.members[0].typeInst.typeName, "MyStruct")
        self.assertActionMembers(m, "MyAction2",
                                (("d", TypeStruct, False),),
                                (("e", TypeStruct, False),))
        self.assertEqual(m.actions["MyAction2"].inputType.members[0].typeInst.typeName, "MyStruct")
        self.assertEqual(m.actions["MyAction2"].outputType.members[0].typeInst.typeName, "MyStruct2")

    def test_unknown_type(self):

        parser = SpecParser()
        parser.parse(StringIO("""\
struct Foo
    MyBadType a

action MyAction
    input
        MyBadType2 a
    output
        MyBadType b
"""), fileName = "foo")
        parser.finalize()
        m = parser.model

        # Check counts
        self.assertEqual(len(parser.errors), 3)
        self.assertEqual(len(m.types), 1)
        self.assertEqual(len(m.actions), 1)

        # Check errors
        self.assertEqual(parser.errors,
                         ["foo:2: error: Unknown member type 'MyBadType'",
                          "foo:6: error: Unknown member type 'MyBadType2'",
                          "foo:8: error: Unknown member type 'MyBadType'"])
