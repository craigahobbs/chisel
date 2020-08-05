# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel schema type model
"""

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
import importlib.resources
import json
from math import isnan, isinf
import os
from uuid import UUID


# Read the type model JSON resource
with importlib.resources.path('chisel', 'schema.py') as schema_py_path:
    with open(os.path.join(os.path.dirname(schema_py_path), 'static', 'typeModel.json'), 'r') as type_model_json_file:
        _TYPE_MODEL = json.load(type_model_json_file)


def get_type_model():
    """
    Get a copy of the Chisel type model

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
     'Typedef',
     'Types',
     'UserType']

    :returns: The map of referenced user type name to user type model
    """

    return dict(_TYPE_MODEL)


def get_referenced_types(types, type_name, referenced_types=None):
    """
    Get a type's referenced type model

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
        if 'keyType' in dict_:
            _get_referenced_types(types, dict_['keyType'], referenced_types)

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

    if type_name not in types:
        raise ValidationError(f"Unknown type {type_name!r}")
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
            if array_value is not None:
                array_value = _validate_type(types, array_type, array_value, member_fqn_value)
            _validate_attr(array_type, array.get('attr'), array_value, member_fqn_value)
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
        dict_key_type = dict_['keyType'] if 'keyType' in dict_ else {'builtin': 'string'}
        for dict_key, dict_value in value_new.items():
            member_fqn_key = dict_key if member_fqn is None else f'{member_fqn}.{dict_key}'

            # Validate the key
            if dict_key is not None:
                dict_key = _validate_type(types, dict_key_type, dict_key, member_fqn)
            _validate_attr(dict_key_type, dict_.get('keyAttr'), dict_key, member_fqn)

            # Validate the value
            if dict_value is not None:
                dict_value = _validate_type(types, dict_['type'], dict_value, member_fqn_key)
            _validate_attr(dict_['type'], dict_.get('attr'), dict_value, member_fqn_key)

            # Copy the key/value
            value_copy[dict_key] = dict_value

        # Return the validated, transformed copy
        value_new = value_copy

    # User type?
    elif 'user' in type_:
        user_type = types[type_['user']]

        # action?
        if 'action' in user_type:
            raise _member_error(type_, value, member_fqn)

        # typedef?
        if 'typedef' in user_type:
            typedef = user_type['typedef']

            # Validate the value
            if value is not None:
                value_new = _validate_type(types, typedef['type'], value, member_fqn)
            _validate_attr(type_, typedef.get('attr'), value_new, member_fqn)

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

                    # Missing non-optional member?
                    if member_name not in value_new:
                        if not member_optional and not is_union:
                            raise ValidationError(f"Required member {member_fqn_member!r} missing")
                    else:
                        # Validate the member value
                        member_value = value_new[member_name]
                        if member_value is not None:
                            member_value = _validate_type(types, member['type'], member_value, member_fqn_member)
                        _validate_attr(member['type'], member.get('attr'), member_value, member_fqn_member)

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
    if value is None:
        if attr is None or ('nullable' in attr and not attr['nullable']):
            raise _member_error(type_, value, member_fqn)
    elif attr is not None:
        if 'eq' in attr and not value == attr['eq']:
            raise _member_error(type_, value, member_fqn, f'== {attr["eq"]}')
        if 'lt' in attr and not value < attr['lt']:
            raise _member_error(type_, value, member_fqn, f'< {attr["lt"]}')
        if 'lte' in attr and not value <= attr['lte']:
            raise _member_error(type_, value, member_fqn, f'<= {attr["lte"]}')
        if 'gt' in attr and not value > attr['gt']:
            raise _member_error(type_, value, member_fqn, f'> {attr["gt"]}')
        if 'gte' in attr and not value >= attr['gte']:
            raise _member_error(type_, value, member_fqn, f'>= {attr["gte"]}')
        if 'lenEq' in attr and not len(value) == attr['lenEq']:
            raise _member_error(type_, value, member_fqn, f'len == {attr["lenEq"]}')
        if 'lenLT' in attr and not len(value) < attr['lenLT']:
            raise _member_error(type_, value, member_fqn, f'len < {attr["lenLT"]}')
        if 'lenLTE' in attr and not len(value) <= attr['lenLTE']:
            raise _member_error(type_, value, member_fqn, f'len <= {attr["lenLTE"]}')
        if 'lenGT' in attr and not len(value) > attr['lenGT']:
            raise _member_error(type_, value, member_fqn, f'len > {attr["lenGT"]}')
        if 'lenGTE' in attr and not len(value) >= attr['lenGTE']:
            raise _member_error(type_, value, member_fqn, f'len >= {attr["lenGTE"]}')


def validate_types(types):
    """
    Validate a user type model

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

    # Validate with the type model
    validated_types = validate_type(_TYPE_MODEL, 'Types', types)

    # Do additional type model validation
    errors = validate_types_errors(validated_types)
    if errors:
        raise ValidationError('\n'.join(message for _, _, message in sorted(errors)))

    return validated_types


def get_effective_type(types, type_):
    """
    Get a type model's effective type (e.g. typedef int is an int)

    :param dict types: The map of user type name to user type model
    :param dict type_: The type model
    """

    if 'user' in type_ and type_['user'] in types:
        user_type = types[type_['user']]
        if 'typedef' in user_type:
            return get_effective_type(types, user_type['typedef']['type'])
    return type_


def validate_types_errors(types):
    """
    Validate a user type model

    :param dict types: The map of user type name to user type model
    :returns: The list of type name, member name, and error message tuples
    """

    errors = []

    # Check each user type
    for type_name, user_type in types.items():

        # Struct?
        if 'struct' in user_type:
            struct = user_type['struct']

            # Inconsistent type name?
            if type_name != struct['name']:
                errors.append((type_name, None, f'Inconsistent type name {struct["name"]!r} for {type_name!r}'))

            # Has members?
            if 'members' in struct:

                # Check member types and their attributes
                for member in struct['members']:
                    _validate_types_type(errors, types, member['type'], member.get('attr'), struct['name'], member['name'])

                # Check for duplicate members
                member_counts = Counter(member['name'] for member in struct['members'])
                for member_name in (member_name for member_name, member_count in member_counts.items() if member_count > 1):
                    errors.append((type_name, member_name, f'Redefinition of {type_name!r} member {member_name!r}'))

        # Enum?
        elif 'enum' in user_type:
            enum = user_type['enum']

            # Inconsistent type name?
            if type_name != enum['name']:
                errors.append((type_name, None, f'Inconsistent type name {enum["name"]!r} for {type_name!r}'))

            # Check for duplicate enumeration values
            if 'values' in enum:
                value_counts = Counter(value['name'] for value in enum['values'])
                for value_name in (value_name for value_name, value_count in value_counts.items() if value_count > 1):
                    errors.append((type_name, value_name, f'Redefinition of {type_name!r} value {value_name!r}'))

        # Typedef?
        elif 'typedef' in user_type:
            typedef = user_type['typedef']

            # Inconsistent type name?
            if type_name != typedef['name']:
                errors.append((type_name, None, f'Inconsistent type name {typedef["name"]!r} for {type_name!r}'))

            # Check the type and its attributes
            _validate_types_type(errors, types, typedef['type'], typedef.get('attr'), type_name, None)

        # Action?
        elif 'action' in user_type: # pragma: no branch
            action = user_type['action']

            # Inconsistent type name?
            if type_name != action['name']:
                errors.append((type_name, None, f'Inconsistent type name {action["name"]!r} for {type_name!r}'))

            # Check action section types
            for section in ('path', 'query', 'input', 'output', 'errors'):
                if section in action:
                    section_type_name = action[section]

                    # Check the section type
                    _validate_types_type(errors, types, {'user': section_type_name}, None, type_name, None)

            # Compute effective input member counts
            member_counts = Counter()
            member_sections = defaultdict(list)
            for section in ('path', 'query', 'input'):
                if section in action:
                    section_type_name = action[section]
                    if section_type_name in types:
                        section_type = get_effective_type(types, {'user': section_type_name})
                        if 'user' in section_type and 'struct' in types[section_type['user']]:
                            section_struct = types[section_type['user']]['struct']
                            if 'members' in section_struct:
                                member_counts.update(member['name'] for member in section_struct['members'])
                                for member in section_struct['members']:
                                    member_sections[member['name']].append(section_struct['name'])

            # Check for duplicate input members
            for member_name in (member_name for member_name, member_count in member_counts.items() if member_count > 1):
                for section_type in member_sections[member_name]:
                    errors.append((section_type, member_name, f'Redefinition of {section_type!r} member {member_name!r}'))

    return errors


# Map of attribute struct member name to attribute description
_ATTR_TO_TEXT = {
    'eq': '==',
    'lt': '<',
    'lte': '<=',
    'gt': '>',
    'gte': '>=',
    'lenEq': 'len ==',
    'lenLT': 'len <',
    'lenLTE': 'len <=',
    'lenGT': 'len >',
    'lenGTE': 'len >='
}


# Map of type name to valid attribute set
_TYPE_TO_ALLOWED_ATTR = {
    'float': set(['eq', 'lt', 'lte', 'gt', 'gte']),
    'int': set(['eq', 'lt', 'lte', 'gt', 'gte']),
    'string': set(['lenEq', 'lenLT', 'lenLTE', 'lenGT', 'lenGTE']),
    'array': set(['lenEq', 'lenLT', 'lenLTE', 'lenGT', 'lenGTE']),
    'dict': set(['lenEq', 'lenLT', 'lenLTE', 'lenGT', 'lenGTE'])
}


def _validate_types_type(errors, types, type_, attr, type_name, member_name):

    # Helper function to push an error tuple
    def error(message):
        if member_name is not None:
            errors.append((type_name, member_name, f'{message} from {type_name!r} member {member_name!r}'))
        else:
            errors.append((type_name, None, f'{message} from {type_name!r}'))

    # Array?
    if 'array' in type_:
        array = type_['array']

        # Check the type and its attributes
        array_type = get_effective_type(types, array['type'])
        _validate_types_type(errors, types, array_type, array.get('attr'), type_name, member_name)

    # Dict?
    elif 'dict' in type_:
        dict_ = type_['dict']

        # Check the type and its attributes
        dict_type = get_effective_type(types, dict_['type'])
        _validate_types_type(errors, types, dict_type, dict_.get('attr'), type_name, member_name)

        # Check the dict key type and its attributes
        if 'keyType' in dict_:
            dict_key_type = get_effective_type(types, dict_['keyType'])
            _validate_types_type(errors, types, dict_key_type, dict_.get('keyAttr'), type_name, member_name)

            # Valid dict key type (string or enum)
            if not ('builtin' in dict_key_type and dict_key_type['builtin'] == 'string') and \
               not ('user' in dict_key_type and dict_key_type['user'] in types and 'enum' in types[dict_key_type['user']]):
                error('Invalid dictionary key type')

    # User type?
    elif 'user' in type_:
        user_type_name = type_['user']

        # Unknown user type?
        if user_type_name not in types:
            error(f'Unknown type {user_type_name!r}')
        else:
            user_type = types[user_type_name]

            # Action type references not allowed
            if 'action' in user_type:
                error(f'Invalid reference to action {user_type_name!r}')

    # Any not-allowed attributes?
    if attr is not None:
        type_effective = get_effective_type(types, type_)
        type_key = next(iter(type_effective.keys()), None)
        allowed_attr = _TYPE_TO_ALLOWED_ATTR.get(type_effective[type_key] if type_key == 'builtin' else type_key)
        disallowed_attr = set(attr)
        disallowed_attr.discard('nullable')
        if allowed_attr is not None:
            disallowed_attr -= allowed_attr
        if disallowed_attr:
            for attr_key in disallowed_attr:
                attr_value = f'{attr[attr_key]:.6f}'.rstrip('0').rstrip('.')
                attr_text = f'{_ATTR_TO_TEXT[attr_key]} {attr_value}'
                error(f'Invalid attribute {attr_text!r}')
