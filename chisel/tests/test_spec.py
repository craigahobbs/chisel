#
# Copyright (C) 2012-2016 Craig Hobbs
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

import unittest

from chisel import SpecParser, SpecParserError
import chisel.compat
import chisel.model


class TestSpecParseSpec(unittest.TestCase): # pylint: disable=protected-access

    # Helper method to assert struct type member properties
    def assert_struct(self, struct_type, members):
        self.assertTrue(isinstance(struct_type, chisel.model.TypeStruct))
        self.assertEqual(len(struct_type.members), len(members))
        for ix_member in chisel.compat.xrange_(0, len(members)):
            name, type_, optional = members[ix_member]
            self.assertEqual(struct_type.members[ix_member].name, name)
            if isinstance(type_, (chisel.model.TypeStruct, chisel.model.TypeArray, chisel.model.TypeDict, chisel.model.TypeEnum)):
                self.assertTrue(struct_type.members[ix_member].type is type_)
            else:
                self.assertTrue(isinstance(struct_type.members[ix_member].type, type_))
            self.assertEqual(struct_type.members[ix_member].optional, optional)

    # Helper method to assert struct type member properties (by struct name)
    def assert_struct_by_name(self, parser, type_name, members):
        self.assertEqual(parser.types[type_name].type_name, type_name)
        self.assert_struct(parser.types[type_name], members)

    # Helper method to assert enum type values
    def assert_enum(self, enum_type, values):
        self.assertTrue(isinstance(enum_type, chisel.model.TypeEnum))
        self.assertEqual(len(enum_type.values), len(values))
        for enum_value in values:
            self.assertTrue(enum_value in enum_type.values)

    # Helper method to assert enum type values (by enum name)
    def assert_enum_by_name(self, parser, type_name, values):
        self.assertEqual(parser.types[type_name].type_name, type_name)
        self.assert_enum(parser.types[type_name], values)

    # Helper method to assert action properties
    def assert_action(self, parser, action_name, input_members, output_members, error_values):
        self.assertEqual(parser.actions[action_name].input_type.type_name, action_name + '_input')
        self.assertEqual(parser.actions[action_name].output_type.type_name, action_name + '_output')
        self.assertEqual(parser.actions[action_name].error_type.type_name, action_name + '_error')
        self.assert_struct(parser.actions[action_name].input_type, input_members)
        self.assert_struct(parser.actions[action_name].output_type, output_members)
        self.assert_enum(parser.actions[action_name].error_type, error_values)

    # Test valid spec parsing
    def test_simple(self):

        # Parse the spec
        parser = SpecParser()
        parser.parse_string('''\
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
    string \\
        c
    bool d
    int[] e
    optional MyStruct[] f
    optional float{} g
    optional datetime h
    optional uuid i
    optional MyEnum : MyStruct{} j
    optional date k

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
        date c

# The fourth action
action MyAction4 \\
''')

        # Check errors & counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 4)
        self.assertEqual(len(parser.actions), 4)

        # Check enum types
        self.assert_enum_by_name(parser, 'MyEnum',
                                 ('Foo',
                                  'Bar',
                                  'Foo and Bar'))

        # Check struct types
        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('a', type(chisel.model.TYPE_STRING), False),
                                    ('b', type(chisel.model.TYPE_INT), False)))
        self.assert_struct_by_name(parser, 'MyStruct2',
                                   (('a', type(chisel.model.TYPE_INT), False),
                                    ('b', type(chisel.model.TYPE_FLOAT), True),
                                    ('c', type(chisel.model.TYPE_STRING), False),
                                    ('d', type(chisel.model.TYPE_BOOL), False),
                                    ('e', chisel.model.TypeArray, False),
                                    ('f', chisel.model.TypeArray, True),
                                    ('g', chisel.model.TypeDict, True),
                                    ('h', type(chisel.model.TYPE_DATETIME), True),
                                    ('i', type(chisel.model.TYPE_UUID), True),
                                    ('j', chisel.model.TypeDict, True),
                                    ('k', type(chisel.model.TYPE_DATE), True)))
        self.assert_struct_by_name(parser, 'MyUnion',
                                   (('a', type(chisel.model.TYPE_INT), True),
                                    ('b', type(chisel.model.TYPE_STRING), True)))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[4].type.type, type(chisel.model.TYPE_INT)))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[5].type.type, chisel.model.TypeStruct))
        self.assertEqual(parser.types['MyStruct2'].members[5].type.type.type_name, 'MyStruct')
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[6].type.type, type(chisel.model.TYPE_FLOAT)))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[9].type.type, chisel.model.TypeStruct))
        self.assertTrue(isinstance(parser.types['MyStruct2'].members[9].type.key_type, chisel.model.TypeEnum))

        # Check actions
        self.assert_action(parser, 'MyAction',
                           (('a', type(chisel.model.TYPE_INT), False),
                            ('b', type(chisel.model.TYPE_STRING), True)),
                           (('c', type(chisel.model.TYPE_BOOL), False),),
                           ('Error1',
                            'Error2',
                            'Error 3'))
        self.assert_action(parser, 'MyAction2',
                           (('foo', parser.types['MyStruct'], False),
                            ('bar', chisel.model.TypeArray, False)),
                           (),
                           ())
        self.assertTrue(isinstance(parser.actions['MyAction2'].input_type.members[1].type.type, chisel.model.TypeStruct))
        self.assertEqual(parser.actions['MyAction2'].input_type.members[1].type.type.type_name, 'MyStruct2')
        self.assert_action(parser, 'MyAction3',
                           (),
                           (('a', type(chisel.model.TYPE_INT), False),
                            ('b', type(chisel.model.TYPE_DATETIME), False),
                            ('c', type(chisel.model.TYPE_DATE), False)),
                           ())
        self.assert_action(parser, 'MyAction4',
                           (),
                           (),
                           ())

    # Test multiple parse calls per parser instance
    def test_multiple(self):

        # Parse spec strings
        parser = SpecParser()
        parser.parse_string('''\
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
''', finalize=False)
        parser.parse_string('''\
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
        self.assert_enum_by_name(parser, 'MyEnum',
                                 ('A',
                                  'B'))
        self.assert_enum_by_name(parser, 'MyEnum2',
                                 ('C',
                                  'D'))

        # Check struct types
        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('c', type(chisel.model.TYPE_STRING), False),
                                    ('d', parser.types['MyEnum2'], False),
                                    ('e', parser.types['MyStruct2'], False)))
        self.assert_struct_by_name(parser, 'MyStruct2',
                                   (('f', type(chisel.model.TYPE_STRING), False),
                                    ('g', parser.types['MyEnum2'], False)))

        # Check actions
        self.assert_action(parser, 'MyAction',
                           (('a', chisel.model.TypeStruct, False),),
                           (('b', chisel.model.TypeStruct, False),
                            ('c', parser.types['MyEnum2'], False)),
                           ())
        self.assertEqual(parser.actions['MyAction'].input_type.members[0].type.type_name, 'MyStruct2')
        self.assertEqual(parser.actions['MyAction'].output_type.members[0].type.type_name, 'MyStruct')
        self.assert_action(parser, 'MyAction2',
                           (('d', chisel.model.TypeStruct, False),),
                           (('e', chisel.model.TypeStruct, False),),
                           ())
        self.assertEqual(parser.actions['MyAction2'].input_type.members[0].type.type_name, 'MyStruct')
        self.assertEqual(parser.actions['MyAction2'].output_type.members[0].type.type_name, 'MyStruct2')

    # Test multiple finalize
    def test_multiple_finalize(self):

        # Parse spec strings
        parser = SpecParser()
        parser.parse_string('''\
struct MyStruct
    MyEnum a

enum MyEnum
    A
    B
''')
        parser.parse_string('''\
struct MyStruct2
    int a
    MyEnum b
    MyEnum2 c

enum MyEnum2
    C
    D
''')

        # Check enum types
        self.assert_enum_by_name(parser, 'MyEnum',
                                 ('A',
                                  'B'))
        self.assert_enum_by_name(parser, 'MyEnum2',
                                 ('C',
                                  'D'))

        # Check struct types
        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('a', parser.types['MyEnum'], False),))
        self.assert_struct_by_name(parser, 'MyStruct2',
                                   (('a', type(chisel.model.TYPE_INT), False),
                                    ('b', parser.types['MyEnum'], False),
                                    ('c', parser.types['MyEnum2'], False)))

    def test_typeref_array_attr(self):

        parser = SpecParser()
        parser.parse_string('''\
struct MyStruct
    MyStruct2[len > 0] a
struct MyStruct2
''')

        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('a', chisel.model.TypeArray, False),))
        self.assertTrue(parser.types['MyStruct'].members[0].type.type is parser.types['MyStruct2'])
        self.assertTrue(parser.types['MyStruct'].members[0].type.attr is None)
        self.assertTrue(parser.types['MyStruct'].members[0].attr is not None)

        self.assert_struct_by_name(parser, 'MyStruct2', ())

    def test_typeref_dict_attr(self):

        parser = SpecParser()
        parser.parse_string('''\
struct MyStruct
    MyEnum : MyStruct2{len > 0} a
enum MyEnum
struct MyStruct2
''')

        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('a', chisel.model.TypeDict, False),))
        self.assertTrue(parser.types['MyStruct'].members[0].type.type is parser.types['MyStruct2'])
        self.assertTrue(parser.types['MyStruct'].members[0].type.attr is None)
        self.assertTrue(parser.types['MyStruct'].members[0].type.key_type is parser.types['MyEnum'])
        self.assertTrue(parser.types['MyStruct'].members[0].type.key_attr is None)
        self.assertTrue(parser.types['MyStruct'].members[0].attr is not None)

        self.assert_struct_by_name(parser, 'MyStruct2', ())

    def test_typeref_invalid_attr(self):

        parser = SpecParser()
        try:
            parser.parse_string('''\
struct MyStruct
    MyStruct2(len > 0) a
struct MyStruct2
''')
        except SpecParserError as exc:
            self.assertEqual(str(exc), """\
:2: error: Invalid attribute 'len > 0'""")
        else:
            self.fail()

    # Test members referencing unknown user types
    def test_error_unknown_type(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
struct Foo
    MyBadType a

action MyAction
    input
        MyBadType2 a
    output
        MyBadType b
''', filename='foo')
        except SpecParserError as exc:
            self.assertEqual(str(exc), """\
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
    def test_error_struct_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
struct Foo
    int a

enum Foo
    A
    B
''')
        except SpecParserError as exc:
            self.assertEqual(str(exc), ":4: error: Redefinition of type 'Foo'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        self.assert_enum_by_name(parser, 'Foo', ('A', 'B'))

        # Check errors
        self.assertEqual(parser.errors,
                         [":4: error: Redefinition of type 'Foo'"])

    # Error - redefinition of enum
    def test_error_enum_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
enum Foo
    A
    B

struct Foo
    int a
''')
        except SpecParserError as exc:
            self.assertEqual(str(exc), ":5: error: Redefinition of type 'Foo'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        self.assert_struct_by_name(parser, 'Foo',
                                   (('a', type(chisel.model.TYPE_INT), False),))

        # Check errors
        self.assertEqual(parser.errors,
                         [":5: error: Redefinition of type 'Foo'"])

    # Error - redefinition of typedef
    def test_error_typedef_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
struct Foo
    int a

typedef int(> 5) Foo
''')
        except SpecParserError as exc:
            self.assertEqual(str(exc), ":4: error: Redefinition of type 'Foo'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check types
        typedef = parser.types['Foo']
        self.assertTrue(isinstance(typedef, chisel.model.Typedef))
        self.assertEqual(typedef.type_name, 'Foo')
        self.assertEqual(typedef.doc, [])
        self.assertTrue(isinstance(typedef.type, type(chisel.model.TYPE_INT)))
        self.assertEqual(self.attr_tuple(typedef.attr), self.attr_tuple(op_gt=5))

        # Check errors
        self.assertEqual(parser.errors,
                         [":4: error: Redefinition of type 'Foo'"])

    # Error - redefinition of user type
    def test_error_action_redefinition(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
action MyAction
    input
        int a

action MyAction
    input
        string b
''')
        except SpecParserError as exc:
            self.assertEqual(str(exc), ":5: error: Redefinition of action 'MyAction'")
        else:
            self.fail()

        # Check counts
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(len(parser.types), 0)
        self.assertEqual(len(parser.actions), 1)

        # Check actions
        self.assert_action(parser, 'MyAction',
                           (('b', type(chisel.model.TYPE_STRING), False),),
                           (),
                           ())

        # Check errors
        self.assertEqual(parser.errors,
                         [":5: error: Redefinition of action 'MyAction'"])

    # Error - invalid action section usage
    def test_error_action_section(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
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
        except SpecParserError as exc:
            self.assertEqual(str(exc), '''\
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
        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('a', type(chisel.model.TYPE_INT), False),))

        # Check actions
        self.assert_action(parser, 'MyAction', (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [':6: error: Action section outside of action scope',
                          ':7: error: Action section outside of action scope',
                          ':8: error: Action section outside of action scope',
                          ':10: error: Syntax error',
                          ':11: error: Syntax error',
                          ':12: error: Syntax error'])

    # Error - member definition outside struct scope
    def test_error_member(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
action MyAction
    int abc

struct MyStruct

enum MyEnum

    int bcd

int cde
''')
        except SpecParserError as exc:
            self.assertEqual(str(exc), '''\
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
        self.assert_struct_by_name(parser, 'MyStruct', ())
        self.assert_enum_by_name(parser, 'MyEnum', ())

        # Check actions
        self.assert_action(parser, 'MyAction', (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [':2: error: Member definition outside of struct scope',
                          ':8: error: Member definition outside of struct scope',
                          ':10: error: Syntax error'])

    # Error - enum value definition outside enum scope
    def test_error_enum(self):

        # Parse spec string
        parser = SpecParser()
        try:
            parser.parse_string('''\
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
        except SpecParserError as exc:
            self.assertEqual(str(exc), '''\
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
        self.assert_struct_by_name(parser, 'MyStruct', ())
        self.assert_enum_by_name(parser, 'MyEnum', ())

        # Check actions
        self.assert_action(parser, 'MyAction', (), (), ())

        # Check errors
        self.assertEqual(parser.errors,
                         [':2: error: Syntax error',
                          ':3: error: Syntax error',
                          ':4: error: Syntax error',
                          ':8: error: Enumeration value outside of enum scope',
                          ':12: error: Enumeration value outside of enum scope'])

    @staticmethod
    def attr_tuple(attr=None, op_eq=None, op_lt=None, op_lte=None, op_gt=None, op_gte=None,
                   op_len_eq=None, op_len_lt=None, op_len_lte=None, op_len_gt=None, op_len_gte=None):
        return (attr.op_eq if attr else op_eq,
                attr.op_lt if attr else op_lt,
                attr.op_lte if attr else op_lte,
                attr.op_gt if attr else op_gt,
                attr.op_gte if attr else op_gte,
                attr.op_len_eq if attr else op_len_eq,
                attr.op_len_lt if attr else op_len_lt,
                attr.op_len_lte if attr else op_len_lte,
                attr.op_len_gt if attr else op_len_gt,
                attr.op_len_gte if attr else op_len_gte)

    # Test valid attribute usage
    def test_attributes(self):

        # Parse spec string
        parser = SpecParser()
        parser.parse_string('''\
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
''', filename='foo')
        struct = parser.types['MyStruct']

        # Check counts
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(parser.types), 1)
        self.assertEqual(len(parser.actions), 0)

        # Check struct members
        self.assert_struct_by_name(parser, 'MyStruct',
                                   (('i1', type(chisel.model.TYPE_INT), True),
                                    ('i2', type(chisel.model.TYPE_INT), True),
                                    ('i3', type(chisel.model.TYPE_INT), False),
                                    ('i4', type(chisel.model.TYPE_INT), False),
                                    ('i5', type(chisel.model.TYPE_INT), False),
                                    ('f1', type(chisel.model.TYPE_FLOAT), False),
                                    ('f2', type(chisel.model.TYPE_FLOAT), False),
                                    ('s1', type(chisel.model.TYPE_STRING), False),
                                    ('s2', type(chisel.model.TYPE_STRING), False),
                                    ('s3', type(chisel.model.TYPE_STRING), False),
                                    ('ai1', chisel.model.TypeArray, False),
                                    ('as1', chisel.model.TypeArray, False),
                                    ('as2', chisel.model.TypeArray, False),
                                    ('di1', chisel.model.TypeDict, False),
                                    ('ds1', chisel.model.TypeDict, False),
                                    ('ds2', chisel.model.TypeDict, False),
                                    ('ds3', chisel.model.TypeDict, False),
                                   ))

        # Check i1 constraints
        itm = iter(struct.members)
        struct_i1 = next(itm)
        self.assertEqual(self.attr_tuple(struct_i1.attr), self.attr_tuple(op_lte=10.5, op_gt=1))

        # Check i2 constraints
        struct_i2 = next(itm)
        self.assertEqual(self.attr_tuple(struct_i2.attr), self.attr_tuple(op_lt=10, op_gte=1))

        # Check i3 constraints
        struct_i3 = next(itm)
        self.assertEqual(self.attr_tuple(struct_i3.attr), self.attr_tuple(op_lte=10, op_gt=0))

        # Check i4 constraints
        struct_i4 = next(itm)
        self.assertEqual(self.attr_tuple(struct_i4.attr), self.attr_tuple(op_lt=-1.4, op_gt=-4))

        # Check i5 constraints
        struct_i5 = next(itm)
        self.assertEqual(self.attr_tuple(struct_i5.attr), self.attr_tuple(op_eq=5))

        # Check f1 constraints
        struct_f1 = next(itm)
        self.assertEqual(self.attr_tuple(struct_f1.attr), self.attr_tuple(op_lte=10.5, op_gt=1))

        # Check f2 constraints
        struct_f2 = next(itm)
        self.assertEqual(self.attr_tuple(struct_f2.attr), self.attr_tuple(op_lt=10, op_gte=1.5))

        # Check s1 constraints
        struct_s1 = next(itm)
        self.assertEqual(self.attr_tuple(struct_s1.attr), self.attr_tuple(op_len_lt=101, op_len_gt=5))

        # Check s2 constraints
        struct_s2 = next(itm)
        self.assertEqual(self.attr_tuple(struct_s2.attr), self.attr_tuple(op_len_lte=100, op_len_gte=5))

        # Check s3 constraints
        struct_s3 = next(itm)
        self.assertEqual(self.attr_tuple(struct_s3.attr), self.attr_tuple(op_len_eq=2))

        # Check ai1 constraints
        struct_ai1 = next(itm)
        self.assertEqual(struct_ai1.attr, None)
        self.assertEqual(self.attr_tuple(struct_ai1.type.attr), self.attr_tuple(op_gt=5))

        # Check as1 constraints
        struct_as1 = next(itm)
        self.assertEqual(self.attr_tuple(struct_as1.attr), self.attr_tuple(op_len_lt=10))
        self.assertEqual(self.attr_tuple(struct_as1.type.attr), self.attr_tuple(op_len_lt=5))

        # Check as2 constraints
        struct_as2 = next(itm)
        self.assertEqual(self.attr_tuple(struct_as2.attr), self.attr_tuple(op_len_eq=3))
        self.assertEqual(self.attr_tuple(struct_as2.type.attr), self.attr_tuple(op_len_eq=2))

        # Check di1 constraints
        struct_di1 = next(itm)
        self.assertEqual(struct_di1.attr, None)
        self.assertEqual(self.attr_tuple(struct_di1.type.attr), self.attr_tuple(op_lt=15))

        # Check ds1 constraints
        struct_ds1 = next(itm)
        self.assertEqual(self.attr_tuple(struct_ds1.attr), self.attr_tuple(op_len_gt=10))
        self.assertEqual(self.attr_tuple(struct_ds1.type.attr), self.attr_tuple(op_len_gt=5))

        # Check ds2 constraints
        ds2 = next(itm)
        self.assertEqual(self.attr_tuple(ds2.attr), self.attr_tuple(op_len_eq=3))
        self.assertEqual(self.attr_tuple(ds2.type.attr), self.attr_tuple(op_len_eq=2))

        # Check ds3 constraints
        ds3 = next(itm)
        self.assertEqual(self.attr_tuple(ds3.attr), self.attr_tuple(op_len_eq=3))
        self.assertEqual(self.attr_tuple(ds3.type.attr), self.attr_tuple(op_len_eq=2))
        self.assertEqual(self.attr_tuple(ds3.type.key_attr), self.attr_tuple(op_len_eq=1))

        self.assertEqual(next(itm, None), None)

    def _test_spec_error(self, errors, spec):
        parser = SpecParser()
        try:
            parser.parse_string(spec)
        except SpecParserError as exc:
            self.assertEqual(str(exc), '\n'.join(errors))
        else:
            self.fail()
        self.assertEqual(len(parser.errors), len(errors))
        self.assertEqual(parser.errors, errors)

    def test_error_attribute_eq(self):
        self._test_spec_error([":2: error: Invalid attribute '== 7'"], '''\
struct MyStruct
    string(== 7) s
''')

    def test_error_attribute_lt(self):
        self._test_spec_error([":2: error: Invalid attribute '< 7'"], '''\
struct MyStruct
    string(< 7) s
''')

    def test_error_attribute_gt(self):
        self._test_spec_error([":2: error: Invalid attribute '> 7'"], '''\
struct MyStruct
    string(> 7) s
''')

    def test_error_attribute_lt_gt(self):
        self._test_spec_error([":2: error: Invalid attribute '< 7'"], '''\
struct MyStruct
    string(< 7, > 7) s
''')

    def test_error_attribute_lte_gte(self):
        self._test_spec_error([":6: error: Invalid attribute '>= 1'",
                               ":7: error: Invalid attribute '<= 2'"], '''\
enum MyEnum
    Foo
    Bar

struct MyStruct
    MyStruct(>= 1) a
    MyEnum(<= 2) b
''')

    def test_error_attribute_len_eq(self):
        self._test_spec_error([":2: error: Invalid attribute 'len == 1'"], '''\
struct MyStruct
    int(len == 1) i
''')

    def test_error_attribute_len_lt(self):
        self._test_spec_error([":2: error: Invalid attribute 'len < 10'"], '''\
struct MyStruct
    float(len < 10) f
''')

    def test_error_attribute_len_gt(self):
        self._test_spec_error([":2: error: Invalid attribute 'len > 1'"], '''\
struct MyStruct
    int(len > 1) i
''')

    def test_error_attribute_len_lt_gt(self):
        self._test_spec_error([":2: error: Invalid attribute 'len < 10'"], '''\
struct MyStruct
    float(len < 10, len > 10) f
''')

    def test_error_attribute_len_lte_gte(self): # pylint: disable=invalid-name
        self._test_spec_error([":2: error: Invalid attribute 'len <= 10'",
                               ":3: error: Invalid attribute 'len >= 10'"], '''\
struct MyStruct
    float(len <= 10) f
    float(len >= 10) f2
''')

    def test_error_attribute_invalid(self):
        self._test_spec_error([':2: error: Syntax error'], '''\
struct MyStruct
    string(regex="abc") a
''')

    def test_error_member_invalid(self):
        self._test_spec_error([':1: error: Member definition outside of struct scope',
                               ':5: error: Member definition outside of struct scope'], '''\
    string a

enum MyEnum
    Foo
    int b
''')

    def test_error_member_redefinition(self):
        self._test_spec_error([":4: error: Redefinition of member 'b'"], '''\
struct MyStruct
    string b
    int a
    float b
''')

    def test_error_enum_duplicate_value(self):
        self._test_spec_error([":4: error: Duplicate enumeration value 'bar'"], '''\
enum MyEnum
    bar
    foo
    bar
''')

    def test_doc(self):

        # Parse spec string
        parser = SpecParser()
        parser.parse_string('''\
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
        self.assertEqual(parser.actions['MyAction'].input_type.doc,
                         [])
        self.assertEqual(parser.actions['MyAction'].input_type.members[0].doc,
                         ['My input member'])
        self.assertEqual(parser.actions['MyAction'].output_type.doc,
                         [])
        self.assertEqual(parser.actions['MyAction'].output_type.members[0].doc,
                         ['My output member'])

    def test_typedef(self):

        parser = SpecParser()
        parser.parse_string('''\
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
        self.assertEqual(typedef.type_name, 'MyTypedef')
        self.assertEqual(typedef.doc, ['My typedef'])
        self.assertTrue(isinstance(typedef.type, chisel.model.TypeDict))
        self.assertEqual(self.attr_tuple(typedef.attr), self.attr_tuple(op_len_gt=0))
        self.assertTrue(typedef.type.key_type is parser.types['MyEnum'])
        self.assertEqual(typedef.type.key_type.doc, [])
        self.assertEqual(len(typedef.type.key_type.values), 2)
        self.assertTrue(typedef.type.type is parser.types['MyStruct'])
        self.assertEqual(typedef.type.type.doc, [])
        self.assertEqual(len(typedef.type.type.members), 2)

        typedef2 = parser.types['MyTypedef2']
        self.assertTrue(isinstance(typedef2, chisel.model.Typedef))
        self.assertEqual(typedef2.type_name, 'MyTypedef2')
        self.assertEqual(typedef2.doc, [])
        self.assertTrue(typedef2.type is parser.types['MyEnum'])
        self.assertEqual(typedef2.attr, None)

    def test_error_dict_non_string_key(self):

        parser = SpecParser()
        try:
            parser.parse_string('''\
struct Foo
    int : int {} a
''')
        except SpecParserError:
            self.assertEqual(parser.errors, [
                ':2: error: Invalid dictionary key type',
            ])
        else:
            self.fail()

    def test_error_action_input_redefinition(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_error_action_output_redefinition(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_error_action_errors_redefinition(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_action_input_struct(self):

        parser = SpecParser()
        parser.parse_string('''\
struct Foo
    int a
    int b

action FooAction
    input Foo
''')
        self.assertTrue(parser.actions['FooAction'].input_type, parser.types['Foo'])

    def test_action_input_typedef(self):

        parser = SpecParser()
        parser.parse_string('''\
struct Bar
    int a
    int b

typedef Bar Foo

action FooAction
    input Foo
''')
        self.assertTrue(parser.actions['FooAction'].input_type, parser.types['Foo'])

    def test_action_input_type_non_struct(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_action_input_type_typedef_non_struct(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_action_output_struct(self):

        parser = SpecParser()
        parser.parse_string('''\
struct Foo
    int a
    int b

action FooAction
    output Foo
''')
        self.assertTrue(parser.actions['FooAction'].output_type, parser.types['Foo'])

    def test_action_output_typedef(self):

        parser = SpecParser()
        parser.parse_string('''\
struct Bar
    int a
    int b

typedef Bar Foo

action FooAction
    output Foo
''')
        self.assertTrue(parser.actions['FooAction'].output_type, parser.types['Foo'])

    def test_action_output_non_struct(self):

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_action_output_typedef_non_struct(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_action_errors_enum(self):

        parser = SpecParser()
        parser.parse_string('''\
enum Foo
    A
    B

action FooAction
    errors Foo
''')
        self.assertTrue(parser.actions['FooAction'].error_type, parser.types['Foo'])

    def test_action_errors_typedef(self):

        parser = SpecParser()
        parser.parse_string('''\
action FooAction
    errors Foo

enum Bar
    A
    B

typedef Bar Foo
''')
        self.assertTrue(parser.actions['FooAction'].error_type, parser.types['Foo'])

    def test_action_errors_non_enum(self):

        parser = SpecParser()
        try:
            parser.parse_string('''\
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

    def test_action_errors_typedef_non_enum(self): # pylint: disable=invalid-name

        parser = SpecParser()
        try:
            parser.parse_string('''\
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
