# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from itertools import chain
from math import isnan, isinf
from uuid import UUID


# Validation mode
class ValidationMode(Enum):
    """
    TODO
    """

    #: TODO
    DEFAULT = 0

    #: TODO
    QUERY_STRING = 1

    #: TODO
    JSON_INPUT = 2


# Immutable validation modes
IMMUTABLE_VALIDATION_MODES = (ValidationMode.DEFAULT,)


class AttributeValidationError(Exception):
    """
    TODO
    """

    __slots__ = ('attr',)

    def __init__(self, attr):
        super().__init__("Invalid attribute '" + attr + "'")

        #: TODO
        self.attr = attr


class ValidationError(Exception):
    """
    TODO
    """

    __slots__ = ('member',)

    def __init__(self, msg, member=None):
        super().__init__(msg)

        #: TODO
        self.member = member


def _flatten_members(members):
    for submember in members:
        if isinstance(submember, tuple):
            yield from _flatten_members(submember)
        else:
            yield submember

def _member_syntax(members):
    if members:
        return ''.join(((f'.{x}') if isinstance(x, str) else (f'[{x!r}]')) for x in _flatten_members(members)).lstrip('.')
    return None

def _member_error(type_, value, members, constraint_syntax=None):
    member_syntax = _member_syntax(members)
    member_part = f" for member '{member_syntax}'" if member_syntax else ''
    type_part = f", expected type '{type_.type_name}'" if type_ else ''
    constraint_part = f' [{constraint_syntax}]' if constraint_syntax else ''
    msg = f"Invalid value {value!r:.1000s} (type '{value.__class__.__name__}'){member_part}{type_part}{constraint_part}"
    return ValidationError(msg, member=member_syntax)


def get_referenced_types(type_):
    """
    TODO
    """

    return sorted(_get_referenced_types(type_, set(), True), key=lambda type_: type_.type_name)

def _get_referenced_types(type_, visited, top_level):
    if isinstance(type_, TypeStruct):
        if type_.type_name not in visited:
            visited.add(type_.type_name)
            if not top_level:
                yield type_
            for member in type_.members():
                yield from _get_referenced_types(member.type, visited, False)
    elif isinstance(type_, TypeEnum):
        if type_.type_name not in visited:
            visited.add(type_.type_name)
            if not top_level:
                yield type_
    elif isinstance(type_, Typedef):
        if type_.type_name not in visited:
            visited.add(type_.type_name)
            if not top_level:
                yield type_
            yield from _get_referenced_types(type_.type, visited, False)
    elif isinstance(type_, TypeArray):
        yield from _get_referenced_types(type_.type, visited, False)
    elif isinstance(type_, TypeDict):
        yield from _get_referenced_types(type_.type, visited, False)
        yield from _get_referenced_types(type_.key_type, visited, False)
    elif isinstance(type_, ActionModel):
        yield from _get_referenced_types(type_.path_type, visited, True)
        yield from _get_referenced_types(type_.query_type, visited, True)
        yield from _get_referenced_types(type_.input_type, visited, True)
        yield from _get_referenced_types(type_.output_type, visited, True)


class ActionModel:
    """
    TODO
    """

    __slots__ = ('name', 'urls', 'path_type', 'query_type', 'input_type', 'output_type', 'error_type', 'doc', 'doc_group')

    def __init__(self, name, doc=None, doc_group=None):

        #: TODO
        self.name = name

        #: TODO
        self.urls = []

        #: TODO
        self.path_type = TypeStruct(type_name=name + '_path')

        #: TODO
        self.query_type = TypeStruct(type_name=name + '_query')

        #: TODO
        self.input_type = TypeStruct(type_name=name + '_input')

        #: TODO
        self.output_type = TypeStruct(type_name=name + '_output')

        #: TODO
        self.error_type = TypeEnum(type_name=name + '_error')

        #: TODO
        self.doc = [] if doc is None else doc

        #: TODO
        self.doc_group = doc_group

    def input_members(self, include_base_types=True):
        """
        TODO
        """

        yield from chain.from_iterable(
            t.members(include_base_types=include_base_types) for t in (self.path_type, self.query_type, self.input_type)
        )


# Struct member attributes
class StructMemberAttributes:
    """
    TODO
    """

    __slots__ = ('op_eq', 'op_lt', 'op_lte', 'op_gt', 'op_gte',
                 'op_len_eq', 'op_len_lt', 'op_len_lte', 'op_len_gt', 'op_len_gte')

    def __init__(self, op_eq=None, op_lt=None, op_lte=None, op_gt=None, op_gte=None,
                 op_len_eq=None, op_len_lt=None, op_len_lte=None, op_len_gt=None, op_len_gte=None):

        #: TODO
        self.op_eq = op_eq

        #: TODO
        self.op_lt = op_lt

        #: TODO
        self.op_lte = op_lte

        #: TODO
        self.op_gt = op_gt

        #: TODO
        self.op_gte = op_gte

        #: TODO
        self.op_len_eq = op_len_eq

        #: TODO
        self.op_len_lt = op_len_lt

        #: TODO
        self.op_len_lte = op_len_lte

        #: TODO
        self.op_len_gt = op_len_gt

        #: TODO
        self.op_len_gte = op_len_gte

    @staticmethod
    def _format_float(value):
        return f'{value:.6f}'.rstrip('0').rstrip('.')

    def validate(self, value, _member=()):
        """
        TODO
        """

        if self.op_lt is not None and value >= self.op_lt:
            raise _member_error(None, value, _member, constraint_syntax='< ' + self._format_float(self.op_lt))
        if self.op_lte is not None and value > self.op_lte:
            raise _member_error(None, value, _member, constraint_syntax='<= ' + self._format_float(self.op_lte))
        if self.op_gt is not None and value <= self.op_gt:
            raise _member_error(None, value, _member, constraint_syntax='> ' + self._format_float(self.op_gt))
        if self.op_gte is not None and value < self.op_gte:
            raise _member_error(None, value, _member, constraint_syntax='>= ' + self._format_float(self.op_gte))
        if self.op_eq is not None and value != self.op_eq:
            raise _member_error(None, value, _member, constraint_syntax='== ' + self._format_float(self.op_eq))
        if self.op_len_lt is not None and len(value) >= self.op_len_lt:
            raise _member_error(None, value, _member, constraint_syntax='len < ' + self._format_float(self.op_len_lt))
        if self.op_len_lte is not None and len(value) > self.op_len_lte:
            raise _member_error(None, value, _member, constraint_syntax='len <= ' + self._format_float(self.op_len_lte))
        if self.op_len_gt is not None and len(value) <= self.op_len_gt:
            raise _member_error(None, value, _member, constraint_syntax='len > ' + self._format_float(self.op_len_gt))
        if self.op_len_gte is not None and len(value) < self.op_len_gte:
            raise _member_error(None, value, _member, constraint_syntax='len >= ' + self._format_float(self.op_len_gte))
        if self.op_len_eq is not None and len(value) != self.op_len_eq:
            raise _member_error(None, value, _member, constraint_syntax='len == ' + self._format_float(self.op_len_eq))

    def validate_attr(self, allow_value=False, allow_length=False):
        """
        TODO
        """

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


class Typedef:
    """
    TODO
    """

    __slots__ = ('type_name', 'type', 'attr', 'doc')

    def __init__(self, type_, attr=None, type_name=None, doc=None):

        #: TODO
        self.type_name = 'typedef' if type_name is None else type_name

        #: TODO
        self.type = type_

        #: TODO
        self.attr = attr

        #: TODO
        self.doc = [] if doc is None else doc

    @staticmethod
    def base_type(type_):
        """
        TODO
        """

        while isinstance(type_, Typedef):
            type_ = type_.type
        return type_

    def validate_attr(self, attr):
        """
        TODO
        """

        self.type.validate_attr(attr)

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        result = self.type.validate(value, mode, _member)
        if self.attr is not None:
            self.attr.validate(result, _member)
        return result


class StructMember:
    """
    TODO
    """

    __slots__ = ('name', 'type', 'optional', 'nullable', 'attr', 'doc')

    def __init__(self, name, type_, optional=False, nullable=False, attr=None, doc=None):

        #: TODO
        self.name = name

        #: TODO
        self.type = type_

        #: TODO
        self.optional = optional

        #: TODO
        self.nullable = nullable

        #: TODO
        self.attr = attr

        #: TODO
        self.doc = [] if doc is None else doc


class TypeStruct:
    """
    TODO
    """

    __slots__ = ('type_name', 'union', 'base_types', '_members', 'doc')

    def __init__(self, type_name=None, union=False, base_types=None, doc=None):

        #: TODO
        self.type_name = ('union' if union else 'struct') if type_name is None else type_name

        #: TODO
        self.union = union

        #: TODO
        self.base_types = base_types

        self._members = []

        #: TODO
        self.doc = [] if doc is None else doc

    def members(self, include_base_types=True):
        """
        TODO
        """

        if include_base_types and self.base_types is not None:
            return chain(
                chain.from_iterable(Typedef.base_type(base_type).members() for base_type in self.base_types if base_type),
                self._members
            )
        return iter(self._members)

    def add_member(self, name, type_, optional=False, nullable=False, attr=None, doc=None):
        """
        TODO
        """

        member = StructMember(name, type_, optional or self.union, nullable, attr, doc)
        self._members.append(member)
        return member

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, dict):
            value_x = value
        elif mode == ValidationMode.QUERY_STRING and value == '':
            value_x = {}
        else:
            raise _member_error(self, value, _member)

        # Valid union?
        if self.union:
            if len(value_x) != 1:
                raise _member_error(self, value, _member)

        # Result a copy?
        value_copy = None if mode in IMMUTABLE_VALIDATION_MODES else {}

        # Validate all member values
        member_count = 0
        for member in self.members():
            member_name = member.name
            if member_name not in value_x:
                if not member.optional:
                    raise ValidationError(f"Required member {_member_syntax((_member, member_name))!r} missing")
            else:
                member_count += 1
                member_value = value_x[member_name]
                if member.nullable and (member_value is None or \
                        (mode == ValidationMode.QUERY_STRING and not isinstance(member.type, TypeString) and member_value == 'null')):
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
            member_set = {member.name for member in self.members()}
            unknown_value_names = [value_name for value_name in value_x.keys() if value_name not in member_set]
            raise ValidationError(f"Unknown member {_member_syntax((_member, unknown_value_names[0]))!r:.100s}")

        return value if value_copy is None else value_copy


class TypeArray:
    """
    TODO
    """

    __slots__ = ('type', 'attr')

    #: TODO
    type_name = 'array'

    def __init__(self, type_, attr=None):

        #: TODO
        self.type = type_

        #: TODO
        self.attr = attr

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr(allow_length=True)

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, (list, tuple)):
            value_x = value
        elif mode == ValidationMode.QUERY_STRING and value == '':
            value_x = []
        else:
            raise _member_error(self, value, _member)

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


class TypeDict:
    """
    TODO
    """

    __slots__ = ('type', 'attr', 'key_type', 'key_attr')

    #: TODO
    type_name = 'dict'

    def __init__(self, type_, attr=None, key_type=None, key_attr=None):

        #: TODO
        self.type = type_

        #: TODO
        self.attr = attr

        #: TODO
        self.key_type = key_type or TYPE_STRING

        #: TODO
        self.key_attr = key_attr

    @staticmethod
    def valid_key_type(key_type):
        """
        TODO
        """

        key_type_base = Typedef.base_type(key_type)
        return isinstance(key_type_base, (TypeString, TypeEnum))

    def has_default_key_type(self):
        """
        TODO
        """

        return isinstance(self.key_type, TypeString)

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr(allow_length=True)

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, dict):
            value_x = value
        elif mode == ValidationMode.QUERY_STRING and value == '':
            value_x = {}
        else:
            raise _member_error(self, value, _member)

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


class EnumValue:
    """
    TODO
    """

    __slots__ = ('value', 'doc')

    def __init__(self, valueString, doc=None):

        #: TODO
        self.value = valueString

        #: TODO
        self.doc = [] if doc is None else doc

    def __eq__(self, other):
        return self.value == other


class TypeEnum:
    """
    TODO
    """

    __slots__ = ('type_name', 'base_types', '_values', 'doc')

    def __init__(self, type_name='enum', base_types=None, doc=None):

        #: TODO
        self.type_name = type_name

        #: TODO
        self.base_types = base_types

        self._values = []

        #: TODO
        self.doc = [] if doc is None else doc

    def values(self, include_base_types=True):
        """
        TODO
        """

        if include_base_types and self.base_types is not None:
            return chain(
                chain.from_iterable(Typedef.base_type(base_type).values() for base_type in self.base_types if base_type),
                self._values
            )
        return iter(self._values)

    def add_value(self, string, doc=None):
        """
        TODO
        """

        value = EnumValue(string, doc)
        self._values.append(value)
        return value

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, unused_mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate the value
        if value not in self.values():
            raise _member_error(self, value, _member)

        return value


class TypeString:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'string'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr(allow_length=True)

    def validate(self, value, unused_mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate the value
        if not isinstance(value, str):
            raise _member_error(self, value, _member)

        return value


class TypeInt:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'int'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr(allow_value=True)

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, int) and not isinstance(value, bool):
            value_x = value
        elif isinstance(value, (float, Decimal)):
            value_x = int(value)
            if value_x != value:
                raise _member_error(self, value, _member)
        elif mode == ValidationMode.QUERY_STRING and isinstance(value, str):
            try:
                value_x = int(value)
            except:
                raise _member_error(self, value, _member) from None
        else:
            raise _member_error(self, value, _member)

        return value if mode in IMMUTABLE_VALIDATION_MODES else value_x


class TypeFloat:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'float'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr(allow_value=True)

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, float):
            value_x = value
        elif isinstance(value, (int, Decimal)) and not isinstance(value, bool):
            value_x = float(value)
        elif mode == ValidationMode.QUERY_STRING and isinstance(value, str):
            try:
                value_x = float(value)
                if isnan(value_x) or isinf(value_x):
                    raise ValueError()
            except:
                raise _member_error(self, value, _member) from None
        else:
            raise _member_error(self, value, _member)

        return value if mode in IMMUTABLE_VALIDATION_MODES else value_x


class TypeBool:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'bool'

    #: TODO
    VALUES = {
        'true': True,
        'false': False
    }

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, bool):
            return value
        if mode == ValidationMode.QUERY_STRING and isinstance(value, str):
            try:
                return self.VALUES[value]
            except:
                raise _member_error(self, value, _member) from None
        raise _member_error(self, value, _member)


class TypeUuid:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'uuid'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, UUID):
            return value
        if mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, str):
            try:
                return UUID(value)
            except:
                raise _member_error(self, value, _member) from None
        raise _member_error(self, value, _member)


class TypeDate:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'date'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, date):
            return value
        if mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except:
                raise _member_error(self, value, _member) from None
        raise _member_error(self, value, _member)


class TypeDatetime:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'datetime'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()):
        """
        TODO
        """

        # Validate and translate the value
        if isinstance(value, datetime):
            return value
        if mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except:
                raise _member_error(self, value, _member) from None
        raise _member_error(self, value, _member)


class TypeObject:
    """
    TODO
    """

    __slots__ = ()

    #: TODO
    type_name = 'object'

    @staticmethod
    def validate_attr(attr):
        """
        TODO
        """

        attr.validate_attr()

    def validate(self, value, mode=ValidationMode.DEFAULT, _member=()): # pylint: disable=unused-argument
        """
        TODO
        """

        if value is not None:
            return value
        raise _member_error(self, value, _member)


#: TODO
TYPE_BOOL = TypeBool()

#: TODO
TYPE_DATE = TypeDate()

#: TODO
TYPE_DATETIME = TypeDatetime()

#: TODO
TYPE_FLOAT = TypeFloat()

#: TODO
TYPE_INT = TypeInt()

#: TODO
TYPE_OBJECT = TypeObject()

#: TODO
TYPE_STRING = TypeString()

#: TODO
TYPE_UUID = TypeUuid()
