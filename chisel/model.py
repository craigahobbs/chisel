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

from datetime import date, datetime
from itertools import chain
from math import isnan, isinf
from uuid import UUID

from .util import TZLOCAL, parse_iso8601_date, parse_iso8601_datetime


# Validation mode
VALIDATE_DEFAULT = 0
VALIDATE_QUERY_STRING = 1
VALIDATE_JSON_INPUT = 2

# Immutable validation modes
IMMUTABLE_VALIDATION_MODES = (VALIDATE_DEFAULT,)


# Type attribute exception
class AttributeValidationError(Exception):
    __slots__ = ('attr',)

    def __init__(self, attr):
        Exception.__init__(self, "Invalid attribute '" + attr + "'")
        self.attr = attr


# Type validation exception
class ValidationError(Exception):
    __slots__ = ('member',)

    def __init__(self, msg, member=None):
        Exception.__init__(self, msg)
        self.member = member

    @classmethod
    def _flatten_members(cls, members):
        for submember in members:
            if isinstance(submember, tuple):
                yield from cls._flatten_members(submember)
            else:
                yield submember

    @classmethod
    def member_syntax(cls, members):
        if members:
            return ''.join((('.' + x) if isinstance(x, str) else ('[' + repr(x) + ']'))
                           for x in cls._flatten_members(members)).lstrip('.')
        return None

    @classmethod
    def member_error(cls, type_, value, members, constraint_syntax=None):
        member_syntax = cls.member_syntax(members)
        msg = 'Invalid value ' + repr(value) + " (type '" + value.__class__.__name__ + "')" + \
              ((" for member '" + member_syntax + "'") if member_syntax else '') + \
              ((", expected type '" + type_.type_name + "'") if type_ else '') + \
              ((' [' + constraint_syntax + ']') if constraint_syntax else '')
        return ValidationError(msg, member=member_syntax)


# Struct member attributes
class StructMemberAttributes(object):
    __slots__ = ('op_eq', 'op_lt', 'op_lte', 'op_gt', 'op_gte',
                 'op_len_eq', 'op_len_lt', 'op_len_lte', 'op_len_gt', 'op_len_gte')

    def __init__(self, op_eq=None, op_lt=None, op_lte=None, op_gt=None, op_gte=None,
                 op_len_eq=None, op_len_lt=None, op_len_lte=None, op_len_gt=None, op_len_gte=None):

        self.op_eq = op_eq
        self.op_lt = op_lt
        self.op_lte = op_lte
        self.op_gt = op_gt
        self.op_gte = op_gte
        self.op_len_eq = op_len_eq
        self.op_len_lt = op_len_lt
        self.op_len_lte = op_len_lte
        self.op_len_gt = op_len_gt
        self.op_len_gte = op_len_gte

    @staticmethod
    def _format_float(value):
        return '{0:.6f}'.format(value).rstrip('0').rstrip('.')

    def validate(self, value, _member=()):
        if self.op_lt is not None and value >= self.op_lt:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='< ' + self._format_float(self.op_lt))
        if self.op_lte is not None and value > self.op_lte:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='<= ' + self._format_float(self.op_lte))
        if self.op_gt is not None and value <= self.op_gt:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='> ' + self._format_float(self.op_gt))
        if self.op_gte is not None and value < self.op_gte:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='>= ' + self._format_float(self.op_gte))
        if self.op_eq is not None and value != self.op_eq:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='== ' + self._format_float(self.op_eq))
        if self.op_len_lt is not None and len(value) >= self.op_len_lt:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='len < ' + self._format_float(self.op_len_lt))
        if self.op_len_lte is not None and len(value) > self.op_len_lte:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='len <= ' + self._format_float(self.op_len_lte))
        if self.op_len_gt is not None and len(value) <= self.op_len_gt:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='len > ' + self._format_float(self.op_len_gt))
        if self.op_len_gte is not None and len(value) < self.op_len_gte:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='len >= ' + self._format_float(self.op_len_gte))
        if self.op_len_eq is not None and len(value) != self.op_len_eq:
            raise ValidationError.member_error(None, value, _member, constraint_syntax='len == ' + self._format_float(self.op_len_eq))

    def validate_attr(self, allow_value=False, allow_length=False):
        if not allow_value:
            if self.op_lt is not None:
                raise AttributeValidationError('< ' + self._format_float(self.op_lt))
            if self.op_lte is not None:
                raise AttributeValidationError('<= ' + self._format_float(self.op_lte))
            if self.op_gt is not None:
                raise AttributeValidationError('> ' + self._format_float(self.op_gt))
            if self.op_gte is not None:
                raise AttributeValidationError('>= ' + self._format_float(self.op_gte))
            if self.op_eq is not None:
                raise AttributeValidationError('== ' + self._format_float(self.op_eq))
        if not allow_length:
            if self.op_len_lt is not None:
                raise AttributeValidationError('len < ' + self._format_float(self.op_len_lt))
            if self.op_len_lte is not None:
                raise AttributeValidationError('len <= ' + self._format_float(self.op_len_lte))
            if self.op_len_gt is not None:
                raise AttributeValidationError('len > ' + self._format_float(self.op_len_gt))
            if self.op_len_gte is not None:
                raise AttributeValidationError('len >= ' + self._format_float(self.op_len_gte))
            if self.op_len_eq is not None:
                raise AttributeValidationError('len == ' + self._format_float(self.op_len_eq))


# Typedef type (type plus attributes)
class Typedef(object):
    __slots__ = ('type_name', 'type', 'attr', 'doc')

    def __init__(self, type_, attr=None, type_name=None, doc=None):
        self.type_name = 'typedef' if type_name is None else type_name
        self.type = type_
        self.attr = attr
        self.doc = [] if doc is None else doc

    @staticmethod
    def base_type(type_):
        while isinstance(type_, Typedef):
            type_ = type_.type
        return type_

    def validate_attr(self, attr):
        self.type.validate_attr(attr)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):
        result = self.type.validate(value, mode, _member)
        if self.attr is not None:
            self.attr.validate(result, _member)
        return result


# Struct member
class StructMember(object):
    __slots__ = ('name', 'type', 'optional', 'nullable', 'attr', 'doc')

    def __init__(self, name, type_, optional=False, nullable=False, attr=None, doc=None):
        self.name = name
        self.type = type_
        self.optional = optional
        self.nullable = nullable
        self.attr = attr
        self.doc = [] if doc is None else doc


# Struct type
class TypeStruct(object):
    __slots__ = ('type_name', 'union', 'base_types', '_members', 'doc')

    def __init__(self, type_name=None, union=False, base_types=None, doc=None):
        self.type_name = ('union' if union else 'struct') if type_name is None else type_name
        self.union = union
        self.base_types = base_types
        self._members = []
        self.doc = [] if doc is None else doc

    def members(self, include_base_types=True):
        return iter(self._members) if self.base_types is None or not include_base_types else \
            chain(chain.from_iterable(Typedef.base_type(base_type).members() for base_type in self.base_types if base_type), self._members)

    def add_member(self, name, type_, optional=False, nullable=False, attr=None, doc=None):
        member = StructMember(name, type_, optional or self.union, nullable, attr, doc)
        self._members.append(member)
        return member

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, dict):
            value_x = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            value_x = {}
        else:
            raise ValidationError.member_error(self, value, _member)

        # Valid union?
        if self.union:
            if len(value_x) != 1:
                raise ValidationError.member_error(self, value, _member)

        # Result a copy?
        value_copy = None if mode in IMMUTABLE_VALIDATION_MODES else {}

        # Validate all member values
        member_count = 0
        for member in self.members():
            member_name = member.name
            if member_name not in value_x:
                if not member.optional:
                    raise ValidationError("Required member '" + ValidationError.member_syntax((_member, member_name)) + "' missing")
                continue
            member_count += 1
            member_value = value_x[member_name]
            if member.nullable and (member_value is None or \
                    (mode == VALIDATE_QUERY_STRING and not isinstance(member.type, _TypeString) and member_value == 'null')):
                member_value_x = None
            else:
                member_path = (_member, member_name)
                member_value_x = member.type.validate(member_value, mode, member_path)
                if member.attr is not None:
                    member.attr.validate(member_value_x, member_path)
            if value_copy is not None:
                value_copy[member_name] = member_value_x

        # Any unknown members?
        if member_count != len(value_x):
            member_set = set(member.name for member in self.members())
            for value_name in value_x.keys():
                if value_name not in member_set:
                    raise ValidationError("Unknown member '" + ValidationError.member_syntax((_member, value_name)) + "'")

        return value if value_copy is None else value_copy


# Array type
class TypeArray(object):
    __slots__ = ('type', 'attr')

    type_name = 'array'

    def __init__(self, type_, attr=None):
        self.type = type_
        self.attr = attr

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr(allow_length=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, list) or isinstance(value, tuple):
            value_x = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            value_x = []
        else:
            raise ValidationError.member_error(self, value, _member)

        # Result a copy?
        value_copy = None if mode in IMMUTABLE_VALIDATION_MODES else []

        # Validate the list contents
        ix_array_value = 0
        for array_value in value_x:
            member_path = (_member, ix_array_value)
            array_value_x = self.type.validate(array_value, mode, member_path)
            if self.attr is not None:
                self.attr.validate(array_value_x, member_path)
            if value_copy is not None:
                value_copy.append(array_value_x)
            ix_array_value += 1

        return value if value_copy is None else value_copy


# Dict type
class TypeDict(object):
    __slots__ = ('type', 'attr', 'key_type', 'key_attr')

    type_name = 'dict'

    def __init__(self, type_, attr=None, key_type=None, key_attr=None):
        self.type = type_
        self.attr = attr
        self.key_type = key_type or TYPE_STRING
        self.key_attr = key_attr

    @staticmethod
    def valid_key_type(key_type):
        key_type_base = Typedef.base_type(key_type)
        return isinstance(key_type_base, _TypeString) or isinstance(key_type_base, TypeEnum)

    def has_default_key_type(self):
        return isinstance(self.key_type, _TypeString)

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr(allow_length=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, dict):
            value_x = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            value_x = {}
        else:
            raise ValidationError.member_error(self, value, _member)

        # Result a copy?
        value_copy = None if mode in IMMUTABLE_VALIDATION_MODES else {}

        # Validate the dict key/value pairs
        for dict_key, dict_value in value_x.items():
            member_path = (_member, dict_key)

            # Validate the key
            dict_key_x = self.key_type.validate(dict_key, mode, member_path)
            if self.key_attr is not None:
                self.key_attr.validate(dict_key_x, member_path)

            # Validate the value
            dict_value_x = self.type.validate(dict_value, mode, member_path)
            if self.attr is not None:
                self.attr.validate(dict_value_x, member_path)

            # Result a copy?
            if value_copy is not None:
                value_copy[dict_key_x] = dict_value_x

        return value if value_copy is None else value_copy


# Enumeration type
class EnumValue(object):
    __slots__ = ('value', 'doc')

    def __init__(self, valueString, doc=None):
        self.value = valueString
        self.doc = [] if doc is None else doc

    def __eq__(self, other):
        return self.value == other


class TypeEnum(object):
    __slots__ = ('type_name', 'base_types', '_values', 'doc')

    def __init__(self, type_name='enum', base_types=None, doc=None):
        self.type_name = type_name
        self.base_types = base_types
        self._values = []
        self.doc = [] if doc is None else doc

    def values(self, include_base_types=True):
        return iter(self._values) if self.base_types is None or not include_base_types else \
            chain(chain.from_iterable(Typedef.base_type(base_type).values() for base_type in self.base_types if base_type), self._values)

    def add_value(self, string, doc=None):
        value = EnumValue(string, doc)
        self._values.append(value)
        return value

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr()

    def validate(self, value, dummy_mode=VALIDATE_DEFAULT, _member=()):

        # Validate the value
        if value not in self.values():
            raise ValidationError.member_error(self, value, _member)

        return value


# String type
class _TypeString(object):
    __slots__ = ()

    type_name = 'string'

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr(allow_length=True)

    def validate(self, value, dummy_mode=VALIDATE_DEFAULT, _member=()):

        # Validate the value
        if not isinstance(value, str):
            raise ValidationError.member_error(self, value, _member)

        return value

TYPE_STRING = _TypeString()


# Int type
class _TypeInt(object):
    __slots__ = ()

    type_name = 'int'

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr(allow_value=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, int) and not isinstance(value, bool):
            value_x = value
        elif isinstance(value, float):
            value_x = int(value)
            if value_x != value:
                raise ValidationError.member_error(self, value, _member)
        elif mode == VALIDATE_QUERY_STRING and isinstance(value, str):
            try:
                value_x = int(value)
            except:
                raise ValidationError.member_error(self, value, _member)
        else:
            raise ValidationError.member_error(self, value, _member)

        return value if mode in IMMUTABLE_VALIDATION_MODES else value_x

TYPE_INT = _TypeInt()


# Float type
class _TypeFloat(object):
    __slots__ = ()

    type_name = 'float'

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr(allow_value=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, float):
            value_x = value
        elif isinstance(value, int) and not isinstance(value, bool):
            value_x = float(value)
        elif mode == VALIDATE_QUERY_STRING and isinstance(value, str):
            try:
                value_x = float(value)
                if isnan(value_x) or isinf(value_x):
                    raise ValueError()
            except:
                raise ValidationError.member_error(self, value, _member)
        else:
            raise ValidationError.member_error(self, value, _member)

        return value if mode in IMMUTABLE_VALIDATION_MODES else value_x

TYPE_FLOAT = _TypeFloat()


# Bool type
class _TypeBool(object):
    __slots__ = ()

    type_name = 'bool'

    VALUES = {
        'true': True,
        'false': False
    }

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, bool):
            return value
        elif mode == VALIDATE_QUERY_STRING and isinstance(value, str):
            try:
                return self.VALUES[value]
            except:
                raise ValidationError.member_error(self, value, _member)
        else:
            raise ValidationError.member_error(self, value, _member)

TYPE_BOOL = _TypeBool()


# Uuid type
class _TypeUuid(object):
    __slots__ = ()

    type_name = 'uuid'

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, UUID):
            return value
        elif mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, str):
            try:
                return UUID(value)
            except:
                raise ValidationError.member_error(self, value, _member)
        else:
            raise ValidationError.member_error(self, value, _member)

TYPE_UUID = _TypeUuid()


# Date type
class _TypeDate(object):
    __slots__ = ()

    type_name = 'date'

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, date):
            return value
        elif mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, str):
            try:
                return parse_iso8601_date(value)
            except:
                raise ValidationError.member_error(self, value, _member)
        else:
            raise ValidationError.member_error(self, value, _member)

TYPE_DATE = _TypeDate()


# Datetime type
class _TypeDatetime(object):
    __slots__ = ()

    type_name = 'datetime'

    @staticmethod
    def validate_attr(attr):
        attr.validate_attr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, datetime):
            # Set a time zone, if necessary
            if mode not in IMMUTABLE_VALIDATION_MODES and value.tzinfo is None:
                return value.replace(tzinfo=TZLOCAL)
            return value
        elif mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, str):
            try:
                return parse_iso8601_datetime(value)
            except:
                raise ValidationError.member_error(self, value, _member)
        else:
            raise ValidationError.member_error(self, value, _member)

TYPE_DATETIME = _TypeDatetime()
