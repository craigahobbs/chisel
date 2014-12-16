#
# Copyright (C) 2012-2014 Craig Hobbs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from chisel import SpecParser, SpecParserError
import chisel.compat
import chisel.model

import unittest


# Spec parser unit tests
class TestSpecParseSpec(unittest.TestCase):

    # Helper method to assert struct type member properties
    def assertStruct(self, structType, members):
        self.assertTrue(isinstance(structType, chisel.model.TypeStruct))
        self.assertEqual(len(structType.members), len(members))
        for ixMember in chisel.compat.xrange_(0, len(members)):
            name, typeOrType, isOptional = members[ixMember]
            self.assertEqual(structType.members[ixMember].name, name)
            if isinstance(typeOrType, (chisel.model.TypeStruct,
                                       chisel.model.TypeArray,
                                       chisel.model.TypeDict,
                                       chisel.model.TypeEnum)):
                self.assertTrue(structType.members[ixMember].type is typeOrType, (structType.members[ixMember].name, structType.members[ixMember].type, ixMember))
            else:
                self.assertTrue(isinstance(structType.members[ixMember].type, typeOrType))
            self.assertEqual(structType.members[ixMember].isOptional, isOptional)

    # Helper method to assert struct type member properties (by struct name)
    def assertStructByName(self, parser, typeName, members):
        self.assertEqual(parser.types[typeName].typeName, typeName)
        self.assertStruct(parser.types[typeName], members)

    # Helper method to assert enum type values
    def assertEnum(self, enumType, values):
        self.assertTrue(isinstance(enumType, chisel.model.TypeEnum))
        self.assertEqual(len(enumType.values), len(values))
        for enumValue in values:
            self.assertTrue(enumValue in enumType.values)

    # Helper method to assert enum type values (by enum name)
    def assertEnumByName(self, parser, typeName, values):
        self.assertEqual(parser.types[typeName].typeName, typeName)
        self.assertEnum(parser.types[typeName], values)

    # Helper method to assert action properties
    def assertAction(self, parser, actionName, inputMembers, outputMembers, errorValues):
        self.assertEqual(parser.actions[actionName].inputType.typeName, actionName + '_Input')
        self.assertEqual(parser.actions[actionName].outputType.typeName, actionName + '_Output')
        self.assertEqual(parser.actions[actionName].errorType.typeName, actionName + '_Error')
        self.assertStruct(parser.actions[actionName].inputType, inputMembers)
        self.assertStruct(parser.actions[actionName].outputType, outputMembers)
        self.assertEnum(parser.actions[actionName].errorType, errorValues)


    # Test valid spec parsing
    def test_spec_simple(self):

        # Parse the spec
        parser = SpecParser()
        parser.parseString('''\
# This is an enum
enum MyEnum
    Foo
    Bar
    "Foo and Bar"

# This is the struct
struct MyStruct

    # The 'a' member
    string a

    # The 'b' member
    int b

# This is the second struct
struct MyStruct2
    int a
    optional \\
        float b
    string c
    bool d
    int[] e
    optional MyStruct[] f
    optional float{} g
    optional datetime h
    optional uuid i
    optional MyEnum : MyStruct{} j

# This is a union
union MyUnion
    int a
    string b

# The action
action MyAction
    input
        int a
        optional string b
    output
        bool c
    errors
        Error1
        Error2
        "Error 3"

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
''')

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 4)
        self.assertEqual(len(parser.actions), 4)

        # Check enum types
        self.assertEnumByName(parser, 'MyEnum',
                              ('Foo',
                               'Bar',
                               'Foo and Bar'))

        # Check struct types
        self.assertStructByName(parser, 'MyStruct',
                                (('a', chisel.model._TypeString, False),
                                 ('b', chisel.model._TypeInt, False)))
        self.assertStructByName(parser, 'MyStruct2',
                                (('a', chisel.model._TypeInt, False),
                                 ('b', chisel.model._TypeFloat, True),
                                 ('c', chisel.model._TypeString, False),
                                 ('d', chisel.model._TypeBool, False),
                                 ('e', chisel.model.TypeArray, False),
                                 ('f', chisel.model.TypeArray, True),
                                 ('g', chisel.model.TypeDict, True),
                                 ('h', chisel.model._TypeDatetime, True),
                                 ('i', chisel.model._TypeUuid, True),
                                 ('j', chisel.model.TypeDict, True)))
        self.assertStructByName(parser, 'MyUnion',
                                (('a', chisel.model._TypeInt, True),
                                 ('b', chisel.model._TypeString, True)))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[4].type.type, chisel.model._TypeInt))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[5].type.type, chisel.model.TypeStruct))
        self.assertEqual(parser.types['MyStruct2'].members[5].type.type.typeName, 'MyStruct')
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[6].type.type, chisel.model._TypeFloat))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[9].type.type, chisel.model.TypeStruct))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[9].type.keyType, chisel.model.TypeEnum))

        # Check actions
        self.assertAction(parser, 'MyAction',
                          (('a', chisel.model._TypeInt, False),
                           ('b', chisel.model._TypeString, True)),
                          (('c', chisel.model._TypeBool, False),),
                          ('Error1',
                           'Error2',
                           'Error 3'))
        self.assertAction(parser, 'MyAction2',
                          (('foo', parser.types['MyStruct'], False),
                           ('bar', chisel.model.TypeArray, False)),
                          (),
                          ())
        self.assertTrue(isinstance(parser.actions['MyAction2'].inputType.members[1].type.type, chisel.model.TypeStruct))
        self.assertEqual(parser.actions['MyAction2'].inputType.members[1].type.type.typeName, 'MyStruct2')
        self.assertAction(parser, 'MyAction3',
                          (),
                          (('a', chisel.model._TypeInt, False),
                           ('b', chisel.model._TypeDatetime, False)),
                          ())
        self.assertAction(parser, 'MyAction4',
                          (),
                          (),
                          ())


    # Test multiple parse calls per parser instance
    def test_spec_multiple(self):

        # Parse spec strings
        parser = SpecParser()
        parser.parseString('''\
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
''', finalize = False)
        parser.parseString('''\
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
''')

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 4)
        self.assertEqual(len(parser.actions), 2)

        # Check enum types
        self.assertEnumByName(parser, 'MyEnum',
                              ('A',
                               'B'))
        self.assertEnumByName(parser, 'MyEnum2',
                              ('C',
                               'D'))

        # Check struct types
        self.assertStructByName(parser, 'MyStruct',
                                (('c', chisel.model._TypeString, False),
                                 ('d', parser.types['MyEnum2'], False),
                                 ('e', parser.types['MyStruct2'], False)))
        self.assertStructByName(parser, 'MyStruct2',
                                (('f', chisel.model._TypeString, False),
                                 ('g', parser.types['MyEnum2'], False)))

        # Check actions
        self.assertAction(parser, 'MyAction',
                          (('a', chisel.model.TypeStruct, False),),
                          (('b', chisel.model.TypeStruct, False),
                           ('c', parser.types['MyEnum2'], False)),
                          ())
        self.assertEqual(parser.actions['MyAction'].inputType.members[0].type.typeName, 'MyStruct2')
        self.assertEqual(parser.actions['MyAction'].outputType.members[0].type.typeName, 'MyStruct')
        self.assertAction(parser, 'MyAction2',
                          (('d', chisel.model.TypeStruct, False),),
                          (('e', chisel.model.TypeStruct, False),),
                          ())
        self.assertEqual(parser.actions['MyAction2'].inputType.members[0].type.typeName, 'MyStruct')
        self.assertEqual(parser.actions['MyAction2'].outputType.members[0].type.typeName, 'MyStruct2')


    # Test multiple finalize
    def test_spec_multiple_finalize(self):

        # Parse spec strings
        parser = SpecParser()
        parser.parseString('''\
struct MyStruct
    MyEnum a

enum MyEnum
    A
    B
''')
        parser.parseString('''\
struct MyStruct2
    int a
    MyEnum b
    MyEnum2 c

enum MyEnum2
    C
    D
''')

        # Check enum types
        self.assertEnumByName(parser, 'MyEnum',
                              ('A',
                               'B'))
        self.assertEnumByName(parser, 'MyEnum2',
                              ('C',
                               'D'))

        # Check struct types
        self.assertStructByName(parser, 'MyStruct',
                                (('a', parser.types['MyEnum'], False),))
        self.assertStructByName(parser, 'MyStruct2',
                                (('a', chisel.model._TypeInt, False),
                                 ('b', parser.types['MyEnum'], False),
                                 ('c', parser.types['MyEnum2'], False)))


    def test_spec_typeref_array_attr(self):

        parser = SpecParser()
        parser.parseString('''\
struct MyStruct
    MyStruct2[len > 0] a
struct MyStruct2
''')

        self.assertStructByName(parser, 'MyStruct',
                                (('a', chisel.model.TypeArray, False),))
        self.assertTrue(parser.types['MyStruct'].members[0].type.type is parser.types['MyStruct2'])
        self.assertTrue(parser.types['MyStruct'].members[0].type.attr is None)
        self.assertTrue(parser.types['MyStruct'].members[0].attr is not None)

        self.assertStructByName(parser, 'MyStruct2', ())


    def test_spec_typeref_dict_attr(self):

        parser = SpecParser()
        parser.parseString('''\
struct MyStruct
    MyEnum : MyStruct2{len > 0} a
enum MyEnum
struct MyStruct2
''')

        self.assertStructByName(parser, 'MyStruct',
                                (('a', chisel.model.TypeDict, False),))
        self.assertTrue(parser.types['MyStruct'].members[0].type.type is parser.types['MyStruct2'])
        self.assertTrue(parser.types['MyStruct'].members[0].type.attr is None)
        self.assertTrue(parser.types['MyStruct'].members[0].type.keyType is parser.types['MyEnum'])
        self.assertTrue(parser.types['MyStruct'].members[0].type.keyAttr is None)
        self.assertTrue(parser.types['MyStruct'].members[0].attr is not None)

        self.assertStructByName(parser, 'MyStruct2', ())


    def test_spec_typeref_invalid_attr(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
struct MyStruct
    MyStruct2(len > 0) a
struct MyStruct2
''')
        except SpecParserError as e:
            self.assertEqual(str(e), """\
:2: error: Invalid attribute 'len > 0'""")
        else:
            self.fail()


    # Test members referencing unknown user types
    def test_spec_error_unknown_type(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString('''\
struct Foo
    MyBadType a

action MyAction
    input
        MyBadType2 a
    output
        MyBadType b
''', fileName = 'foo')
        except SpecParserError as e:
            self.assertEqual(str(e), """\
foo:2: error: Unknown member type 'MyBadType'
foo:6: error: Unknown member type 'MyBadType2'
foo:8: error: Unknown member type 'MyBadType'""")
        else:
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
            parser.parseString('''\
struct Foo
    int a

enum Foo
    A
    B
''')
        except SpecParserError as e:
            self.assertEqual(str(e), ":4: error: Redefinition of type 'Foo'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        self.assertEnumByName(parser, 'Foo', ('A', 'B'))

        # Check errors
        self.assertEqual(parser.errors,
                         [":4: error: Redefinition of type 'Foo'"])


    # Error - redefinition of enum
    def test_spec_error_enum_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString('''\
enum Foo
    A
    B

struct Foo
    int a
''')
        except SpecParserError as e:
            self.assertEqual(str(e), ":5: error: Redefinition of type 'Foo'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        self.assertStructByName(parser, 'Foo',
                                (('a', chisel.model._TypeInt, False),))

        # Check errors
        self.assertEqual(parser.errors,
                         [":5: error: Redefinition of type 'Foo'"])


    # Error - redefinition of typedef
    def test_spec_error_typedef_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString('''\
struct Foo
    int a

typedef int(> 5) Foo
''')
        except SpecParserError as e:
            self.assertEqual(str(e), ":4: error: Redefinition of type 'Foo'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        typedef = parser.types['Foo']
        self.assertTrue(isinstance(typedef, chisel.model.Typedef))
        self.assertEqual(typedef.typeName, 'Foo')
        self.assertEqual(typedef.doc, [])
        self.assertTrue(isinstance(typedef.type, chisel.model._TypeInt))
        self.assertEqual(self.attrTuple(typedef.attr), self.attrTuple(gt = 5))

        # Check errors
        self.assertEqual(parser.errors,
                         [":4: error: Redefinition of type 'Foo'"])


    # Error - redefinition of user type
    def test_spec_error_action_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString('''\
action MyAction
    input
        int a

action MyAction
    input
        string b
''')
        except SpecParserError as e:
            self.assertEqual(str(e), ":5: error: Redefinition of action 'MyAction'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 0)
        self.assertEqual(len(parser.actions), 1)

        # Check actions
        self.assertAction(parser, 'MyAction',
                          (('b', chisel.model._TypeString, False),),
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
            parser.parseString('''\
action MyAction

struct MyStruct
    int a

    input
    output
    errors

input
output
errors
''')
        except SpecParserError as e:
            self.assertEqual(str(e), '''\
:6: error: Action section outside of action scope
:7: error: Action section outside of action scope
:8: error: Action section outside of action scope
:10: error: Syntax error
:11: error: Syntax error
:12: error: Syntax error''')
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 6)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 1)

        # Check types
        self.assertStructByName(parser, 'MyStruct',
                                (('a', chisel.model._TypeInt, False),))

        # Check actions
        self.assertAction(parser, 'MyAction', (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [':6: error: Action section outside of action scope',
                          ':7: error: Action section outside of action scope',
                          ':8: error: Action section outside of action scope',
                          ':10: error: Syntax error',
                          ':11: error: Syntax error',
                          ':12: error: Syntax error'])


    # Error - member definition outside struct scope
    def test_spec_error_member(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString('''\
action MyAction
    int abc

struct MyStruct

enum MyEnum

    int bcd

int cde
''')
        except SpecParserError as e:
            self.assertEqual(str(e), '''\
:2: error: Member definition outside of struct scope
:8: error: Member definition outside of struct scope
:10: error: Syntax error''')
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 3)
        self.assertEqual(len(parser.types), 2)
        self.assertEqual(len(parser.actions), 1)

        # Check types
        self.assertStructByName(parser, 'MyStruct', ())
        self.assertEnumByName(parser, 'MyEnum', ())

        # Check actions
        self.assertAction(parser, 'MyAction', (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [':2: error: Member definition outside of struct scope',
                          ':8: error: Member definition outside of struct scope',
                          ':10: error: Syntax error'])


    # Error - enum value definition outside enum scope
    def test_spec_error_enum(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parseString('''\
enum MyEnum
    "abc
    abc"
Value1

struct MyStruct

    Value2

action MyAction
    input
        MyError
''')
        except SpecParserError as e:
            self.assertEqual(str(e), '''\
:2: error: Syntax error
:3: error: Syntax error
:4: error: Syntax error
:8: error: Enumeration value outside of enum scope
:12: error: Enumeration value outside of enum scope''')
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 5)
        self.assertEqual(len(parser.types), 2)
        self.assertEqual(len(parser.actions), 1)

        # Check types
        self.assertStructByName(parser, 'MyStruct', ())
        self.assertEnumByName(parser, 'MyEnum', ())

        # Check actions
        self.assertAction(parser, 'MyAction', (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [':2: error: Syntax error',
                          ':3: error: Syntax error',
                          ':4: error: Syntax error',
                          ':8: error: Enumeration value outside of enum scope',
                          ':12: error: Enumeration value outside of enum scope'])


    @staticmethod
    def attrTuple(attr = None, eq = None, lt = None, lte = None, gt = None, gte = None,
                  len_eq = None, len_lt = None, len_lte = None, len_gt = None, len_gte = None):
        return (attr.eq if attr else eq,
                attr.lt if attr else lt,
                attr.lte if attr else lte,
                attr.gt if attr else gt,
                attr.gte if attr else gte,
                attr.len_eq if attr else len_eq,
                attr.len_lt if attr else len_lt,
                attr.len_lte if attr else len_lte,
                attr.len_gt if attr else len_gt,
                attr.len_gte if attr else len_gte)


    # Test valid attribute usage
    def test_spec_attributes(self):

        # Parse spec string
        parser = SpecParser()
        parser.parseString('''\
struct MyStruct
    optional int(> 1,<= 10.5) i1
    optional int (>= 1, < 10 ) i2
    int( > 0, <= 10) i3
    int(> -4, < -1.4) i4
    int(== 5) i5
    float( > 1, <= 10.5) f1
    float(>= 1.5, < 10 ) f2
    string(len > 5, len < 101) s1
    string( len >= 5, len <= 100 ) s2
    string( len == 2 ) s3
    int(> 5)[] ai1
    string(len < 5)[len < 10] as1
    string(len == 2)[len == 3] as2
    int(< 15){} di1
    string(len > 5){len > 10} ds1
    string(len == 2){len == 3} ds2
    string(len == 1) : string(len == 2){len == 3} ds3
''', fileName = 'foo')
        s = parser.types['MyStruct']

        # Check counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check struct members
        self.assertStructByName(parser, 'MyStruct',
                                (('i1', chisel.model._TypeInt, True),
                                 ('i2', chisel.model._TypeInt, True),
                                 ('i3', chisel.model._TypeInt, False),
                                 ('i4', chisel.model._TypeInt, False),
                                 ('i5', chisel.model._TypeInt, False),
                                 ('f1', chisel.model._TypeFloat, False),
                                 ('f2', chisel.model._TypeFloat, False),
                                 ('s1', chisel.model._TypeString, False),
                                 ('s2', chisel.model._TypeString, False),
                                 ('s3', chisel.model._TypeString, False),
                                 ('ai1', chisel.model.TypeArray, False),
                                 ('as1', chisel.model.TypeArray, False),
                                 ('as2', chisel.model.TypeArray, False),
                                 ('di1', chisel.model.TypeDict, False),
                                 ('ds1', chisel.model.TypeDict, False),
                                 ('ds2', chisel.model.TypeDict, False),
                                 ('ds3', chisel.model.TypeDict, False),
                                 ))

        # Check i1 constraints
        itm = iter(s.members)
        i1 = next(itm)
        self.assertEqual(self.attrTuple(i1.attr), self.attrTuple(lte = 10.5, gt = 1))

        # Check i2 constraints
        i2 = next(itm)
        self.assertEqual(self.attrTuple(i2.attr), self.attrTuple(lt = 10, gte = 1))

        # Check i3 constraints
        i3 = next(itm)
        self.assertEqual(self.attrTuple(i3.attr), self.attrTuple(lte = 10, gt = 0))

        # Check i4 constraints
        i4 = next(itm)
        self.assertEqual(self.attrTuple(i4.attr), self.attrTuple(lt = -1.4, gt = -4))

        # Check i4 constraints
        i4 = next(itm)
        self.assertEqual(self.attrTuple(i4.attr), self.attrTuple(eq = 5))

        # Check f1 constraints
        f1 = next(itm)
        self.assertEqual(self.attrTuple(f1.attr), self.attrTuple(lte = 10.5, gt = 1))

        # Check f2 constraints
        f2 = next(itm)
        self.assertEqual(self.attrTuple(f2.attr), self.attrTuple(lt = 10, gte = 1.5))

        # Check s1 constraints
        s1 = next(itm)
        self.assertEqual(self.attrTuple(s1.attr), self.attrTuple(len_lt = 101, len_gt = 5))

        # Check s2 constraints
        s2 = next(itm)
        self.assertEqual(self.attrTuple(s2.attr), self.attrTuple(len_lte = 100, len_gte = 5))

        # Check s3 constraints
        s3 = next(itm)
        self.assertEqual(self.attrTuple(s3.attr), self.attrTuple(len_eq = 2))

        # Check ai1 constraints
        ai1 = next(itm)
        self.assertEqual(ai1.attr, None)
        self.assertEqual(self.attrTuple(ai1.type.attr), self.attrTuple(gt = 5))

        # Check as1 constraints
        as1 = next(itm)
        self.assertEqual(self.attrTuple(as1.attr), self.attrTuple(len_lt = 10))
        self.assertEqual(self.attrTuple(as1.type.attr), self.attrTuple(len_lt = 5))

        # Check as2 constraints
        as2 = next(itm)
        self.assertEqual(self.attrTuple(as2.attr), self.attrTuple(len_eq = 3))
        self.assertEqual(self.attrTuple(as2.type.attr), self.attrTuple(len_eq = 2))

        # Check di1 constraints
        di1 = next(itm)
        self.assertEqual(di1.attr, None)
        self.assertEqual(self.attrTuple(di1.type.attr), self.attrTuple(lt = 15))

        # Check ds1 constraints
        ds1 = next(itm)
        self.assertEqual(self.attrTuple(ds1.attr), self.attrTuple(len_gt = 10))
        self.assertEqual(self.attrTuple(ds1.type.attr), self.attrTuple(len_gt = 5))

        # Check ds2 constraints
        ds2 = next(itm)
        self.assertEqual(self.attrTuple(ds2.attr), self.attrTuple(len_eq = 3))
        self.assertEqual(self.attrTuple(ds2.type.attr), self.attrTuple(len_eq = 2))

        # Check ds3 constraints
        ds3 = next(itm)
        self.assertEqual(self.attrTuple(ds3.attr), self.attrTuple(len_eq = 3))
        self.assertEqual(self.attrTuple(ds3.type.attr), self.attrTuple(len_eq = 2))
        self.assertEqual(self.attrTuple(ds3.type.keyAttr), self.attrTuple(len_eq = 1))

        self.assertEqual(next(itm, None), None)


    def _test_spec_error(self, errors, spec):
        parser = SpecParser()
        try:
            parser.parseString(spec)
        except SpecParserError as e:
            self.assertEqual(str(e), '\n'.join(errors))
        else:
            self.fail()
        self.assertEqual(len(parser.errors), len(errors))
        self.assertEqual(parser.errors, errors)


    def test_spec_error_attribute_eq(self):
        self._test_spec_error([":2: error: Invalid attribute '== 7'"], '''\
struct MyStruct
    string(== 7) s
''')


    def test_spec_error_attribute_lt(self):
        self._test_spec_error([":2: error: Invalid attribute '< 7'"], '''\
struct MyStruct
    string(< 7) s
''')


    def test_spec_error_attribute_gt(self):
        self._test_spec_error([":2: error: Invalid attribute '> 7'"], '''\
struct MyStruct
    string(> 7) s
''')


    def test_spec_error_attribute_lt_gt(self):
        self._test_spec_error([":2: error: Invalid attribute '< 7'"], '''\
struct MyStruct
    string(< 7, > 7) s
''')


    def test_spec_error_attribute_lte_gte(self):
        self._test_spec_error([":6: error: Invalid attribute '>= 1'",
                               ":7: error: Invalid attribute '<= 2'"], '''\
enum MyEnum
    Foo
    Bar

struct MyStruct
    MyStruct(>= 1) a
    MyEnum(<= 2) b
''')


    def test_spec_error_attribute_len_eq(self):
        self._test_spec_error([":2: error: Invalid attribute 'len == 1'"], '''\
struct MyStruct
    int(len == 1) i
''')


    def test_spec_error_attribute_len_lt(self):
        self._test_spec_error([":2: error: Invalid attribute 'len < 10'"], '''\
struct MyStruct
    float(len < 10) f
''')


    def test_spec_error_attribute_len_gt(self):
        self._test_spec_error([":2: error: Invalid attribute 'len > 1'"], '''\
struct MyStruct
    int(len > 1) i
''')


    def test_spec_error_attribute_len_lt_gt(self):
        self._test_spec_error([":2: error: Invalid attribute 'len < 10'"], '''\
struct MyStruct
    float(len < 10, len > 10) f
''')


    def test_spec_error_attribute_len_lte_gte(self):
        self._test_spec_error([":2: error: Invalid attribute 'len <= 10'",
                               ":3: error: Invalid attribute 'len >= 10'"], '''\
struct MyStruct
    float(len <= 10) f
    float(len >= 10) f2
''')


    def test_spec_error_attribute_invalid(self):
        self._test_spec_error([':2: error: Syntax error'], '''\
struct MyStruct
    string(regex="abc") a
''')


    def test_spec_error_member_invalid(self):
        self._test_spec_error([':1: error: Member definition outside of struct scope',
                               ':5: error: Member definition outside of struct scope'], '''\
    string a

enum MyEnum
    Foo
    int b
''')


    def test_spec_error_member_redefinition(self):
        self._test_spec_error([":4: error: Redefinition of member 'b'"], '''\
struct MyStruct
    string b
    int a
    float b
''')


    def test_spec_error_enum_duplicate_value(self):
        self._test_spec_error([":4: error: Duplicate enumeration value 'bar'"], '''\
enum MyEnum
    bar
    foo
    bar
''')


    def test_spec_doc(self):

        # Parse spec string
        parser = SpecParser()
        parser.parseString('''\
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
''')
        self.assertEqual(len(parser.errors), 0)

        # Check documentation comments
        self.assertEqual(parser.types['MyEnum'].doc,
                         ['My enum'])
        self.assertEqual(parser.types['MyEnum'].values[0].doc,
                         ['MyEnum value 1'])
        self.assertEqual(parser.types['MyEnum'].values[1].doc,
                         ['', 'MyEnum value 2', '', 'Second line', ''])
        self.assertEqual(parser.types['MyEnum2'].doc,
                         [])
        self.assertEqual(parser.types['MyEnum2'].values[0].doc,
                         [])
        self.assertEqual(parser.types['MyStruct'].doc,
                         ['My struct'])
        self.assertEqual(parser.types['MyStruct'].members[0].doc,
                         ['MyStruct member a'])
        self.assertEqual(parser.types['MyStruct'].members[1].doc,
                         ['', 'MyStruct member b', ''])
        self.assertEqual(parser.types['MyStruct2'].doc,
                         [])
        self.assertEqual(parser.types['MyStruct2'].members[0].doc,
                         [])
        self.assertEqual(parser.actions['MyAction'].doc,
                         ['My action'])
        self.assertEqual(parser.actions['MyAction'].inputType.doc,
                         [])
        self.assertEqual(parser.actions['MyAction'].inputType.members[0].doc,
                         ['My input member'])
        self.assertEqual(parser.actions['MyAction'].outputType.doc,
                         [])
        self.assertEqual(parser.actions['MyAction'].outputType.members[0].doc,
                         ['My output member'])


    def test_spec_typedef(self):

        parser = SpecParser()
        parser.parseString('''\
typedef MyEnum MyTypedef2

enum MyEnum
    A
    B

# My typedef
typedef MyEnum : MyStruct{len > 0} MyTypedef

struct MyStruct
    int a
    optional int b
''')

        self.assertEqual(len(parser.types), 4)

        typedef = parser.types['MyTypedef']
        self.assertTrue(isinstance(typedef, chisel.model.Typedef))
        self.assertEqual(typedef.typeName, 'MyTypedef')
        self.assertEqual(typedef.doc, ['My typedef'])
        self.assertTrue(isinstance(typedef.type, chisel.model.TypeDict))
        self.assertEqual(self.attrTuple(typedef.attr), self.attrTuple(len_gt = 0))
        self.assertTrue(typedef.type.keyType is parser.types['MyEnum'])
        self.assertEqual(typedef.type.keyType.doc, [])
        self.assertEqual(len(typedef.type.keyType.values), 2)
        self.assertTrue(typedef.type.type is parser.types['MyStruct'])
        self.assertEqual(typedef.type.type.doc, [])
        self.assertEqual(len(typedef.type.type.members), 2)

        typedef2 = parser.types['MyTypedef2']
        self.assertTrue(isinstance(typedef2, chisel.model.Typedef))
        self.assertEqual(typedef2.typeName, 'MyTypedef2')
        self.assertEqual(typedef2.doc, [])
        self.assertTrue(typedef2.type is parser.types['MyEnum'])
        self.assertEqual(typedef2.attr, None)


    def test_spec_error_dict_nonStringKey(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
struct Foo
    int : int {} a
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid dictionary key type',
            ])
        else:
            self.fail()


    def test_spec_error_action_inputRedefinition(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action Foo
    input
        int a
    output
        int b
    input
        int c
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':6: error: Redefinition of action input',
                ':7: error: Member definition outside of struct scope',
            ])
        else:
            self.fail()


    def test_spec_error_action_outputRedefinition(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action Foo
    output
        int a
    input
        int b
    output
        int c
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':6: error: Redefinition of action output',
                ':7: error: Member definition outside of struct scope',
            ])
        else:
            self.fail()


    def test_spec_error_action_errorsRedefinition(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action Foo
    errors
        A
        B
    input
        int a
    errors
        C
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':7: error: Redefinition of action errors',
                ':8: error: Enumeration value outside of enum scope',
            ])
        else:
            self.fail()


    def test_spec_action_input_struct(self):

        parser = SpecParser()
        parser.parseString('''\
struct Foo
    int a
    int b

action FooAction
    input Foo
''')
        self.assertTrue(parser.actions['FooAction'].inputType, parser.types['Foo'])


    def test_spec_action_input_typedef(self):

        parser = SpecParser()
        parser.parseString('''\
struct Bar
    int a
    int b

typedef Bar Foo

action FooAction
    input Foo
''')
        self.assertTrue(parser.actions['FooAction'].inputType, parser.types['Foo'])


    def test_spec_action_input_type_nonStruct(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action FooAction
    input Foo

enum Foo
    A
    B
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid action input type',
            ])
        else:
            self.fail()


    def test_spec_action_input_type_typedef_nonStruct(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action FooAction
    input Foo

enum Bar
    A
    B

typedef Bar Foo
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid action input type',
            ])
        else:
            self.fail()


    def test_spec_action_output_struct(self):

        parser = SpecParser()
        parser.parseString('''\
struct Foo
    int a
    int b

action FooAction
    output Foo
''')
        self.assertTrue(parser.actions['FooAction'].outputType, parser.types['Foo'])


    def test_spec_action_output_typedef(self):

        parser = SpecParser()
        parser.parseString('''\
struct Bar
    int a
    int b

typedef Bar Foo

action FooAction
    output Foo
''')
        self.assertTrue(parser.actions['FooAction'].outputType, parser.types['Foo'])


    def test_spec_action_output_nonStruct(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action FooAction
    output Foo

enum Foo
    A
    B
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid action output type',
            ])
        else:
            self.fail()


    def test_spec_action_output_typedef_nonStruct(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action FooAction
    output Foo

enum Bar
    A
    B

typedef Bar Foo
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid action output type',
            ])
        else:
            self.fail()


    def test_spec_action_errors_enum(self):

        parser = SpecParser()
        parser.parseString('''\
enum Foo
    A
    B

action FooAction
    errors Foo
''')
        self.assertTrue(parser.actions['FooAction'].errorType, parser.types['Foo'])


    def test_spec_action_errors_typedef(self):

        parser = SpecParser()
        parser.parseString('''\
action FooAction
    errors Foo

enum Bar
    A
    B

typedef Bar Foo
''')
        self.assertTrue(parser.actions['FooAction'].errorType, parser.types['Foo'])


    def test_spec_action_errors_nonEnum(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action FooAction
    errors Foo

struct Foo
    int a
    int b
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid action errors type',
            ])
        else:
            self.fail()


    def test_spec_action_errors_typedef_nonEnum(self):

        parser = SpecParser()
        try:
            parser.parseString('''\
action FooAction
    errors Foo

struct Bar
    int a
    int b

typedef Bar Foo
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid action errors type',
            ])
        else:
            self.fail()
