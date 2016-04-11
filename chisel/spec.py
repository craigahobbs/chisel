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

from itertools import chain
import re

from .model import AttributeValidationError, StructMemberAttributes, TypeArray, \
    TYPE_BOOL, TYPE_DATE, TYPE_DATETIME, Typedef, TypeDict, TypeEnum, TYPE_INT, \
    TYPE_FLOAT, TYPE_STRING, TypeStruct, TYPE_UUID


# Action model
class ActionModel(object):
    __slots__ = ('name', 'input_type', 'output_type', 'error_type', 'doc')

    def __init__(self, name, doc=None):
        self.name = name
        self.input_type = TypeStruct(type_name=name + '_input')
        self.output_type = TypeStruct(type_name=name + '_output')
        self.error_type = TypeEnum(type_name=name + '_error')
        self.doc = [] if doc is None else doc


# Spec parser exception
class SpecParserError(Exception):
    __slots__ = ('errors',)

    def __init__(self, errors):
        Exception.__init__(self, '\n'.join(errors))
        self.errors = errors


# Specification language parser class
class SpecParser(object):

    __slots__ = (
        'types',
        'actions',
        'errors',
        '_parse_lines',
        '_parse_filename',
        '_parse_linenum',
        '_action',
        '_action_sections',
        '_type',
        '_doc',
        '_typerefs',
        '_finalize_checks'
    )

    # Spec language regex
    _RE_PART_ID = r'(?:[A-Za-z]\w*)'
    _RE_PART_ATTR_GROUP = r'(?:(?P<op><=|<|>|>=|==)\s*(?P<opnum>-?\d+(?:\.\d+)?)' \
                          r'|(?P<ltype>len)\s*(?P<lop><=|<|>|>=|==)\s*(?P<lopnum>\d+))'
    _RE_PART_ATTR = re.sub(r'\(\?P<[^>]+>', r'(?:', _RE_PART_ATTR_GROUP)
    _RE_PART_ATTRS = r'(?:' + _RE_PART_ATTR + r'(?:\s*,\s*' + _RE_PART_ATTR + r')*)'
    _RE_ATTR_GROUP = re.compile(_RE_PART_ATTR_GROUP)
    _RE_FIND_ATTRS = re.compile(_RE_PART_ATTR + r'(?:\s*,\s*|\s*\Z)')
    _RE_LINE_CONT = re.compile(r'\\s*$')
    _RE_COMMENT = re.compile(r'^\s*(?:#-.*|#(?P<doc>.*))?$')
    _RE_ACTION = re.compile(r'^action\s+(?P<id>' + _RE_PART_ID + r')')
    _RE_PART_BASE_IDS = r'(?:\s*\(\s*(?P<base_ids>' + _RE_PART_ID + r'(?:\s*,\s*' + _RE_PART_ID + r')*)\s*\)\s*)'
    _RE_BASE_IDS_SPLIT = re.compile(r'\s*,\s*')
    _RE_DEFINITION = re.compile(r'^(?P<type>action|struct|union|enum)\s+(?P<id>' + _RE_PART_ID + r')' + _RE_PART_BASE_IDS + r'?\s*$')
    _RE_SECTION = re.compile(r'^\s+(?P<type>input|output|errors)' + _RE_PART_BASE_IDS + r'?\s*$')
    _RE_PART_TYPEDEF = r'(?P<type>' + _RE_PART_ID + r')' \
                       r'(?:\s*\(\s*(?P<attrs>' + _RE_PART_ATTRS + r')\s*\))?' \
                       r'(?:' \
                       r'(?:\s*\[\s*(?P<array>' + _RE_PART_ATTRS + r'?)\s*\])?' \
                       r'|' \
                       r'(?:' \
                       r'\s*:\s*(?P<dictValueType>' + _RE_PART_ID + r')' \
                       r'(?:\s*\(\s*(?P<dictValueAttrs>' + _RE_PART_ATTRS + r')\s*\))?' \
                       r')?' \
                       r'(?:\s*\{\s*(?P<dict>' + _RE_PART_ATTRS + r'?)\s*\})?' \
                       r')' \
                       r'\s+(?P<id>' + _RE_PART_ID + r')'
    _RE_TYPEDEF = re.compile(r'^typedef\s+' + _RE_PART_TYPEDEF + r'\s*$')
    _RE_MEMBER = re.compile(r'^\s+(?P<optional>optional\s+)?(?P<nullable>nullable\s+)?' + _RE_PART_TYPEDEF + r'\s*$')
    _RE_VALUE = re.compile(r'^\s+"?(?P<id>(?<!")' + _RE_PART_ID + r'(?!")|(?<=").*?(?="))"?\s*$')

    # Built-in types
    _TYPES = {
        'string': TYPE_STRING,
        'int': TYPE_INT,
        'float': TYPE_FLOAT,
        'bool': TYPE_BOOL,
        'date': TYPE_DATE,
        'datetime': TYPE_DATETIME,
        'uuid': TYPE_UUID,
    }

    def __init__(self, spec=None):
        self.types = {}
        self.actions = {}
        self.errors = []
        self._typerefs = []
        self._finalize_checks = []
        self._action = None
        self._action_sections = None
        self._type = None
        self._doc = None
        self._parse_lines = None
        self._parse_filename = None
        self._parse_linenum = 0
        if spec is not None:
            self.parse_string(spec)

    # Parse a specification string
    def parse_string(self, spec, filename='', finalize=True):
        self.parse(spec.splitlines(), finalize=finalize, filename=filename)

    # Parse a specification from a collection of spec lines (e.g an input stream)
    def parse(self, lines, filename='', finalize=True):

        # Set the parser state
        self._action = None
        self._type = None
        self._doc = []
        self._parse_lines = lines
        self._parse_filename = filename
        self._parse_linenum = 0

        # Do the work
        self._parse()
        if finalize:
            self.finalize()

    # Finalize parsing (must call after calling parse one or more times - can be repeated)
    def finalize(self):

        # Fixup type refs
        for typeref in self._typerefs:
            typeref(True)
        self._typerefs = []

        # Additional finalization checks
        for finalize_check in self._finalize_checks:
            finalize_check()
        self._finalize_checks = []

        # Raise a parser exception if there are any errors
        if self.errors:
            raise SpecParserError(self.errors)

    # Set a type attribute by name
    def _set_type(self, parent_type, parent_object, parent_type_attr, type_name, type_attr, validate_fn=None):
        filename = self._parse_filename
        linenum = self._parse_linenum

        def set_type(error):
            type_ = self._TYPES.get(type_name) or self.types.get(type_name)
            if type_ is not None:
                error_count = len(self.errors)
                if validate_fn is not None:
                    validate_fn(parent_type, type_, filename, linenum)
                self._validate_attr(type_, type_attr, filename, linenum)
                if error_count == len(self.errors):
                    if isinstance(parent_type_attr, int):
                        parent_object[parent_type_attr] = type_
                    else:
                        setattr(parent_object, parent_type_attr, type_)
            elif error:
                self._error("Unknown member type '" + type_name + "'", filename, linenum)
            return type_

        type_ = set_type(False)
        if type_ is None:
            self._typerefs.append(set_type)

    def _validate_dict_key_type(self, dict_type, key_type, filename, linenum):
        if not dict_type.valid_key_type(key_type):
            self._error('Invalid dictionary key type', filename, linenum)

    def _validate_struct_base_type(self, struct_type, base_type, filename, linenum, def_type=None):
        base_type_base = Typedef.base_type(base_type)
        if not isinstance(base_type_base, TypeStruct) or base_type_base.union != struct_type.union:
            if def_type is None:
                def_type = 'union' if struct_type.union else 'struct'
            self._error('Invalid ' + def_type + " base type '" + base_type.type_name + "'", filename, linenum)

    def _validate_enum_base_type(self, dummy_enum_type, base_type, filename, linenum, def_type=None):
        if not isinstance(Typedef.base_type(base_type), TypeEnum):
            if def_type is None:
                def_type = 'enum'
            self._error('Invalid ' + def_type + " base type '" + base_type.type_name + "'", filename, linenum)

    def _validate_input_base_type(self, *args):
        self._validate_struct_base_type(*args, def_type='action input')

    def _validate_output_base_type(self, *args):
        self._validate_struct_base_type(*args, def_type='action output')

    def _validate_errors_base_type(self, *args):
        self._validate_enum_base_type(*args, def_type='action errors')

    def _set_finalize(self, type_, finalize_fn):
        filename = self._parse_filename
        linenum = self._parse_linenum

        def finalize_check():
            finalize_fn(type_, filename, linenum)

        self._finalize_checks.append(finalize_check)

    def _finalize_circular_base_type(self, type_, filename, linenum):
        is_circular = False
        base_types = {}
        def traverse_base_types(type_):
            if type_.base_types:
                for base_type in (base_type for base_type in type_.base_types if base_type):
                    base_type_name = Typedef.base_type(base_type).type_name
                    base_type_count = base_types[base_type_name] = base_types.get(base_type_name, 0) + 1
                    if base_type_count == 1:
                        traverse_base_types(Typedef.base_type(base_type))
        traverse_base_types(type_)
        for base_type_name, base_type_count in base_types.items():
            if base_type_count != 1:
                is_circular = True
                self._error("Circular base type detected for type '" + base_type_name + "'", filename, linenum)
        return is_circular

    def _finalize_struct_base_type(self, struct_type, filename, linenum):
        if struct_type.base_types is not None and not self._finalize_circular_base_type(struct_type, filename, linenum):
            members = {}
            for member in struct_type.members():
                member_count = members[member.name] = members.get(member.name, 0) + 1
                if member_count == 2:
                    self._error("Redefinition of member '" + member.name + "' from base type", filename, linenum)

    def _finalize_enum_base_type(self, enum_type, filename, linenum):
        if enum_type.base_types is not None and not self._finalize_circular_base_type(enum_type, filename, linenum):
            values = {}
            for value in enum_type.values():
                value_count = values[value.value] = values.get(value.value, 0) + 1
                if value_count == 2:
                    self._error("Redefinition of enumeration value '" + value.value + "' from base type", filename, linenum)

    # Record an error
    def _error(self, msg, filename=None, linenum=None):
        self.errors.append('%s:%d: error: %s' % (filename or self._parse_filename, linenum or self._parse_linenum, msg))

    # Validate a type's attributes
    def _validate_attr(self, type_, attr, filename=None, linenum=None):
        try:
            if attr is not None:
                type_.validate_attr(attr)
        except AttributeValidationError as exc:
            self._error("Invalid attribute '" + exc.attr + "'", filename, linenum)

    # Parse an attributes string
    @classmethod
    def _parse_attr(cls, attrs_string):
        attr = None
        if attrs_string is not None:
            for attr_string in cls._RE_FIND_ATTRS.findall(attrs_string):
                match_attr = cls._RE_ATTR_GROUP.match(attr_string)
                attr_op = match_attr.group('op')
                attr_length_op = match_attr.group('lop') if attr_op is None else None

                if attr is None:
                    attr = StructMemberAttributes()

                if attr_op is not None:
                    attr_value = float(match_attr.group('opnum'))
                    if attr_op == '<':
                        attr.op_lt = attr_value
                    elif attr_op == '<=':
                        attr.op_lte = attr_value
                    elif attr_op == '>':
                        attr.op_gt = attr_value
                    elif attr_op == '>=':
                        attr.op_gte = attr_value
                    else:  # ==
                        attr.op_eq = attr_value
                else:  # attr_length_op is not None:
                    attr_value = int(match_attr.group('lopnum')) # pylint: disable=redefined-variable-type
                    if attr_length_op == '<':
                        attr.op_len_lt = attr_value
                    elif attr_length_op == '<=':
                        attr.op_len_lte = attr_value
                    elif attr_length_op == '>':
                        attr.op_len_gt = attr_value
                    elif attr_length_op == '>=':
                        attr.op_len_gte = attr_value
                    else:  # ==
                        attr.op_len_eq = attr_value
        return attr

    # Construct typedef parts
    def _parse_typedef(self, parent, parent_type_attr, parent_attr_attr, match_typedef):
        array_attrs_string = match_typedef.group('array')
        dict_attrs_string = match_typedef.group('dict')

        # Array member?
        if array_attrs_string is not None:
            value_type_name = match_typedef.group('type')
            value_attr = self._parse_attr(match_typedef.group('attrs'))
            array_type = TypeArray(None, attr=value_attr)
            self._set_type(array_type, array_type, 'type', value_type_name, value_attr)

            array_attr = self._parse_attr(array_attrs_string)
            self._validate_attr(array_type, array_attr)

            setattr(parent, parent_type_attr, array_type)
            setattr(parent, parent_attr_attr, array_attr)

        # Dictionary member?
        elif dict_attrs_string is not None:
            value_type_name = match_typedef.group('dictValueType')
            if value_type_name is not None:
                value_attr = self._parse_attr(match_typedef.group('dictValueAttrs'))
                key_type_name = match_typedef.group('type')
                key_attr = self._parse_attr(match_typedef.group('attrs'))
                dict_type = TypeDict(None, attr=value_attr, key_type=None, key_attr=key_attr)
                self._set_type(dict_type, dict_type, 'type', value_type_name, value_attr)
                self._set_type(dict_type, dict_type, 'key_type', key_type_name, key_attr, self._validate_dict_key_type)
            else:
                value_type_name = match_typedef.group('type')
                value_attr = self._parse_attr(match_typedef.group('attrs'))
                dict_type = TypeDict(None, attr=value_attr)
                self._set_type(dict_type, dict_type, 'type', value_type_name, value_attr)

            dict_attr = self._parse_attr(dict_attrs_string)
            self._validate_attr(dict_type, dict_attr)

            setattr(parent, parent_type_attr, dict_type)
            setattr(parent, parent_attr_attr, dict_attr)

        # Non-container member...
        else:
            member_type_name = match_typedef.group('type')
            member_attr = self._parse_attr(match_typedef.group('attrs'))

            self._set_type(parent, parent, parent_type_attr, member_type_name, member_attr)
            setattr(parent, parent_attr_attr, member_attr)

    # Parse a specification from a stream
    def _parse(self):

        # Process each line
        self._parse_linenum = 0
        line_continuation = []
        for line_part in chain(self._parse_lines, ('',)):
            self._parse_linenum += 1

            # Line continuation?
            line_part_no_continuation = self._RE_LINE_CONT.sub('', line_part)
            if line_continuation or line_part_no_continuation is not line_part:
                line_continuation.append(line_part_no_continuation)
            if line_part_no_continuation is not line_part:
                continue
            elif line_continuation:
                line = ''.join(line_continuation)
                del line_continuation[:]
            else:
                line = line_part

            # Match line syntax
            match_comment = self._RE_COMMENT.search(line)
            match_action = self._RE_ACTION.search(line) if match_comment is None else None
            match_definition = self._RE_DEFINITION.search(line) if match_action is None else None
            match_section = self._RE_SECTION.search(line) if match_definition is None else None
            match_value = self._RE_VALUE.search(line) if match_section is None else None
            match_member = self._RE_MEMBER.search(line) if match_value is None else None
            match_typedef = self._RE_TYPEDEF.search(line) if match_member is None else None

            # Comment?
            if match_comment:
                doc_string = match_comment.group('doc')
                if doc_string is not None:
                    self._doc.append(doc_string.strip())

            # Action?
            elif match_action:
                action_id = match_action.group('id')

                # Action already defined?
                if action_id in self.actions:
                    self._error("Redefinition of action '" + action_id + "'")

                # Create the new action
                self._action = ActionModel(action_id, doc=self._doc)
                self._action_sections = set()
                self._type = None
                self._doc = []
                self.actions[self._action.name] = self._action

            # Definition?
            elif match_definition:
                definition_string = match_definition.group('type')
                definition_id = match_definition.group('id')
                definition_base_ids = match_definition.group('base_ids')
                if definition_base_ids is not None:
                    definition_base_ids = self._RE_BASE_IDS_SPLIT.split(definition_base_ids)

                # Struct definition
                if definition_string == 'struct' or definition_string == 'union':

                    # Type already defined?
                    if definition_id in self._TYPES or definition_id in self.types:
                        self._error("Redefinition of type '" + definition_id + "'")

                    # Create the new struct type
                    self._action = None
                    self._type = TypeStruct(type_name=definition_id, union=(definition_string == 'union'), doc=self._doc)
                    if definition_base_ids is not None:
                        self._type.base_types = [None for _ in definition_base_ids]
                        for base_index, base_id in enumerate(definition_base_ids):
                            self._set_type(self._type, self._type.base_types, base_index, base_id, None, self._validate_struct_base_type)
                        self._set_finalize(self._type, self._finalize_struct_base_type)
                    self._doc = []
                    self.types[self._type.type_name] = self._type

                # Enum definition
                else:  # definition_string == 'enum':

                    # Type already defined?
                    if definition_id in self._TYPES or definition_id in self.types:
                        self._error("Redefinition of type '" + definition_id + "'")

                    # Create the new enum type
                    self._action = None
                    self._type = TypeEnum(type_name=definition_id, doc=self._doc) # pylint: disable=redefined-variable-type
                    if definition_base_ids is not None:
                        self._type.base_types = [None for _ in definition_base_ids]
                        for base_index, base_id in enumerate(definition_base_ids):
                            self._set_type(self._type, self._type.base_types, base_index, base_id, None, self._validate_enum_base_type)
                        self._set_finalize(self._type, self._finalize_enum_base_type)
                    self._doc = []
                    self.types[self._type.type_name] = self._type

            # Section?
            elif match_section:
                section_string = match_section.group('type')
                section_base_ids = match_section.group('base_ids')
                if section_base_ids is not None:
                    section_base_ids = self._RE_BASE_IDS_SPLIT.split(section_base_ids)

                # Not in an action scope?
                if self._action is None:
                    self._error('Action section outside of action scope')
                    continue

                # Action section redefinition?
                if section_string in self._action_sections:
                    self._error('Redefinition of action ' + section_string)
                    self._type = None
                    continue
                self._action_sections.add(section_string)

                # Set the action section type
                if section_string == 'input':
                    self._type = self._action.input_type
                    if section_base_ids is not None:
                        self._type.base_types = [None for _ in section_base_ids]
                        for base_index, base_id in enumerate(section_base_ids):
                            self._set_type(self._action.input_type, self._action.input_type.base_types, base_index, base_id,
                                           None, self._validate_input_base_type)
                        self._set_finalize(self._type, self._finalize_struct_base_type)

                elif section_string == 'output':
                    self._type = self._action.output_type
                    if section_base_ids is not None:
                        self._type.base_types = [None for _ in section_base_ids]
                        for base_index, base_id in enumerate(section_base_ids):
                            self._set_type(self._action.output_type, self._action.output_type.base_types, base_index, base_id,
                                           None, self._validate_output_base_type)
                        self._set_finalize(self._type, self._finalize_struct_base_type)

                else:  # section_string == 'errors':
                    self._type = self._action.error_type
                    if section_base_ids is not None:
                        self._type.base_types = [None for _ in section_base_ids]
                        for base_index, base_id in enumerate(section_base_ids):
                            self._set_type(self._action.error_type, self._action.error_type.base_types, base_index, base_id,
                                           None, self._validate_errors_base_type)
                        self._set_finalize(self._type, self._finalize_enum_base_type)

            # Enum value?
            elif match_value:
                value_string = match_value.group('id')

                # Not in an enum scope?
                if not isinstance(self._type, TypeEnum):
                    self._error('Enumeration value outside of enum scope')
                    continue

                # Redefinition of enum value?
                if value_string in self._type.values(include_base_types=False):
                    self._error("Redefinition of enumeration value '" + value_string + "'")

                # Add the enum value
                self._type.add_value(value_string, doc=self._doc)
                self._doc = []

            # Struct member?
            elif match_member:
                optional = match_member.group('optional') is not None
                nullable = match_member.group('nullable') is not None
                member_name = match_member.group('id')

                # Not in a struct scope?
                if not isinstance(self._type, TypeStruct):
                    self._error('Member definition outside of struct scope')
                    continue

                # Member name already defined?
                if any(member.name == member_name for member in self._type.members(include_base_types=False)):
                    self._error("Redefinition of member '" + member_name + "'")

                # Create the member
                member = self._type.add_member(member_name, None, optional=optional, nullable=nullable, attr=None, doc=self._doc)
                self._parse_typedef(member, 'type', 'attr', match_member)

                self._doc = []

            # Typedef?
            elif match_typedef:
                typedef_name = match_typedef.group('id')

                # Type already defined?
                if typedef_name in self._TYPES or typedef_name in self.types:
                    self._error("Redefinition of type '" + typedef_name + "'")

                # Create the typedef
                typedef = Typedef(None, attr=None, type_name=typedef_name, doc=self._doc)
                self._parse_typedef(typedef, 'type', 'attr', match_typedef)
                self.types[typedef_name] = typedef

                # Reset current action/type
                self._action = None
                self._type = None
                self._doc = []

            # Unrecognized line syntax
            else:
                self._error('Syntax error')
