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
    [regex = "^[A-Za-z]\w*$" ] string s3
    [regex = "^\\\".*?\\\"$" ] string s4
    [regex = "[abc]\\\\" ] string s5
    [> 5] int[] ai1
    [< 15] int{} di1
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
                                 ("s3", TypeString, False),
                                 ("s4", TypeString, False),
                                 ("s5", TypeString, False),
                                 ("ai1", TypeArray, False),
                                 ("di1", TypeDict, False)))

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
        self.assertEqual(s1.constraint_regex, None)

        # Check s2 constraints
        s2 = s.members[5].typeInst
        self.assertEqual(s2.constraint_len_lt, None)
        self.assertEqual(s2.constraint_len_lte, 100)
        self.assertEqual(s2.constraint_len_gt, None)
        self.assertEqual(s2.constraint_len_gte, 5)
        self.assertEqual(s2.constraint_regex, None)

        # Check s3 constraints
        s3 = s.members[6].typeInst
        self.assertEqual(s3.constraint_len_lt, None)
        self.assertEqual(s3.constraint_len_lte, None)
        self.assertEqual(s3.constraint_len_gt, None)
        self.assertEqual(s3.constraint_len_gte, None)
        self.assertTrue(s3.constraint_regex.search("A_12"))

        # Check s4 constraints
        s4 = s.members[7].typeInst
        self.assertEqual(s4.constraint_len_lt, None)
        self.assertEqual(s4.constraint_len_lte, None)
        self.assertEqual(s4.constraint_len_gt, None)
        self.assertEqual(s4.constraint_len_gte, None)
        self.assertTrue(s4.constraint_regex.search("\"abc\""))

        # Check s5 constraints
        s5 = s.members[8].typeInst
        self.assertEqual(s5.constraint_len_lt, None)
        self.assertEqual(s5.constraint_len_lte, None)
        self.assertEqual(s5.constraint_len_gt, None)
        self.assertEqual(s5.constraint_len_gte, None)
        self.assertTrue(s5.constraint_regex.search("fooa\\bar"))

        # Check ai1 constraints
        ai1 = s.members[9].typeInst.typeInst
        self.assertEqual(ai1.constraint_lt, None)
        self.assertEqual(ai1.constraint_lte, None)
        self.assertEqual(ai1.constraint_gt, 5)
        self.assertEqual(ai1.constraint_gte, None)

        # Check di1 constraints
        di1 = s.members[10].typeInst.typeInst
        self.assertEqual(di1.constraint_lt, 15)
        self.assertEqual(di1.constraint_lte, None)
        self.assertEqual(di1.constraint_gt, None)
        self.assertEqual(di1.constraint_gte, None)

    def test_attributes_fail(self):

        def checkFail(errors, spec):
            parser = SpecParser()
            parser.parse(StringIO(spec))
            parser.finalize()
            self.assertEqual(len(parser.errors), len(errors))
            self.assertEqual(parser.errors, errors)

        checkFail([":2: error: Invalid attribute 'len > 1'"],
"""\
struct MyStruct
    [len > 1] int i
""")

        checkFail([":2: error: Invalid attribute 'len < 10'"],
"""\
struct MyStruct
    [len < 10] float f
""")

        checkFail([":2: error: Invalid attribute 'regex = \"^[abcd]$\"'"],
"""\
struct MyStruct
    [ regex = "^[abcd]$" ] int i
""")

        checkFail([":2: error: Invalid attribute 'regex = \"^[abcd]$\"'"],
"""\
struct MyStruct
    [ regex = "^[abcd]$" ] float f
""")

        checkFail([":2: error: Invalid attribute '>5'",
                   ":2: error: Invalid attribute '<7'"],
"""\
struct MyStruct
    [>5, <7] string s
""")

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
