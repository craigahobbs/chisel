#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Struct, SpecParser, ValidationError
from chisel.model import TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool, TypeDatetime

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

    # Test valid spec parsing
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
    [optional] datetime h

# The action
action MyAction
    input
        int a
        [optional] string b
    output
        bool c
    errors
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
                                 ("g", TypeDict, True),
                                 ("h", TypeDatetime, True)))
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

    # Test multiple parse calls per parser instance
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

    # Test members referencing unknown user types
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

    # Test valid attribute usage
    def test_attributes(self):

        parser = SpecParser()
        parser.parse(StringIO("""\
struct MyStruct
    [optional,> 1,<= 10.5] int i1
    [>= 1, < 10, optional ] int i2
    [ > 1, <= 10.5] float f1
    [>= 1.5, < 10 ] float f2
    [len > 5, len < 101] string s1
    [ len >= 5, len <= 100 ] string s2
    [> 5] int[] ai1
    [< 15] int{} di1
    [ > 0, <= 10] int i3
"""), fileName = "foo")
        parser.finalize()
        m = parser.model
        s = parser.model.types["MyStruct"]

        # Check counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(m.types), 1)
        self.assertEqual(len(m.actions), 0)

        # Check struct members
        self.assertStructByName(m, "MyStruct",
                                (("i1", TypeInt, True),
                                 ("i2", TypeInt, True),
                                 ("f1", TypeFloat, False),
                                 ("f2", TypeFloat, False),
                                 ("s1", TypeString, False),
                                 ("s2", TypeString, False),
                                 ("ai1", TypeArray, False),
                                 ("di1", TypeDict, False),
                                 ("i3", TypeInt, False),
                                 ))

        # Check i1 constraints
        i1 = s.members[0].typeInst
        self.assertEqual(i1.constraint_lt, None)
        self.assertEqual(i1.constraint_lte, 10.5)
        self.assertEqual(i1.constraint_gt, 1)
        self.assertEqual(i1.constraint_gte, None)

        # Check i2 constraints
        i2 = s.members[1].typeInst
        self.assertEqual(i2.constraint_lt, 10)
        self.assertEqual(i2.constraint_lte, None)
        self.assertEqual(i2.constraint_gt, None)
        self.assertEqual(i2.constraint_gte, 1)

        # Check f1 constraints
        f1 = s.members[2].typeInst
        self.assertEqual(f1.constraint_lt, None)
        self.assertEqual(f1.constraint_lte, 10.5)
        self.assertEqual(f1.constraint_gt, 1)
        self.assertEqual(f1.constraint_gte, None)

        # Check f2 constraints
        f2 = s.members[3].typeInst
        self.assertEqual(f2.constraint_lt, 10)
        self.assertEqual(f2.constraint_lte, None)
        self.assertEqual(f2.constraint_gt, None)
        self.assertEqual(f2.constraint_gte, 1.5)

        # Check s1 constraints
        s1 = s.members[4].typeInst
        self.assertEqual(s1.constraint_len_lt, 101)
        self.assertEqual(s1.constraint_len_lte, None)
        self.assertEqual(s1.constraint_len_gt, 5)
        self.assertEqual(s1.constraint_len_gte, None)

        # Check s2 constraints
        s2 = s.members[5].typeInst
        self.assertEqual(s2.constraint_len_lt, None)
        self.assertEqual(s2.constraint_len_lte, 100)
        self.assertEqual(s2.constraint_len_gt, None)
        self.assertEqual(s2.constraint_len_gte, 5)

        # Check ai1 constraints
        ai1 = s.members[6].typeInst.typeInst
        self.assertEqual(ai1.constraint_lt, None)
        self.assertEqual(ai1.constraint_lte, None)
        self.assertEqual(ai1.constraint_gt, 5)
        self.assertEqual(ai1.constraint_gte, None)

        # Check di1 constraints
        di1 = s.members[7].typeInst.typeInst
        self.assertEqual(di1.constraint_lt, 15)
        self.assertEqual(di1.constraint_lte, None)
        self.assertEqual(di1.constraint_gt, None)
        self.assertEqual(di1.constraint_gte, None)

        # Check i3 constraints
        i3 = s.members[8].typeInst
        self.assertEqual(i3.constraint_lt, None)
        self.assertEqual(i3.constraint_lte, 10)
        self.assertEqual(i3.constraint_gt, 0)
        self.assertEqual(i3.constraint_gte, None)

    # Test invalid member attribute usage
    def test_attributes_fail(self):

        def checkFail(errors, spec):
            parser = SpecParser()
            parser.parse(StringIO(spec))
            parser.finalize()
            self.assertEqual(len(parser.errors), len(errors))
            self.assertEqual(parser.errors, errors)

        # Invalid len> attribute usage
        checkFail([":2: error: Invalid attribute 'len > 1'"],
"""\
struct MyStruct
    [len > 1] int i
""")

        # Invalid len< attribute usage
        checkFail([":2: error: Invalid attribute 'len < 10'"],
"""\
struct MyStruct
    [len < 10] float f
""")

        # Invalid > and < attribute usage
        checkFail([":2: error: Invalid attribute '>5'",
                   ":2: error: Invalid attribute '<7'"],
"""\
struct MyStruct
    [>5, <7] string s
""")

        # Invalid >= and <= attribute usage
        checkFail([":6: error: Invalid attribute '>=1'",
                   ":7: error: Invalid attribute '<=2'"],
"""\
enum MyEnum
    Foo
    Bar

struct MyStruct
    [>=1] MyStruct a
    [<=2] MyEnum b
""")

        # Unknown attribute syntax
        checkFail([":2: error: Syntax error"],
"""\
struct MyStruct
    [regex="abc"] string a
""")

    # Test documentation comments
    def test_doc(self):

        parser = SpecParser()
        parser.parse(StringIO("""\
# My enum
enum MyEnum

  # MyEnum value 1
  MyEnumValue1

  #
  # MyEnum value 2
  #
  # Second line
  #
  MyEnumValue2

#- Hidden comment
enum MyEnum2

  #- Hidden comment
  MyEnum2Value1

# My struct
struct MyStruct

  # MyStruct member a
  int a

  #
  # MyStruct member b
  #
  string[] b

#- Hidden comment
struct MyStruct2

  #- Hidden comment
  int a

# My action
action MyAction

  input

    # My input member
    float a

  output

    # My output member
    datetime b
"""))
        parser.finalize()
        self.assertEqual(len(parser.errors), 0)
        m = parser.model

        # Check model documentation comments
        self.assertEqual(m.types["MyEnum"].doc,
                         ["My enum"])
        self.assertEqual(m.types["MyEnum"].values[0].doc,
                         ["MyEnum value 1"])
        self.assertEqual(m.types["MyEnum"].values[1].doc,
                         ["", "MyEnum value 2", "", "Second line", ""])
        self.assertEqual(m.types["MyEnum2"].doc,
                         [])
        self.assertEqual(m.types["MyEnum2"].values[0].doc,
                         [])
        self.assertEqual(m.types["MyStruct"].doc,
                         ["My struct"])
        self.assertEqual(m.types["MyStruct"].members[0].doc,
                         ["MyStruct member a"])
        self.assertEqual(m.types["MyStruct"].members[1].doc,
                         ["", "MyStruct member b", ""])
        self.assertEqual(m.types["MyStruct2"].doc,
                         [])
        self.assertEqual(m.types["MyStruct2"].members[0].doc,
                         [])
        self.assertEqual(m.actions["MyAction"].doc,
                         ["My action"])
        self.assertEqual(m.actions["MyAction"].inputType.doc,
                         [])
        self.assertEqual(m.actions["MyAction"].inputType.members[0].doc,
                         ["My input member"])
        self.assertEqual(m.actions["MyAction"].outputType.doc,
                         [])
        self.assertEqual(m.actions["MyAction"].outputType.members[0].doc,
                         ["My output member"])
