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

from chisel.compat import json, long_, PY3
from chisel.model import JsonDatetime, JsonFloat, JsonUUID, ValidationError, \
    VALIDATE_DEFAULT, VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT, VALIDATE_JSON_OUTPUT, \
    TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool, \
    TypeUuid, TypeDatetime, tzutc, tzlocal, IMMUTABLE_VALIDATION_MODES
import chisel.model

from datetime import datetime
import unittest
from uuid import UUID

ALL_VALIDATION_MODES = (VALIDATE_DEFAULT, VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT, VALIDATE_JSON_OUTPUT)


class TestModelJsonDatetime(unittest.TestCase):

    # Datetime with timezone
    def test_model_jsonDatetime(self):

        value = datetime(2013, 6, 30, 17, 19, 0, tzinfo=tzutc)
        o = JsonDatetime(value)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(o.value, value)
        self.assertTrue(o.value.tzinfo is not None)
        self.assertEqual(repr(o), '"2013-06-30T17:19:00+00:00"')
        self.assertEqual(str(o), '"2013-06-30T17:19:00+00:00"')
        self.assertEqual(json.dumps({'v': o}), '{"v": "2013-06-30T17:19:00+00:00"}')

    # Datetime without timezone
    def test_model_jsonDatetime_no_timezone(self):

        value = datetime(2013, 6, 30, 17, 19, 0)
        o = JsonDatetime(value)
        oExpected = JsonDatetime(datetime(2013, 6, 30, 17, 19, 0, tzinfo=tzlocal))
        self.assertTrue(isinstance(o, float))
        self.assertTrue(isinstance(o.value, datetime))
        self.assertTrue(o.value.tzinfo is not None)
        self.assertEqual(repr(o), repr(oExpected))
        self.assertEqual(str(o), repr(oExpected))
        self.assertEqual(json.dumps({'v': o}), '{"v": ' + repr(o) + '}')

    # Test built-in float function behavior
    def test_model_jsonDatetime_float(self):

        value = datetime(2013, 6, 30, 17, 19, 0, tzinfo=tzutc)
        o = JsonDatetime(value)
        f = float(o)
        self.assertTrue(f is o)
        self.assertEqual(repr(o), '"2013-06-30T17:19:00+00:00"')


class TestModelJsonFloat(unittest.TestCase):

    def test_model_jsonFloat_default(self):

        o = JsonFloat(2.1234567)
        f = float(o)
        self.assertTrue(f is o)
        self.assertEqual(repr(o), '2.123457')
        self.assertEqual(str(o), '2.123457')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2.123457}')

    # Basic two decimal places float repr
    def test_model_jsonFloat(self):

        o = JsonFloat(2.25, 2)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2.25')
        self.assertEqual(str(o), '2.25')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2.25}')

    # Two decimal places float repr round up
    def test_model_jsonFloat_round_up(self):

        o = JsonFloat(2.256, 2)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2.26')
        self.assertEqual(str(o), '2.26')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2.26}')

    # Two decimal places float repr round down
    def test_model_jsonFloat_round_down(self):

        o = JsonFloat(2.254, 2)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2.25')
        self.assertEqual(str(o), '2.25')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2.25}')

    # Two decimal places float repr - ugly in Python 2.6
    def test_model_jsonFloat_ugly(self):

        o = JsonFloat(2.03, 2)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2.03')
        self.assertEqual(str(o), '2.03')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2.03}')

    # Two decimal places float repr with end-zero trimming
    def test_model_jsonFloat_zero_trim(self):

        o = JsonFloat(2.5, 2)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2.5')
        self.assertEqual(str(o), '2.5')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2.5}')

    # Two decimal places float repr with end-point trimming
    def test_model_jsonFloat_point_trim(self):

        o = JsonFloat(2., 2)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2')
        self.assertEqual(str(o), '2')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2}')

    # Zero decimal places
    def test_model_jsonFloat_zero_prec(self):

        o = JsonFloat(2.25, 0)
        self.assertTrue(isinstance(o, float))
        self.assertEqual(repr(o), '2')
        self.assertEqual(str(o), '2')
        self.assertEqual(json.dumps({'v': o}), '{"v": 2}')

    # Test built-in float function behavior
    def test_model_jsonFloat_float(self):

        o = JsonFloat(2.25, 2)
        f = float(o)
        self.assertTrue(f is o)
        self.assertEqual(repr(o), '2.25')


class TestModelJsonUUID(unittest.TestCase):

    def test_model_jsonUUID(self):

        value = UUID('184EAB31-4307-416C-AAC4-3B92B2358677')
        o = JsonUUID(value)
        self.assertTrue(isinstance(o, float))
        self.assertTrue(o.value is value)
        self.assertEqual(repr(o), '"184eab31-4307-416c-aac4-3b92b2358677"')
        self.assertEqual(str(o), '"184eab31-4307-416c-aac4-3b92b2358677"')
        self.assertEqual(json.dumps({'v': o}), '{"v": "184eab31-4307-416c-aac4-3b92b2358677"}')

    # Test built-in float function behavior
    def test_model_jsonUUID_float(self):

        value = UUID('184EAB31-4307-416C-AAC4-3B92B2358677')
        o = JsonUUID(value)
        f = float(o)
        self.assertTrue(f is o)
        self.assertEqual(repr(o), '"184eab31-4307-416c-aac4-3b92b2358677"')


class TestModelValidationError(unittest.TestCase):

    def test_model_memberSyntax_dict_single(self):
        self.assertEqual(ValidationError.memberSyntax(('a',)), 'a')

    def test_model_memberSyntax_dict_nested(self):
        self.assertEqual(ValidationError.memberSyntax(('a', 'b', 'c')), 'a.b.c')

    def test_model_memberSyntax_array_single(self):
        self.assertEqual(ValidationError.memberSyntax((0,)), '[0]')

    def test_model_memberSyntax_array_nested(self):
        self.assertEqual(ValidationError.memberSyntax((0, 1, 0)), '[0][1][0]')

    def test_model_memberSyntax_mixed(self):
        self.assertEqual(ValidationError.memberSyntax(('a', 1, 'b')), 'a[1].b')

    def test_model_memberSyntax_mixed2(self):
        self.assertEqual(ValidationError.memberSyntax((1, 'a', 0)), '[1].a[0]')

    def test_model_memberSyntax_empty(self):
        self.assertEqual(ValidationError.memberSyntax(()), None)

    def test_model_memberSyntax_none(self):
        self.assertEqual(ValidationError.memberSyntax(None), None)

    def test_model_memberError_basic(self):
        e = ValidationError.memberError(TypeInt(), 'abc', ('a',))
        self.assertTrue(isinstance(e, Exception))
        self.assertTrue(isinstance(e, ValidationError))
        self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member 'a', expected type 'int'")
        self.assertEqual(e.member, 'a')

    def test_model_memberError_no_member(self):
        e = ValidationError.memberError(TypeInt(), 'abc', ())
        self.assertTrue(isinstance(e, Exception))
        self.assertTrue(isinstance(e, ValidationError))
        self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'int'")
        self.assertEqual(e.member, None)

    def test_model_memberError_constraint(self):
        e = ValidationError.memberError(TypeInt(), 6, ('a',), constraintSyntax='< 5')
        self.assertTrue(isinstance(e, Exception))
        self.assertTrue(isinstance(e, ValidationError))
        self.assertEqual(str(e), "Invalid value 6 (type 'int') for member 'a', expected type 'int' [< 5]")
        self.assertEqual(e.member, 'a')


class TestStructMemberAttributes(unittest.TestCase):

    def test_model_StructMemberAttributes_validate_eq(self):
        attr = chisel.model.StructMemberAttributes(eq=5)
        attr.validate(5)
        try:
            attr.validate(4)
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 4 (type 'int') [== 5]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_lt(self):
        attr = chisel.model.StructMemberAttributes(lt=5)
        attr.validate(4)
        try:
            attr.validate(5)
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 5 (type 'int') [< 5]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_lte(self):
        attr = chisel.model.StructMemberAttributes(lte=5)
        attr.validate(5)
        try:
            attr.validate(6)
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 6 (type 'int') [<= 5]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_gt(self):
        attr = chisel.model.StructMemberAttributes(gt=5)
        attr.validate(6)
        try:
            attr.validate(5)
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 5 (type 'int') [> 5]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_gte(self):
        attr = chisel.model.StructMemberAttributes(gte=5)
        attr.validate(5)
        try:
            attr.validate(4)
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 4 (type 'int') [>= 5]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_len_eq(self):
        attr = chisel.model.StructMemberAttributes(len_eq=3)
        attr.validate('abc')
        try:
            attr.validate('ab')
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 'ab' (type 'str') [len == 3]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_len_lt(self):
        attr = chisel.model.StructMemberAttributes(len_lt=3)
        attr.validate('ab')
        try:
            attr.validate('abc')
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 'abc' (type 'str') [len < 3]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_len_lte(self):
        attr = chisel.model.StructMemberAttributes(len_lte=3)
        attr.validate('abc')
        try:
            attr.validate('abcd')
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 'abcd' (type 'str') [len <= 3]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_len_gt(self):
        attr = chisel.model.StructMemberAttributes(len_gt=3)
        attr.validate('abcd')
        try:
            attr.validate('abc')
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 'abc' (type 'str') [len > 3]")
        else:
            self.fail()

    def test_model_StructMemberAttributes_validate_len_gte(self):
        attr = chisel.model.StructMemberAttributes(len_gte=3)
        attr.validate('abc')
        try:
            attr.validate('ab')
        except chisel.model.ValidationError as e:
            self.assertEqual(str(e), "Invalid value 'ab' (type 'str') [len >= 3]")
        else:
            self.fail()


class TestModelTypedefValidation(unittest.TestCase):

    # Test typedef type construction
    def test_model_typedef_init(self):

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gt=5))
        self.assertEqual(t.typeName, 'typedef')
        self.assertTrue(isinstance(t.type, chisel.model._TypeInt))
        self.assertTrue(isinstance(t.attr, chisel.model.StructMemberAttributes))
        self.assertEqual(t.doc, [])

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gt=5), typeName='Foo', doc=['A', 'B'])
        self.assertEqual(t.typeName, 'Foo')
        self.assertTrue(isinstance(t.type, chisel.model._TypeInt))
        self.assertTrue(isinstance(t.attr, chisel.model.StructMemberAttributes))
        self.assertEqual(t.doc, ['A', 'B'])

    # Test typedef attribute validation
    def test_model_typedef_validateAttr(self):

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gt=5))

        try:
            t.validateAttr(chisel.model.StructMemberAttributes())
        except:
            self.fail()

        try:
            t.validateAttr(chisel.model.StructMemberAttributes(gt=7))
        except:
            self.fail()

        try:
            t.validateAttr(chisel.model.StructMemberAttributes(len_gt=7))
            self.fail()
        except chisel.model.AttributeValidationError as e:
            self.assertEqual(str(e), "Invalid attribute 'len > 7'")

    # All validation modes - success
    def test_model_typedef_validate(self):

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gte=5))

        o = 5
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # All validation modes - success
    def test_model_typedef_validate_no_attr(self):

        t = chisel.model.Typedef(TypeInt())

        o = 5
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # Query string validation mode - transformed value
    def test_model_typedef_validate_transformed_value(self):

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gte=5))

        o = '5'
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, 5)

    # Query string validation mode - transformed value
    def test_model_typedef_validate_type_error(self):

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gte=5))

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'int'")
            else:
                self.fail()

    # Query string validation mode - transformed value
    def test_model_typedef_validate_attr_error(self):

        t = chisel.model.Typedef(TypeInt(), chisel.model.StructMemberAttributes(gte=5))

        o = 4
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 4 (type 'int') [>= 5]")
            else:
                self.fail()


class TestModelStructValidation(unittest.TestCase):

    # Test struct type construction
    def test_model_struct_init(self):

        t = TypeStruct()
        self.assertEqual(t.typeName, 'struct')
        self.assertEqual(t.isUnion, False)
        self.assertEqual(t.members, [])
        self.assertEqual(t.doc, [])

        t.addMember('a', TypeStruct())
        self.assertEqual(len(t.members), 1)
        self.assertEqual(t.members[0].name, 'a')
        self.assertTrue(isinstance(t.members[0].type, TypeStruct))
        self.assertEqual(t.members[0].isOptional, False)
        self.assertEqual(t.members[0].doc, [])

    # Test union type construction
    def test_model_struct_init_union(self):

        t = TypeStruct(isUnion=True)
        self.assertEqual(t.typeName, 'union')
        self.assertEqual(t.isUnion, True)
        self.assertEqual(t.members, [])
        self.assertEqual(t.doc, [])

        t.addMember('a', TypeStruct())
        self.assertEqual(len(t.members), 1)
        self.assertEqual(t.members[0].name, 'a')
        self.assertTrue(isinstance(t.members[0].type, TypeStruct))
        self.assertEqual(t.members[0].isOptional, True)
        self.assertEqual(t.members[0].doc, [])

    # All validation modes - success
    def test_model_struct_validation(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())
        t.addMember('b', TypeString())

        o = {'a': 7, 'b': 'abc'}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 7, 'b': 'abc'})

    # All validation modes - union success
    def test_model_struct_validation_union(self):

        t = TypeStruct(isUnion=True)
        t.addMember('a', TypeInt())
        t.addMember('b', TypeString())

        o = {'a': 7}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 7})

        o = {'b': 'abc'}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'b': 'abc'})

    # All validation modes - optional member present
    def test_model_struct_validation_optional_present(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())
        t.addMember('b', TypeString(), isOptional=True)

        o = {'a': 7, 'b': 'abc'}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 7, 'b': 'abc'})

    # All validation modes - optional member missing
    def test_model_struct_validation_optional_missing(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())
        t.addMember('b', TypeString(), isOptional=True)

        o = {'a': 7}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 7})

    # All validation modes - member with attributes - valid
    def test_model_struct_validation_member_attributes_valid(self):

        t = TypeStruct()
        t.addMember('a', TypeInt(), attr=chisel.model.StructMemberAttributes(lt=5))

        o = {'a': 4}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 4})

    # All validation modes - member with attributes - invalid
    def test_model_struct_validation_member_attributes_invalid(self):

        t = TypeStruct()
        t.addMember('a', TypeInt(), attr=chisel.model.StructMemberAttributes(lt=5))

        o = {'a': 7}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 7 (type 'int') for member 'a' [< 5]")
            else:
                self.fail()

    # All validation modes - nested structure
    def test_model_struct_validation_nested(self):

        t = TypeStruct()
        t2 = TypeStruct()
        t.addMember('a', t2)
        t2.addMember('b', TypeInt())

        o = {'a': {'b': 7}}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
                self.assertTrue(o['a'] is o2['a'])
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(o['a'] is not o2['a'])
                self.assertTrue(isinstance(o2, dict))
                self.assertTrue(isinstance(o2['a'], dict))
            self.assertEqual(o2, {'a': {'b': 7}})

    # Query string validation mode - transformed member
    def test_model_struct_validation_query_string_transformed_member(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())

        o = {'a': '7'}
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, {'a': 7})

    # Query string validation mode - empty string
    def test_model_struct_validation_query_string_empty_string(self):

        t = TypeStruct()

        o = ''
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, {})

    # JSON input validation mode - transformed member
    def test_model_struct_validation_json_input_transformed_member(self):

        t = TypeStruct()
        t.addMember('a', TypeUuid())

        o = {'a': '184EAB31-4307-416C-AAC4-3B92B2358677'}
        o2 = t.validate(o, mode=VALIDATE_JSON_INPUT)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, {'a': UUID('184EAB31-4307-416C-AAC4-3B92B2358677')})

    # All validation modes - error - invalid value
    def test_model_struct_validation_error_invalid_value(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'struct'")
            else:
                self.fail()

    # All validation modes - error - optional none value
    def test_model_struct_validation_error_optional_none_value(self):

        t = TypeStruct()
        t.addMember('a', TypeInt(), isOptional=True)

        o = {'a': None}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value None (type 'NoneType') for member 'a', expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - member validation
    def test_model_struct_validation_error_member_validation(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())

        o = {'a': 'abc'}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member 'a', expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - nested member validation
    def test_model_struct_validation_error_nested_member_validation(self):

        t = TypeStruct()
        t2 = TypeStruct()
        t.addMember('a', t2)
        t2.addMember('b', TypeInt())

        o = {'a': {'b': 'abc'}}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member 'a.b', expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - unknown member
    def test_model_struct_validation_error_unknown_member(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())

        o = {'a': 7, 'b': 8}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Unknown member 'b'")
            else:
                self.fail()

    # All validation modes - error - missing member
    def test_model_struct_validation_error_missing_member(self):

        t = TypeStruct()
        t.addMember('a', TypeInt())

        o = {}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Required member 'a' missing")
            else:
                self.fail()

    # All validation modes - error - union with more than one member
    def test_model_struct_validation_error_union_multiple_members(self):

        t = TypeStruct(isUnion=True)
        t.addMember('a', TypeInt())
        t.addMember('bb', TypeString())

        o = {'a': 1, 'bb': 'abcd'}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertTrue(str(e).startswith('Invalid value {'))
                self.assertTrue(str(e).endswith("} (type 'dict'), expected type 'union'"))
            else:
                self.fail()

    # All validation modes - error - empty union
    def test_model_struct_validation_error_union_zero_members(self):

        t = TypeStruct(isUnion=True)
        t.addMember('a', TypeInt())
        t.addMember('b', TypeString())

        o = {}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value {} (type 'dict'), expected type 'union'")
            else:
                self.fail()

    # All validation modes - error - union unknown member
    def test_model_struct_validation_error_union_unknown_member(self):

        t = TypeStruct(isUnion=True)
        t.addMember('a', TypeInt())
        t.addMember('b', TypeString())

        o = {'c': 7}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Unknown member 'c'")
            else:
                self.fail()


class TestModelArrayValidation(unittest.TestCase):

    # Test array type construction
    def test_model_array_init(self):

        t = TypeArray(TypeInt())
        self.assertEqual(t.typeName, 'array')
        self.assertTrue(isinstance(t.type, chisel.model._TypeInt))
        self.assertEqual(t.attr, None)

    # All validation modes - success
    def test_model_array_validation(self):

        t = TypeArray(TypeInt())

        o = [1, 2, 3]
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, list))
            self.assertEqual(o2, [1, 2, 3])

    # All validation modes - value attributes - success
    def test_model_array_validation_attributes(self):

        t = TypeArray(TypeInt(), attr=chisel.model.StructMemberAttributes(lt=5))

        o = [1, 2, 3]
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, list))
            self.assertEqual(o2, [1, 2, 3])

    # All validation modes - value attributes - invalid value
    def test_model_array_validation_attributes_invalid(self):

        t = TypeArray(TypeInt(), attr=chisel.model.StructMemberAttributes(lt=5))

        o = [1, 7, 3]
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 7 (type 'int') for member '[1]' [< 5]")
            else:
                self.fail()

    # All validation modes - nested
    def test_model_array_validation_nested(self):

        t = TypeArray(TypeArray(TypeInt()))

        o = [[1, 2, 3], [4, 5, 6]]
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, list))
            self.assertEqual(o2, [[1, 2, 3], [4, 5, 6]])

    # Query string validation mode - transformed member
    def test_model_array_validation_query_string_transformed_member(self):

        t = TypeArray(TypeInt())

        o = [1, '2', 3]
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, [1, 2, 3])

    # Query string validation mode - empty string
    def test_model_array_validation_query_string_empty_string(self):

        t = TypeArray(TypeInt())

        o = ''
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, [])

    # JSON input validation mode - transformed member
    def test_model_array_validation_json_input_transformed_member(self):

        t = TypeArray(TypeUuid())

        o = ['39E23A29-2BEA-4402-A4D2-BB3DC057D17A']
        o2 = t.validate(o, mode=VALIDATE_JSON_INPUT)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, [UUID('39E23A29-2BEA-4402-A4D2-BB3DC057D17A')])

    # All validation modes - error - invalid value
    def test_model_array_validation_error_invalid_value(self):

        t = TypeArray(TypeInt())

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'array'")
            else:
                self.fail()

    # All validation modes - error - member validation
    def test_model_array_validation_error_member_validation(self):

        t = TypeArray(TypeInt())

        o = [1, 'abc', 3]
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member '[1]', expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - error nested
    def test_model_array_validation_error_nested(self):

        t = TypeArray(TypeArray(TypeInt()))

        o = [[1, 2, 3], [4, 5, 'abc']]
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member '[1][2]', expected type 'int'")
            else:
                self.fail()


class TestModelDictValidation(unittest.TestCase):

    # Test dict type construction
    def test_model_dict_init(self):

        t = TypeDict(TypeInt())
        self.assertEqual(t.typeName, 'dict')
        self.assertTrue(isinstance(t.type, chisel.model._TypeInt))

    # All validation modes - success
    def test_model_dict_validation(self):

        t = TypeDict(TypeInt())

        o = {'a': 7, 'b': 8}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 7, 'b': 8})

    # All validation modes - value attributes - success
    def test_model_dict_validation_value_attributes(self):

        t = TypeDict(TypeInt(), attr=chisel.model.StructMemberAttributes(lt=5))

        o = {'a': 1, 'b': 2}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 1, 'b': 2})

    # All validation modes - value attributes - invalid value
    def test_model_dict_validation_value_attributes_invalid(self):

        t = TypeDict(TypeInt(), attr=chisel.model.StructMemberAttributes(lt=5))

        o = {'a': 1, 'b': 7}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 7 (type 'int') for member 'b' [< 5]")
            else:
                self.fail()

    # All validation modes - key attributes - success
    def test_model_dict_validation_key_attributes(self):

        t = TypeDict(TypeInt(), keyAttr=chisel.model.StructMemberAttributes(len_lt=5))

        o = {'a': 1, 'b': 2}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': 1, 'b': 2})

    # All validation modes - key attributes - invalid key
    def test_model_dict_validation_key_attributes_invalid(self):

        t = TypeDict(TypeInt(), keyAttr=chisel.model.StructMemberAttributes(len_lt=2))

        o = {'a': 1, 'bc': 2}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'bc' (type 'str') for member 'bc' [len < 2]")
            else:
                self.fail()

    # All validation modes - nested
    def test_model_dict_validation_nested(self):

        t = TypeDict(TypeDict(TypeInt()))

        o = {'a': {'b': 7}}
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, dict))
            self.assertEqual(o2, {'a': {'b': 7}})

    # Query string validation mode - transformed member
    def test_model_dict_validation_query_string_transformed_member(self):

        t = TypeDict(TypeInt())

        o = {'a': '7'}
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, {'a': 7})

    # Query string validation mode - empty string
    def test_model_dict_validation_query_string_empty_string(self):

        t = TypeDict(TypeInt())

        o = ''
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, {})

    # JSON input validation mode - transformed member
    def test_model_dict_validation_json_input_transformed_member(self):

        t = TypeDict(TypeUuid())

        o = {'a': '72D33C44-7D30-4F15-903C-56DCC6DECD75'}
        o2 = t.validate(o, mode=VALIDATE_JSON_INPUT)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, {'a': UUID('72D33C44-7D30-4F15-903C-56DCC6DECD75')})

    # All validation modes - error - invalid value
    def test_model_dict_validation_error_invalid_value(self):

        t = TypeDict(TypeInt())

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'dict'")
            else:
                self.fail()

    # All validation modes - error - member key validation
    def test_model_dict_validation_error_member_key_validation(self):

        t = TypeDict(TypeInt())

        o = {7: 7}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 7 (type 'int') for member '[7]', expected type 'string'")
            else:
                self.fail()

    # All validation modes - error - member validation
    def test_model_dict_validation_error_member_validation(self):

        t = TypeDict(TypeInt())

        o = {'7': 'abc'}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member '7', expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - nested member validation
    def test_model_dict_validation_error_nested_member_validation(self):

        t = TypeDict(TypeDict(TypeInt()))

        o = {'a': {'b': 'abc'}}
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str') for member 'a.b', expected type 'int'")
            else:
                self.fail()


class TestModelEnumValidation(unittest.TestCase):

    # Test enum type construction
    def test_model_enum_init(self):

        t = TypeEnum()
        t.addValue('a')
        t.addValue('b')

        self.assertEqual(t.typeName, 'enum')
        self.assertEqual(t.values[0].value, 'a')
        self.assertEqual(t.values[0].doc, [])
        self.assertEqual(t.values[1].value, 'b')
        self.assertEqual(t.values[1].doc, [])
        self.assertEqual(t.doc, [])

    # All validation modes - valid enumeration value
    def test_model_enum_validate(self):

        t = TypeEnum()
        t.addValue('a')
        t.addValue('b')

        o = 'a'
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # All validation modes - valid enumeration value
    def test_model_enum_validate_error(self):

        t = TypeEnum()
        t.addValue('a')
        t.addValue('b')

        o = 'c'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'c' (type 'str'), expected type 'enum'")
            else:
                self.fail()


class TestModelStringValidation(unittest.TestCase):

    # Test string type construction
    def test_model_string_init(self):

        t = TypeString()

        self.assertEqual(t.typeName, 'string')

    # All validation modes - success
    def test_model_string_validate(self):

        t = TypeString()

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # All validation modes - unicode
    def test_model_string_validate_unicode(self):

        t = TypeString()

        o = str('abc') if PY3 else unicode('abc')
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # All validation modes - error - invalid value
    def test_model_string_validate_error(self):

        t = TypeString()

        o = 7
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 7 (type 'int'), expected type 'string'")
            else:
                self.fail()


class TestModelIntValidation(unittest.TestCase):

    # Test int type construction
    def test_model_int_init(self):

        t = TypeInt()

        self.assertEqual(t.typeName, 'int')

    # All validation modes - success
    def test_model_int_validate(self):

        t = TypeInt()

        o = 7
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # All validation modes - float
    def test_model_int_validate_float(self):

        t = TypeInt()

        o = 7.
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, (int, long_)))
                self.assertEqual(o2, 7)

    # Query string validation mode - string
    def test_model_int_query_string(self):

        t = TypeInt()

        o = '7'
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, 7)

    # All validation modes - error - invalid value
    def test_model_int_validate_error(self):

        t = TypeInt()

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - not-integer float
    def test_model_int_validate_error_float(self):

        t = TypeInt()

        o = 7.5
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 7.5 (type 'float'), expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - fake JSON float
    def test_model_int_validate_error_fake_float(self):

        t = TypeInt()

        o = JsonUUID(UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'))
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value \"aed91c7b-dcfd-49b3-a483-dbc9ea2031a3\" (type 'JsonUUID'), expected type 'int'")
            else:
                self.fail()

    # All validation modes - error - bool
    def test_model_int_validate_error_bool(self):

        t = TypeInt()

        o = True
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value True (type 'bool'), expected type 'int'")
            else:
                self.fail()


class TestModelFloatValidation(unittest.TestCase):

    # Test float type construction
    def test_model_float_init(self):

        t = TypeFloat()

        self.assertEqual(t.typeName, 'float')

    # All validation modes - success
    def test_model_float_validate(self):

        t = TypeFloat()

        o = 7.5
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # All validation modes - int
    def test_model_float_validate_int(self):

        t = TypeFloat()

        o = 7
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, float))
                self.assertEqual(o2, 7.)

    # All validation modes - long
    def test_model_float_validate_long(self):

        t = TypeFloat()

        o = long_(7)
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            if mode in IMMUTABLE_VALIDATION_MODES:
                self.assertTrue(o is o2)
            else:
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, float))
                self.assertEqual(o2, 7.)

    # Query string validation mode - string
    def test_model_float_query_string(self):

        t = TypeFloat()

        o = '7.5'
        o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
        self.assertTrue(o is not o2)
        self.assertEqual(o2, 7.5)

    # All validation modes - error - invalid value
    def test_model_float_validate_error(self):

        t = TypeFloat()

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'float'")
            else:
                self.fail()

    # All validation modes - error - bool
    def test_model_float_validate_error_bool(self):

        t = TypeFloat()

        o = True
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value True (type 'bool'), expected type 'float'")
            else:
                self.fail()

    # All validation modes - error - fake JSON float
    def test_model_float_validate_error_fake_float(self):

        t = TypeFloat()

        o = JsonUUID(UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'))
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value \"aed91c7b-dcfd-49b3-a483-dbc9ea2031a3\" (type 'JsonUUID'), expected type 'float'")
            else:
                self.fail()


class TestModelBoolValidation(unittest.TestCase):

    # Test bool type construction
    def test_model_bool_init(self):

        t = TypeBool()

        self.assertEqual(t.typeName, 'bool')

    # All validation modes - success
    def test_model_bool_validate(self):

        t = TypeBool()

        o = False
        for mode in ALL_VALIDATION_MODES:
            o2 = t.validate(o, mode)
            self.assertTrue(o is o2)

    # Query string validation mode - string
    def test_model_bool_validate_query_string(self):

        t = TypeBool()

        for o, expected in (('false', False), ('true', True)):
            o2 = t.validate(o, mode=VALIDATE_QUERY_STRING)
            self.assertTrue(o is not o2)
            self.assertTrue(isinstance(o2, bool))
            self.assertEqual(o2, expected)

    # All validation modes - error - invalid value
    def test_model_bool_validate_error(self):

        t = TypeBool()

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'bool'")
            else:
                self.fail()


class TestModelUuidValidation(unittest.TestCase):

    # Test uuid type construction
    def test_model_uuid_init(self):

        t = TypeUuid()

        self.assertEqual(t.typeName, 'uuid')

    # All validation modes - UUID object
    def test_model_uuid_validate(self):

        t = TypeUuid()

        o = UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3')
        for mode in ALL_VALIDATION_MODES:
            if mode != VALIDATE_JSON_OUTPUT:
                o2 = t.validate(o, mode)
                self.assertTrue(o is o2)
            else:
                try:
                    o2 = t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e),
                                     "Invalid value UUID('aed91c7b-dcfd-49b3-a483-dbc9ea2031a3') (type 'UUID'), "
                                     "expected type 'uuid' [JsonUUID object required]")
                else:
                    pass

    # All validation modes - JsonUUID object
    def test_model_uuid_validate_JsonUUID(self):

        t = TypeUuid()

        o = JsonUUID(UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'))
        for mode in ALL_VALIDATION_MODES:
            if mode == VALIDATE_JSON_OUTPUT:
                o2 = t.validate(o, mode)
                self.assertTrue(o is o2)
            else:
                try:
                    o2 = t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e),
                                     "Invalid value \"aed91c7b-dcfd-49b3-a483-dbc9ea2031a3\" (type 'JsonUUID'), "
                                     "expected type 'uuid'")
                else:
                    pass

    # All validation modes - UUID string
    def test_model_uuid_validate_string(self):

        t = TypeUuid()

        o = 'AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'
        for mode in ALL_VALIDATION_MODES:
            if mode in (VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT):
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, UUID))
                self.assertEqual(o2, UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'))
            else:
                try:
                    o2 = t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value 'AED91C7B-DCFD-49B3-A483-DBC9EA2031A3' (type 'str'), expected type 'uuid'")
                else:
                    pass

    # All validation modes - error - invalid value
    def test_model_uuid_validate_error(self):

        t = TypeUuid()

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'uuid'")
            else:
                self.fail()


class TestModelDatetimeValidation(unittest.TestCase):

    # Test datetime type construction
    def test_model_datetime_init(self):

        t = TypeDatetime()

        self.assertEqual(t.typeName, 'datetime')

    # All validation modes - datetime object
    def test_model_datetime_validate(self):

        t = TypeDatetime()

        o = datetime(2013, 5, 26, 11, 1, 0, tzinfo=tzutc)
        for mode in ALL_VALIDATION_MODES:
            if mode != VALIDATE_JSON_OUTPUT:
                o2 = t.validate(o, mode)
                self.assertTrue(o is o2)
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertTrue(str(e).startswith('Invalid value datetime.datetime(2013, 5, 26, 11, 1, '
                                                      'tzinfo=<chisel.model._TZUTC object at '))
                    self.assertTrue(str(e).endswith(">) (type 'datetime'), expected type 'datetime' [JsonDatetime object required]"))
                else:
                    self.fail()

    # All validation modes - JSONDatetime object
    def test_model_datetime_JSONDatetime(self):

        t = TypeDatetime()

        o = JsonDatetime(datetime(2013, 5, 26, 11, 1, 0, tzinfo=tzutc))
        for mode in ALL_VALIDATION_MODES:
            if mode == VALIDATE_JSON_OUTPUT:
                o2 = t.validate(o, mode)
                self.assertTrue(o is o2)
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value \"2013-05-26T11:01:00+00:00\" (type 'JsonDatetime'), expected type 'datetime'")
                else:
                    self.fail()

    # All validation modes - datetime object with no timezone
    def test_model_datetime_validate_no_timezone(self):

        t = TypeDatetime()

        o = datetime(2013, 5, 26, 11, 1, 0)
        for mode in ALL_VALIDATION_MODES:
            if mode == VALIDATE_DEFAULT:
                o2 = t.validate(o, mode)
                self.assertTrue(o is o2)
            elif mode not in IMMUTABLE_VALIDATION_MODES:
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertEqual(o2, datetime(2013, 5, 26, 11, 1, 0, tzinfo=tzlocal))
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e),
                                     "Invalid value datetime.datetime(2013, 5, 26, 11, 1) (type 'datetime'), "
                                     "expected type 'datetime' [JsonDatetime object required]")
                else:
                    self.fail()

    # All validation modes - ISO datetime string
    def test_model_datetime_validate_query_string(self):

        t = TypeDatetime()

        o = '2013-05-26T11:01:00+08:00'
        for mode in ALL_VALIDATION_MODES:
            if mode in (VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT):
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, datetime))
                self.assertEqual(o2, datetime(2013, 5, 26, 3, 1, 0, tzinfo=tzutc))
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value '2013-05-26T11:01:00+08:00' (type 'str'), expected type 'datetime'")
                else:
                    self.fail()

    # All validation modes - ISO datetime string - zulu
    def test_model_datetime_validate_query_string_zulu(self):

        t = TypeDatetime()

        o = '2013-05-26T11:01:00+00:00'
        for mode in ALL_VALIDATION_MODES:
            if mode in (VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT):
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, datetime))
                self.assertEqual(o2, datetime(2013, 5, 26, 11, 1, 0, tzinfo=tzutc))
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value '2013-05-26T11:01:00+00:00' (type 'str'), expected type 'datetime'")
                else:
                    self.fail()

    # All validation modes - ISO datetime string - fraction second
    def test_model_datetime_validate_query_string_fracsec(self):

        t = TypeDatetime()

        o = '2013-05-26T11:01:00.1234+00:00'
        for mode in ALL_VALIDATION_MODES:
            if mode in (VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT):
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, datetime))
                self.assertEqual(o2, datetime(2013, 5, 26, 11, 1, 0, 123400, tzinfo=tzutc))
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value '2013-05-26T11:01:00.1234+00:00' (type 'str'), expected type 'datetime'")
                else:
                    self.fail()

    # All validation modes - ISO datetime string - no seconds
    def test_model_datetime_validate_query_string_no_seconds(self):

        t = TypeDatetime()

        o = '2013-05-26T11:01Z'
        for mode in ALL_VALIDATION_MODES:
            if mode in (VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT):
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, datetime))
                self.assertEqual(o2, datetime(2013, 5, 26, 11, 1, 0, 0, tzinfo=tzutc))
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value '2013-05-26T11:01Z' (type 'str'), expected type 'datetime'")
                else:
                    self.fail()

    # All validation modes - ISO datetime string - no minutes
    def test_model_datetime_validate_query_string_no_minutes(self):

        t = TypeDatetime()

        o = '2013-05-26T11Z'
        for mode in ALL_VALIDATION_MODES:
            if mode in (VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT):
                o2 = t.validate(o, mode)
                self.assertTrue(o is not o2)
                self.assertTrue(isinstance(o2, datetime))
                self.assertEqual(o2, datetime(2013, 5, 26, 11, 0, 0, 0, tzinfo=tzutc))
            else:
                try:
                    t.validate(o, mode)
                except ValidationError as e:
                    self.assertEqual(str(e), "Invalid value '2013-05-26T11Z' (type 'str'), expected type 'datetime'")
                else:
                    self.fail()

    # All validation modes - error - invalid value
    def test_model_datetime_validate_error(self):

        t = TypeDatetime()

        o = 'abc'
        for mode in ALL_VALIDATION_MODES:
            try:
                t.validate(o, mode)
            except ValidationError as e:
                self.assertEqual(str(e), "Invalid value 'abc' (type 'str'), expected type 'datetime'")
            else:
                self.fail()
