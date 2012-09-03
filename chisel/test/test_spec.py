#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Struct, SpecParser, ValidationError
from chisel.model import TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool

from StringIO import StringIO
import unittest


# Struct validation tests
class TestParseSpec(unittest.TestCase):

    def assertStruct(self, structTypeInst, members):
        self.assertEqual(len(structTypeInst.members), len(members))
        for ixMember in xrange(0, len(members)):
            name, typeInstOrType, isOptional = members[ixMember]
            self.assertTrue(isinstance(structTypeInst, TypeStruct))
            self.assertEqual(structTypeInst.members[ixMember].name, name)
            self.assertTrue(structTypeInst.members[ixMember].typeInst is typeInstOrType or
                            isinstance(structTypeInst.members[ixMember].typeInst, typeInstOrType))
            self.assertEqual(structTypeInst.members[ixMember].isOptional, isOptional)

    def assertStructByName(self, model, typeName, members):
        self.assertEqual(model.types[typeName].typeName, typeName)
        self.assertStruct(model.types[typeName], members)

    def assertEnum(self, enumTypeInst, values = None):
        values = [] if values is None else values
        self.assertEqual(len(enumTypeInst.values), len(values))
        for enumValue in values:
            self.assertTrue(enumValue in enumTypeInst.values)

    def assertEnumByName(self, model, typeName, values):
        self.assertEqual(model.types[typeName].typeName, typeName)
        self.assertEnum(model.types[typeName], values)

    def assertAction(self, model, actionName, inputMembers, outputMembers, errorValues = None):
        self.assertEqual(model.actions[actionName].inputType.typeName, actionName + "_Input")
        self.assertEqual(model.actions[actionName].outputType.typeName, actionName + "_Output")
        self.assertEqual(model.actions[actionName].errorType.typeName, actionName + "_Error")
        self.assertStruct(model.actions[actionName].inputType, inputMembers)
        self.assertStruct(model.actions[actionName].outputType, outputMembers)
        self.assertEnum(model.actions[actionName].errorType, errorValues)

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
    error
        Error1
        Error2
"""))
        parser.finalize()
        m = parser.model

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(m.types), 3)
        self.assertEqual(len(m.actions), 1)

        # Check enum types
        self.assertEnumByName(m, "MyEnum",
                              ("Foo",
                               "Bar"))

        # Check struct types
        self.assertStructByName(m, "MyStruct",
                                (("a", TypeString, False),
                                 ("b", TypeInt, False)))
        self.assertStructByName(m, "MyStruct2",
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
        self.assertAction(m, "MyAction",
                          (("a", TypeInt, False),
                           ("b", TypeString, True)),
                          (("c", TypeBool, False),),
                          ("Error1",
                           "Error2"))

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
        self.assertEnumByName(m, "MyEnum",
                              ("A",
                               "B"))
        self.assertEnumByName(m, "MyEnum2",
                              ("C",
                               "D"))

        # Check struct types
        self.assertStructByName(m, "MyStruct",
                                (("c", TypeString, False),
                                 ("d", m.types["MyEnum2"], False),
                                 ("e", m.types["MyStruct2"], False)))
        self.assertStructByName(m, "MyStruct2",
                                (("f", TypeString, False),
                                 ("g", m.types["MyEnum2"], False)))

        # Check actions
        self.assertAction(m, "MyAction",
                          (("a", TypeStruct, False),),
                          (("b", TypeStruct, False),
                           ("c", m.types["MyEnum2"], False)))
        self.assertEqual(m.actions["MyAction"].inputType.members[0].typeInst.typeName, "MyStruct2")
        self.assertEqual(m.actions["MyAction"].outputType.members[0].typeInst.typeName, "MyStruct")
        self.assertAction(m, "MyAction2",
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
