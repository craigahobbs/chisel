#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import SpecParser, SpecParserError
from chisel.model import TypeStruct, TypeArray, TypeDict, TypeEnum, \
    TypeString, TypeInt, TypeFloat, TypeBool, TypeDatetime, TypeUuid

import unittest


# Spec parser unit tests
class TestParseSpec(unittest.TestCase):

    # Helper method to assert struct type member properties
    def assertStruct(self, structTypeInst, members):
        self.assertTrue(isinstance(structTypeInst, TypeStruct))
        self.assertEqual(len(structTypeInst.members), len(members))
        for ixMember in xrange(0, len(members)):
            name, typeInstOrType, isOptional = members[ixMember]
            self.assertEqual(structTypeInst.members[ixMember].name, name)
            self.assertTrue(structTypeInst.members[ixMember].typeInst is typeInstOrType or
                            isinstance(structTypeInst.members[ixMember].typeInst, typeInstOrType))
            self.assertEqual(structTypeInst.members[ixMember].isOptional, isOptional)

    # Helper method to assert struct type member properties (by struct name)
    def assertStructByName(self, parser, typeName, members):
        self.assertEqual(parser.types[typeName].typeName, typeName)
        self.assertStruct(parser.types[typeName], members)

    # Helper method to assert enum type values
    def assertEnum(self, enumTypeInst, values):
        self.assertTrue(isinstance(enumTypeInst, TypeEnum))
        self.assertEqual(len(enumTypeInst.values), len(values))
        for enumValue in values:
            self.assertTrue(enumValue in enumTypeInst.values)

    # Helper method to assert enum type values (by enum name)
    def assertEnumByName(self, parser, typeName, values):
        self.assertEqual(parser.types[typeName].typeName, typeName)
        self.assertEnum(parser.types[typeName], values)

    # Helper method to assert action properties
    def assertAction(self, parser, actionName, inputMembers, outputMembers, errorValues):
        self.assertEqual(parser.actions[actionName].inputType.typeName, actionName + "_Input")
        self.assertEqual(parser.actions[actionName].outputType.typeName, actionName + "_Output")
        self.assertEqual(parser.actions[actionName].errorType.typeName, actionName + "_Error")
        self.assertStruct(parser.actions[actionName].inputType, inputMembers)
        self.assertStruct(parser.actions[actionName].outputType, outputMembers)
        self.assertEnum(parser.actions[actionName].errorType, errorValues)

    # Test valid spec parsing
    def test_spec_simple(self):

        # Parse the spec
        parser = SpecParser()
        parser.parseString("""\
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
    [optional] \\
        float b
    string c
    bool d
    int[] e
    [optional] MyStruct[] f
    [optional] float{} g
    [optional] datetime h
    [optional] uuid i

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

# The second action
action MyAction2
    input
        MyStruct foo
        MyStruct2[] bar

# The third action
action MyAction3
    output
        int a
        datetime b

# The fourth action
action MyAction4
""")

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 3)
        self.assertEqual(len(parser.actions), 4)

        # Check enum types
        self.assertEnumByName(parser, "MyEnum",
                              ("Foo",
                               "Bar"))

        # Check struct types
        self.assertStructByName(parser, "MyStruct",
                                (("a", TypeString, False),
                                 ("b", TypeInt, False)))
        self.assertStructByName(parser, "MyStruct2",
                                (("a", TypeInt, False),
                                 ("b", TypeFloat, True),
                                 ("c", TypeString, False),
                                 ("d", TypeBool, False),
                                 ("e", TypeArray, False),
                                 ("f", TypeArray, True),
                                 ("g", TypeDict, True),
                                 ("h", TypeDatetime, True),
                                 ("i", TypeUuid, True)))
        self.assertTrue(isinstance(parser.types["MyStruct2"].members[4].typeInst.typeInst, TypeInt))
        self.assertTrue(isinstance(parser.types["MyStruct2"].members[5].typeInst.typeInst, TypeStruct))
        self.assertEqual(parser.types["MyStruct2"].members[5].typeInst.typeInst.typeName, "MyStruct")
        self.assertTrue(isinstance(parser.types["MyStruct2"].members[6].typeInst.typeInst, TypeFloat))

        # Check actions
        self.assertAction(parser, "MyAction",
                          (("a", TypeInt, False),
                           ("b", TypeString, True)),
                          (("c", TypeBool, False),),
                          ("Error1",
                           "Error2"))
        self.assertAction(parser, "MyAction2",
                          (("foo", parser.types["MyStruct"], False),
                           ("bar", TypeArray, False)),
                          (),
                          ())
        self.assertTrue(isinstance(parser.actions["MyAction2"].inputType.members[1].typeInst.typeInst, TypeStruct))
        self.assertEqual(parser.actions["MyAction2"].inputType.members[1].typeInst.typeInst.typeName, "MyStruct2")
        self.assertAction(parser, "MyAction3",
                          (),
                          (("a", TypeInt, False),
                           ("b", TypeDatetime, False)),
                          ())
        self.assertAction(parser, "MyAction4",
                          (),
                          (),
                          ())

    # Test multiple parse calls per parser instance
    def test_spec_multiple(self):

        # Parse spec strings
        parser = SpecParser()
        parser.parseString("""\
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
""", finalize = False)
        parser.parseString("""\
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
""")

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 4)
        self.assertEqual(len(parser.actions), 2)

        # Check enum types
        self.assertEnumByName(parser, "MyEnum",
                              ("A",
                               "B"))
        self.assertEnumByName(parser, "MyEnum2",
                              ("C",
                               "D"))

        # Check struct types
        self.assertStructByName(parser, "MyStruct",
                                (("c", TypeString, False),
                                 ("d", parser.types["MyEnum2"], False),
                                 ("e", parser.types["MyStruct2"], False)))
        self.assertStructByName(parser, "MyStruct2",
                                (("f", TypeString, False),
                                 ("g", parser.types["MyEnum2"], False)))

        # Check actions
        self.assertAction(parser, "MyAction",
                          (("a", TypeStruct, False),),
                          (("b", TypeStruct, False),
                           ("c", parser.types["MyEnum2"], False)),
                          ())
        self.assertEqual(parser.actions["MyAction"].inputType.members[0].typeInst.typeName, "MyStruct2")
        self.assertEqual(parser.actions["MyAction"].outputType.members[0].typeInst.typeName, "MyStruct")
        self.assertAction(parser, "MyAction2",
                          (("d", TypeStruct, False),),
                          (("e", TypeStruct, False),),
                          ())
        self.assertEqual(parser.actions["MyAction2"].inputType.members[0].typeInst.typeName, "MyStruct")
        self.assertEqual(parser.actions["MyAction2"].outputType.members[0].typeInst.typeName, "MyStruct2")

    # Test members referencing unknown user types
    def test_spec_error_unknown_type(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString("""\
struct Foo
    MyBadType a

action MyAction
    input
        MyBadType2 a
    output
        MyBadType b
""", fileName = "foo")
            self.fail()
        except SpecParserError:
            pass
        except:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 3)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 1)

        # Check errors
        self.assertEqual(parser.errors,
                         ["foo:2: error: Unknown member type 'MyBadType'",
                          "foo:6: error: Unknown member type 'MyBadType2'",
                          "foo:8: error: Unknown member type 'MyBadType'"])

    # Error - redefinition of struct
    def test_spec_error_struct_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString("""\
struct Foo
    int a

enum Foo
    A
    B
""")
            self.fail()
        except SpecParserError:
            pass
        except:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        self.assertEnumByName(parser, "Foo", ("A", "B"))

        # Check errors
        self.assertEqual(parser.errors,
                         [":4: error: Redefinition of type 'Foo'"])

    # Error - redefinition of enum
    def test_spec_error_enum_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString("""\
enum Foo
    A
    B

struct Foo
    int a
""")
            self.fail()
        except SpecParserError:
            pass
        except:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        self.assertStructByName(parser, "Foo",
                                (("a", TypeInt, False),))

        # Check errors
        self.assertEqual(parser.errors,
                         [":5: error: Redefinition of type 'Foo'"])

    # Error - redefinition of user type
    def test_spec_error_action_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString("""\
action MyAction
    input
        int a

action MyAction
    input
        string b
""")
            self.fail()
        except SpecParserError:
            pass
        except:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 0)
        self.assertEqual(len(parser.actions), 1)

        # Check actions
        self.assertAction(parser, "MyAction",
                          (("b", TypeString, False),),
                          (),
                          ())

        # Check errors
        self.assertEqual(parser.errors,
                         [":5: error: Redefinition of action 'MyAction'"])

    # Error - invalid action section usage
    def test_spec_error_action_section(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString("""\
action MyAction

struct MyStruct
    int a

    input
    output
    errors

input
output
errors
""")
            self.fail()
        except SpecParserError:
            pass
        except:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 6)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 1)

        # Check types
        self.assertStructByName(parser, "MyStruct",
                                (("a", TypeInt, False),))

        # Check actions
        self.assertAction(parser, "MyAction", (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [":6: error: Action section outside of action scope",
                          ":7: error: Action section outside of action scope",
                          ":8: error: Action section outside of action scope",
                          ":10: error: Syntax error",
                          ":11: error: Syntax error",
                          ":12: error: Syntax error"])

    # Error - member definition outside struct scope
    def test_spec_error_member(self):

        # Parse spec string
        parser = SpecParser()
        parser.parseString("""\
action MyAction
    int abc

struct MyStruct

enum MyEnum

    int bcd

int cde
""")

        # Check counts
        self.assertEqual(len(parser.errors), 3)
        self.assertEqual(len(parser.types), 2)
        self.assertEqual(len(parser.actions), 1)

        # Check types
        self.assertStructByName(parser, "MyStruct", ())
        self.assertEnumByName(parser, "MyEnum", ())

        # Check actions
        self.assertAction(parser, "MyAction", (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [":2: error: Member outside of struct scope",
                          ":8: error: Member outside of struct scope",
                          ":10: error: Syntax error"])

    # Error - enum value definition outside enum scope
    def test_spec_error_member(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString("""\
enum MyEnum
Value1

struct MyStruct

    Value2

action MyAction
    input
        MyError
""")
            self.fail()
        except SpecParserError:
            pass
        except:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 3)
        self.assertEqual(len(parser.types), 2)
        self.assertEqual(len(parser.actions), 1)

        # Check types
        self.assertStructByName(parser, "MyStruct", ())
        self.assertEnumByName(parser, "MyEnum", ())

        # Check actions
        self.assertAction(parser, "MyAction", (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [":2: error: Syntax error",
                          ":6: error: Enumeration value outside of enum scope",
                          ":10: error: Enumeration value outside of enum scope"])

    # Test valid attribute usage
    def test_spec_attributes(self):

        # Parse spec string
        parser = SpecParser()
        parser.parseString("""\
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
""", fileName = "foo")
        s = parser.types["MyStruct"]

        # Check counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check struct members
        self.assertStructByName(parser, "MyStruct",
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
    def test_spec_error_attributes(self):

        def checkFail(errors, spec):
            parser = SpecParser()
            try:
                parser.parseString(spec)
                self.fail()
            except SpecParserError:
                pass
            except:
                self.fail()
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

        # Member definition outside of struct scope
        checkFail([":1: error: Member definition outside of struct scope",
                   ":5: error: Member definition outside of struct scope"],
                  """\
    string a

enum MyEnum
    Foo
    int b
""")

        # Member redefinition
        checkFail([":4: error: Redefinition of member 'b'"],
                  """\
struct MyStruct
    string b
    int a
    float b
""")

        # Duplicate enumeration value
        checkFail([":4: error: Duplicate enumeration value 'bar'"],
                  """\
enum MyEnum
    bar
    foo
    bar
""")

    # Test documentation comments
    def test_spec_doc(self):

        # Parse spec string
        parser = SpecParser()
        parser.parseString("""\
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
""")
        self.assertEqual(len(parser.errors), 0)

        # Check documentation comments
        self.assertEqual(parser.types["MyEnum"].doc,
                         ["My enum"])
        self.assertEqual(parser.types["MyEnum"].values[0].doc,
                         ["MyEnum value 1"])
        self.assertEqual(parser.types["MyEnum"].values[1].doc,
                         ["", "MyEnum value 2", "", "Second line", ""])
        self.assertEqual(parser.types["MyEnum2"].doc,
                         [])
        self.assertEqual(parser.types["MyEnum2"].values[0].doc,
                         [])
        self.assertEqual(parser.types["MyStruct"].doc,
                         ["My struct"])
        self.assertEqual(parser.types["MyStruct"].members[0].doc,
                         ["MyStruct member a"])
        self.assertEqual(parser.types["MyStruct"].members[1].doc,
                         ["", "MyStruct member b", ""])
        self.assertEqual(parser.types["MyStruct2"].doc,
                         [])
        self.assertEqual(parser.types["MyStruct2"].members[0].doc,
                         [])
        self.assertEqual(parser.actions["MyAction"].doc,
                         ["My action"])
        self.assertEqual(parser.actions["MyAction"].inputType.doc,
                         [])
        self.assertEqual(parser.actions["MyAction"].inputType.members[0].doc,
                         ["My input member"])
        self.assertEqual(parser.actions["MyAction"].outputType.doc,
                         [])
        self.assertEqual(parser.actions["MyAction"].outputType.members[0].doc,
                         ["My output member"])
