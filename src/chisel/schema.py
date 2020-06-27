# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel schema type model
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from math import isnan, isinf
from uuid import UUID

from .spec import SpecParser, SpecParserError


# The Chisel schema type model types dict
_TYPE_MODEL = SpecParser('''

# Map of user type name to user type model
typedef UserType{len > 0} TypeDict

# Union representing a member type
union Type

    # A built-in type
    BuiltinType builtin

    # An array type
    Array array

    # A dictionary type
    Dict dict

    # A user type name
    string user

# A type or member's attributes
struct Attributes

    # The value is equal
    optional float eq

    # The value is less than
    optional float lt

    # The value is less than or equal to
    optional float lte

    # The value is greater than
    optional float gt

    # The value is greater than or equal to
    optional float gte

    # The length is equal to
    optional int len_eq

    # The length is less-than
    optional int len_lt

    # The length is less than or equal to
    optional int len_lte

    # The length is greater than
    optional int len_gt

    # The length is greater than or equal to
    optional int len_gte

# The built-in type enumeration
enum BuiltinType

    # The string type
    string

    # The integer type
    int

    # The float type
    float

    # The boolean type
    bool

    # A date formatted as an ISO-8601 date string
    date

    # A date/time formatted as an ISO-8601 date/time string
    datetime

    # A UUID formatted as string
    uuid

    # An object of any type
    object

# An array type
struct Array

    # The contained type
    Type type

    # The contained type's attributes
    optional Attributes attr

# A dictionary type
struct Dict

    # The contained key type
    Type type

    # The contained key type's attributes
    optional Attributes attr

    # The contained value type
    optional Type key_type

    # The contained value type's attributes
    optional Attributes key_attr

# A user type
union UserType

    # An enumeration type
    Enum enum

    # A struct type
    Struct struct

    # A type definition
    Typedef typedef

    # A JSON web API (not reference-able)
    Action action

# An enumeration type
struct Enum

    # The enum type name
    string name

    # The documentation markdown text
    optional string doc

    # The enumeration values
    optional EnumValue[len > 0] values

# An enumeration type value
struct EnumValue

    # The value string
    string name

    # The documentation markdown text
    optional string doc

# A struct type
struct Struct

    # The struct type name
    string name

    # The documentation markdown text
    optional string doc

    # The struct members
    optional StructMember[len > 0] members

    # If true, the struct is a union and exactly one of the optional members is present.
    optional bool union

# A struct member
struct StructMember

    # The member name
    string name

    # The documentation markdown text
    optional string doc

    # The member type
    Type type

    # The member type attributes
    optional Attributes attr

    # If true, the member is optional and may not be present.
    optional bool optional

    # If true, the member may be null.
    optional bool nullable

# A typedef type
struct Typedef

    # The typedef type name
    string name

    # The documentation markdown text
    optional string doc

    # The typedef's type
    Type type

    # The typedef's type attributes
    optional Attributes attr

# A JSON web service API
struct Action

    # The action name
    string name

    # The documentation markdown text
    optional string doc

    # The action's documentation group name
    optional string doc_group

    # The action's URLs
    optional ActionURL[len > 0] urls

    # The path parameters struct type name
    optional string path

    # The query parameters struct type name
    optional string query

    # The content body struct type name
    optional string input

    # The response body struct type name
    optional string output

    # The custom error response codes enum type name
    optional string errors

# An action URL model
struct ActionURL

    # The HTTP method. If not provided, matches all HTTP methods.
    optional string method

    # The URL path. If not provided, uses the default URL path of "/<action_name>".
    optional string path
''').types


def get_type_model():
    """
    Get a copy of the Chisel type model types dict

    >>> import chisel
    >>> from pprint import pprint
    >>> pprint(sorted(chisel.get_type_model().keys()))
    ['Action',
     'ActionURL',
     'Array',
     'Attributes',
     'BuiltinType',
     'Dict',
     'Enum',
     'EnumValue',
     'Struct',
     'StructMember',
     'Type',
     'TypeDict',
     'Typedef',
     'UserType']
    """

    return dict(_TYPE_MODEL)


def get_referenced_types(types, type_name, referenced_types=None):
    """
    Get a type's referenced types dict

    >>> import chisel
    >>> types = {
    ...     'Struct1': {
    ...         'struct': {
    ...             'name': 'Struct1',
    ...             'members': [
    ...                 {'name': 'a', 'type': {'user': 'Struct2'}}
    ...             ]
    ...         }
    ...     },
    ...     'Struct2': {
    ...         'struct': {
    ...             'name': 'Struct2',
    ...             'members': [
    ...                 {'name': 'b', 'type': {'builtin': 'int'}}
    ...             ]
    ...         }
    ...     },
    ...     'MyTypedef': {
    ...         'typedef': {
    ...             'name': 'MyTypedef',
    ...             'type': {'builtin': 'int'},
    ...             'attr': {'lt': 0}
    ...         }
    ...     }
    ... }
    >>> chisel.validate_types(types) # doctest: +SKIP
    >>> from pprint import pprint
    >>> pprint(chisel.get_referenced_types(types, 'Struct1'))
    {'Struct1': {'struct': {'members': [{'name': 'a', 'type': {'user': 'Struct2'}}],
                            'name': 'Struct1'}},
     'Struct2': {'struct': {'members': [{'name': 'b', 'type': {'builtin': 'int'}}],
                            'name': 'Struct2'}}}

    :param dict types: The map of user type name to user type model
    :param str type_name: The type name
    :param dict referenced_types: An optional map of referenced user type name to user type
    :returns: The map of referenced user type name to user type model
    """

    return _get_referenced_types(types, {'user': type_name}, referenced_types)


def _get_referenced_types(types, type_, referenced_types=None):

    # Create the referenced types dict, if necessary
    if referenced_types is None:
        referenced_types = {}

    # Array?
    if 'array' in type_:
        array = type_['array']
        _get_referenced_types(types, array['type'], referenced_types)

    # Dict?
    elif 'dict' in type_:
        dict_ = type_['dict']
        _get_referenced_types(types, dict_['type'], referenced_types)
        if 'key_type' in dict_:
            _get_referenced_types(types, dict_['key_type'], referenced_types)

    # User type?
    elif 'user' in type_:
        type_name = type_['user']

        # Already encountered?
        if type_name not in referenced_types:
            user_type = types[type_name]
            referenced_types[type_name] = user_type

            # Struct?
            if 'struct' in user_type:
                struct = user_type['struct']
                if 'members' in struct:
                    for member in struct['members']:
                        _get_referenced_types(types, member['type'], referenced_types)

            # Typedef?
            elif 'typedef' in user_type:
                typedef = user_type['typedef']
                _get_referenced_types(types, typedef['type'], referenced_types)

            # Action?
            elif 'action' in user_type:
                action = user_type['action']
                if 'path' in action:
                    _get_referenced_types(types, {'user': action['path']}, referenced_types)
                if 'query' in action:
                    _get_referenced_types(types, {'user': action['query']}, referenced_types)
                if 'input' in action:
                    _get_referenced_types(types, {'user': action['input']}, referenced_types)
                if 'output' in action:
                    _get_referenced_types(types, {'user': action['output']}, referenced_types)
                if 'errors' in action:
                    _get_referenced_types(types, {'user': action['errors']}, referenced_types)

    return referenced_types


class ValidationError(Exception):
    """
    Chisel type model validation error

    :param str msg: The error message
    :param member_fqn: The fully qualified member name or None
    :type member_fqn: str or None
    """

    __slots__ = ('member',)

    def __init__(self, msg, member_fqn=None):
        super().__init__(msg)

        #: The fully qualified member name or None
        self.member = member_fqn


def validate_types(types):
    """
    Validate a user type model dict

    >>> import chisel
    >>> chisel.validate_types({
    ...     'Struct1': {
    ...         'struct': {
    ...             'name': 'Struct1',
    ...             'members': [
    ...                 {'name': 'a', 'type': {'user': 'Struct2'}}
    ...             ]
    ...         }
    ...     }
    ... }) # doctest: +SKIP
    >>> try:
    ...     chisel.validate_types({
    ...         'MyStruct': {
    ...             'struct': {}
    ...         }
    ...     })
    ... except Exception as exc:
    ...     str(exc)
    "Required member 'MyStruct.struct.name' missing"

    :param dict types: The map of user type name to user type model
    :raises ValidationError: A validation error occurred
    """

    validated_types = validate_type(_TYPE_MODEL, 'TypeDict', types)
    try:
        SpecParser.validate_types(types)
    except SpecParserError as exc:
        raise ValidationError('\n'.join(exc.errors))
    return validated_types


def validate_type(types, type_name, value, member_fqn=None):
    """
    Type-validate a value using the Chisel user type model. Container values are duplicated since some member types are
    transformed during validation.

    >>> import chisel
    >>> types = {
    ...     'Struct1': {
    ...         'struct': {
    ...             'name': 'Struct1',
    ...             'members': [
    ...                 {'name': 'a', 'type': {'user': 'Struct2'}}
    ...             ]
    ...         }
    ...     },
    ...     'Struct2': {
    ...         'struct': {
    ...             'name': 'Struct2',
    ...             'members': [
    ...                 {'name': 'b', 'type': {'array': {'type': {'builtin': 'int'}}}}
    ...             ]
    ...         }
    ...     }
    ... }
    >>> chisel.validate_types(types) # doctest: +SKIP
    >>> chisel.validate_type(types, 'Struct1', {'a': {'b': [5, '7']}})
    {'a': {'b': [5, 7]}}

    >>> try:
    ...     chisel.validate_type(types, 'Struct1', {'a': {'b': [5, 'abc']}})
    ... except chisel.ValidationError as exc:
    ...     str(exc)
    "Invalid value 'abc' (type 'str') for member 'a.b.1', expected type 'int'"

    :param dict types: The map of user type name to user type model
    :param str type_name: The type name
    :param object value: The value object to validate
    :param str member_fqn: The fully-qualified member name
    :returns: The validated, transformed value object
    :raises ValidationError: A validation error occurred
    """

    return _validate_type(types, {'user': type_name}, value, member_fqn)


def _validate_type(types, type_, value, member_fqn=None):
    value_new = value

    # Built-in type?
    if 'builtin' in type_:
        builtin = type_['builtin']

        # string?
        if builtin == 'string':

            # Not a string?
            if not isinstance(value, str):
                raise _member_error(type_, value, member_fqn)

        # int?
        elif builtin == 'int':

            # Convert string, float, or Decimal?
            if isinstance(value, (str, float, Decimal)):
                try:
                    value_new = int(value)
                    if not isinstance(value, str) and value_new != value:
                        raise ValueError()
                except ValueError:
                    raise _member_error(type_, value, member_fqn) from None

            # Not an int?
            elif not isinstance(value, int) or isinstance(value, bool):
                raise _member_error(type_, value, member_fqn)

        # float?
        elif builtin == 'float':

            # Convert string, int, or Decimal?
            if isinstance(value, (str, int, Decimal)) and not isinstance(value, bool):
                try:
                    value_new = float(value)
                    if isnan(value_new) or isinf(value_new):
                        raise ValueError()
                except ValueError:
                    raise _member_error(type_, value, member_fqn) from None

            # Not a float?
            elif not isinstance(value, float):
                raise _member_error(type_, value, member_fqn)

        # bool?
        elif builtin == 'bool':

            # Convert string?
            if isinstance(value, str):
                if value == 'true':
                    value_new = True
                elif value == 'false':
                    value_new = False
                else:
                    raise _member_error(type_, value, member_fqn)

            # Not a bool?
            elif not isinstance(value, bool):
                raise _member_error(type_, value, member_fqn)

        # date?
        elif builtin == 'date':

            # Convert string?
            if isinstance(value, str):
                try:
                    value_new = datetime.fromisoformat(value).date()
                except ValueError:
                    raise _member_error(type_, value, member_fqn)

            # Not a date?
            elif not isinstance(value, date) or isinstance(value, datetime):
                raise _member_error(type_, value, member_fqn)

        # datetime?
        elif builtin == 'datetime':

            # Convert string?
            if isinstance(value, str):
                try:
                    value_new = datetime.fromisoformat(value)
                except ValueError:
                    raise _member_error(type_, value, member_fqn)

                # No timezone?
                if value_new.tzinfo is None:
                    value_new = value_new.replace(tzinfo=timezone.utc)

            # Not a datetime?
            elif not isinstance(value, datetime):
                raise _member_error(type_, value, member_fqn)

        # uuid?
        elif builtin == 'uuid':

            # Convert string?
            if isinstance(value, str):
                try:
                    value_new = UUID(value)
                except ValueError:
                    raise _member_error(type_, value, member_fqn)

            # Not a UUID?
            elif not isinstance(value, UUID):
                raise _member_error(type_, value, member_fqn)

        # object?
        elif builtin == 'object':

            # None?
            if value is None:
                raise _member_error(type_, value, member_fqn)

    # array?
    elif 'array' in type_:

        # Valid value type?
        array = type_['array']
        array_type = array['type']
        if isinstance(value, str) and value == '':
            value_new = []
        elif not isinstance(value, (list, tuple)):
            raise _member_error(type_, value, member_fqn)

        # Validate the list contents
        value_copy = []
        for ix_array_value, array_value in enumerate(value_new):
            member_fqn_value = f'{ix_array_value}' if member_fqn is None else f'{member_fqn}.{ix_array_value}'
            array_value = _validate_type(types, array_type, array_value, member_fqn_value)
            if 'attr' in array:
                _validate_attr(array_type, array['attr'], array_value, member_fqn_value)
            value_copy.append(array_value)

        # Return the validated, transformed copy
        value_new = value_copy

    # dict?
    elif 'dict' in type_:

        # Valid value type?
        dict_ = type_['dict']
        if isinstance(value, str) and value == '':
            value_new = {}
        elif not isinstance(value, dict):
            raise _member_error(type_, value, member_fqn)

        # Validate the dict key/value pairs
        value_copy = {}
        dict_key_type = dict_['key_type'] if 'key_type' in dict_ else {'builtin': 'string'}
        for dict_key, dict_value in value_new.items():
            member_fqn_key = dict_key if member_fqn is None else f'{member_fqn}.{dict_key}'

            # Validate the key
            _validate_type(types, dict_key_type, dict_key, member_fqn)
            if 'key_attr' in dict_:
                _validate_attr(dict_key_type, dict_['key_attr'], dict_key, member_fqn)

            # Validate the value
            dict_value = _validate_type(types, dict_['type'], dict_value, member_fqn_key)
            if 'attr' in dict_:
                _validate_attr(dict_['type'], dict_['attr'], dict_value, member_fqn_key)

            # Copy the key/value
            value_copy[dict_key] = dict_value

        # Return the validated, transformed copy
        value_new = value_copy

    # User type?
    elif 'user' in type_:
        user_type = types[type_['user']]

        # typedef?
        if 'typedef' in user_type:
            typedef = user_type['typedef']

            # Validate the value
            value_new = _validate_type(types, typedef['type'], value, member_fqn)
            if 'attr' in typedef:
                _validate_attr(type_, typedef['attr'], value_new, member_fqn)

        # enum?
        elif 'enum' in user_type:
            enum = user_type['enum']

            # Not a valid enum value?
            if 'values' not in enum or value not in (enum_value['name'] for enum_value in enum['values']):
                raise _member_error(type_, value, member_fqn)

        # struct?
        elif 'struct' in user_type:
            struct = user_type['struct']

            # Valid value type?
            if isinstance(value, str) and value == '':
                value_new = {}
            elif not isinstance(value, dict):
                raise _member_error({'user': struct['name']}, value, member_fqn)

            # Valid union?
            is_union = struct.get('union', False)
            if is_union:
                if len(value) != 1:
                    raise _member_error({'user': struct['name']}, value, member_fqn)

            # Validate the struct members
            value_copy = {}
            if 'members' in struct:
                for member in struct['members']:
                    member_name = member['name']
                    member_fqn_member = member_name if member_fqn is None else f'{member_fqn}.{member_name}'
                    member_optional = member.get('optional', False)
                    member_nullable = member.get('nullable', False)

                    # Missing non-optional member?
                    if member_name not in value:
                        if not member_optional and not is_union:
                            raise ValidationError(f"Required member {member_fqn_member!r} missing")
                    else:
                        # Validate the member value
                        member_value = value_new[member_name]
                        if not (member_nullable and member_value is None):
                            member_value = _validate_type(types, member['type'], member_value, member_fqn_member)
                            if 'attr' in member:
                                _validate_attr(member['type'], member['attr'], member_value, member_fqn_member)

                        # Copy the validated member
                        value_copy[member_name] = member_value

            # Any unknown members?
            if len(value_copy) != len(value_new):
                if 'members' in struct:
                    member_set = {member['name'] for member in struct['members']}
                    unknown_key = next(value_name for value_name in value_new.keys() if value_name not in member_set) # pragma: no branch
                else:
                    unknown_key = next(value_name for value_name in value_new.keys()) # pragma: no branch
                unknown_fqn = unknown_key if member_fqn is None else f'{member_fqn}.{unknown_key}'
                raise ValidationError(f"Unknown member {unknown_fqn!r:.100s}")

            # Return the validated, transformed copy
            value_new = value_copy

    return value_new


def _member_error(type_, value, member_fqn, attr=None):
    member_part = f" for member {member_fqn!r}" if member_fqn else ''
    type_name = type_['builtin'] if 'builtin' in type_ else (
        'array' if 'array' in type_ else ('dict' if 'dict' in type_ else type_['user']))
    attr_part = f' [{attr}]' if attr else ''
    msg = f"Invalid value {value!r:.1000s} (type {value.__class__.__name__!r}){member_part}, expected type {type_name!r}{attr_part}"
    return ValidationError(msg, member_fqn)


def _validate_attr(type_, attr, value, member_fqn):

    def attr_error(attr_key, attr_str):
        attr_value = f'{attr[attr_key]:.6f}'.rstrip('0').rstrip('.')
        raise _member_error(type_, value, member_fqn, f'{attr_str} {attr_value}')

    if 'eq' in attr and not value == attr['eq']:
        attr_error('eq', '==')
    if 'lt' in attr and not value < attr['lt']:
        attr_error('lt', '<')
    if 'lte' in attr and not value <= attr['lte']:
        attr_error('lte', '<=')
    if 'gt' in attr and not value > attr['gt']:
        attr_error('gt', '>')
    if 'gte' in attr and not value >= attr['gte']:
        attr_error('gte', '>=')
    if 'len_eq' in attr and not len(value) == attr['len_eq']:
        attr_error('len_eq', 'len ==')
    if 'len_lt' in attr and not len(value) < attr['len_lt']:
        attr_error('len_lt', 'len <')
    if 'len_lte' in attr and not len(value) <= attr['len_lte']:
        attr_error('len_lte', 'len <=')
    if 'len_gt' in attr and not len(value) > attr['len_gt']:
        attr_error('len_gt', 'len >')
    if 'len_gte' in attr and not len(value) >= attr['len_gte']:
        attr_error('len_gte', 'len >=')
