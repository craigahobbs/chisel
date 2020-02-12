# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from functools import partial
from itertools import chain
import os
import re

from .model import \
    ActionModel, AttributeValidationError, StructMemberAttributes, \
    TYPE_BOOL, TYPE_DATE, TYPE_DATETIME, TYPE_FLOAT, TYPE_INT, TYPE_OBJECT, TYPE_STRING, TYPE_UUID, \
    TypeArray, TypeDict, TypeEnum, TypeStruct, Typedef


class SpecParserError(Exception):
    """
    TODO
    """

    __slots__ = ('errors',)

    def __init__(self, errors):
        super().__init__('\n'.join(errors))

        #: TODO
        self.errors = errors


# Spec language regex
RE_PART_ID = r'(?:[A-Za-z]\w*)'
RE_PART_ATTR_GROUP = \
    r'(?:(?P<op><=|<|>|>=|==)\s*(?P<opnum>-?\d+(?:\.\d+)?)' \
    r'|(?P<ltype>len)\s*(?P<lop><=|<|>|>=|==)\s*(?P<lopnum>\d+))'
RE_PART_ATTR = re.sub(r'\(\?P<[^>]+>', r'(?:', RE_PART_ATTR_GROUP)
RE_PART_ATTRS = r'(?:' + RE_PART_ATTR + r'(?:\s*,\s*' + RE_PART_ATTR + r')*)'
RE_ATTR_GROUP = re.compile(RE_PART_ATTR_GROUP)
RE_FIND_ATTRS = re.compile(RE_PART_ATTR + r'(?:\s*,\s*|\s*\Z)')
RE_LINE_CONT = re.compile(r'\\s*$')
RE_COMMENT = re.compile(r'^\s*(?:#-.*|#(?P<doc>.*))?$')
RE_GROUP = re.compile(r'^group(?:\s+"(?P<group>.+?)")?\s*$')
RE_ACTION = re.compile(r'^action\s+(?P<id>' + RE_PART_ID + r')')
RE_PART_BASE_IDS = r'(?:\s*\(\s*(?P<base_ids>' + RE_PART_ID + r'(?:\s*,\s*' + RE_PART_ID + r')*)\s*\)\s*)'
RE_BASE_IDS_SPLIT = re.compile(r'\s*,\s*')
RE_DEFINITION = re.compile(r'^(?P<type>struct|union|enum)\s+(?P<id>' + RE_PART_ID + r')' + RE_PART_BASE_IDS + r'?\s*$')
RE_SECTION = re.compile(r'^\s+(?P<type>path|query|input|output|errors)' + RE_PART_BASE_IDS + r'?\s*$')
RE_SECTION_PLAIN = re.compile(r'^\s+(?P<type>url)\s*$')
RE_PART_TYPEDEF = \
    r'(?P<type>' + RE_PART_ID + r')' \
    r'(?:\s*\(\s*(?P<attrs>' + RE_PART_ATTRS + r')\s*\))?' \
    r'(?:' \
    r'(?:\s*\[\s*(?P<array>' + RE_PART_ATTRS + r'?)\s*\])?' \
    r'|' \
    r'(?:' \
    r'\s*:\s*(?P<dictValueType>' + RE_PART_ID + r')' \
    r'(?:\s*\(\s*(?P<dictValueAttrs>' + RE_PART_ATTRS + r')\s*\))?' \
    r')?' \
    r'(?:\s*\{\s*(?P<dict>' + RE_PART_ATTRS + r'?)\s*\})?' \
    r')' \
    r'\s+(?P<id>' + RE_PART_ID + r')'
RE_TYPEDEF = re.compile(r'^typedef\s+' + RE_PART_TYPEDEF + r'\s*$')
RE_MEMBER = re.compile(r'^\s+(?P<optional>optional\s+)?(?P<nullable>nullable\s+)?' + RE_PART_TYPEDEF + r'\s*$')
RE_VALUE = re.compile(r'^\s+"?(?P<id>(?<!")' + RE_PART_ID + r'(?!")|(?<=").*?(?="))"?\s*$')
RE_URL = re.compile(r'^\s+(?P<method>[A-Za-z]+|\*)(?:\s+(?P<path>/[^\s]*))?')


# Built-in types
TYPES = {
    'bool': TYPE_BOOL,
    'date': TYPE_DATE,
    'datetime': TYPE_DATETIME,
    'float': TYPE_FLOAT,
    'int': TYPE_INT,
    'object': TYPE_OBJECT,
    'string': TYPE_STRING,
    'uuid': TYPE_UUID
}


# Specification language parser class
class SpecParser:
    """
    TODO
    """

    __slots__ = (
        'types',
        'actions',
        'errors',
        '_parse_lines',
        '_parse_filename',
        '_parse_linenum',
        '_action',
        '_action_sections',
        '_urls',
        '_type',
        '_doc',
        '_doc_group',
        '_typerefs',
        '_finalize_checks'
    )

    def __init__(self, spec=None):

        #: TODO
        self.types = {}

        #: TODO
        self.actions = {}

        #: TODO
        self.errors = []

        self._typerefs = []
        self._finalize_checks = []
        self._action = None
        self._action_sections = None
        self._urls = None
        self._type = None
        self._doc = None
        self._doc_group = None
        self._parse_lines = None
        self._parse_filename = None
        self._parse_linenum = 0
        if spec is not None:
            self.parse_string(spec)

    # Parse a specification from an iterator of spec lines (e.g an input stream)
    def parse(self, lines, filename='', finalize=True):
        """
        TODO
        """

        # Set the parser state
        self._action = None
        self._urls = None
        self._type = None
        self._doc = []
        self._doc_group = None
        self._parse_lines = lines
        self._parse_filename = filename
        self._parse_linenum = 0

        # Do the work
        self._parse()
        if finalize:
            self.finalize()

    # Parse a specification string
    def parse_string(self, spec, filename='', finalize=True):
        """
        TODO
        """

        self.parse(spec.splitlines(), finalize=finalize, filename=filename)

    # Finalize parsing (must call after calling parse one or more times - can be repeated)
    def finalize(self):
        """
        TODO
        """

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

    def load(self, path, spec_ext='.chsl', finalize=True):
        """
        TODO
        """

        if os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    _, ext = os.path.splitext(filename)
                    if ext == spec_ext:
                        spec_path = os.path.join(dirpath, filename)
                        with open(spec_path, 'r', encoding='utf-8') as file_spec:
                            self.parse(file_spec, filename=spec_path, finalize=False)
        else:
            with open(path, 'r', encoding='utf-8') as file_spec:
                self.parse(file_spec, filename=path, finalize=False)

        if finalize:
            self.finalize()

    # Set a type attribute by name
    def _set_type(self, parent_type, parent_object, parent_type_attr, type_name, type_attr, validate_fn=None):
        filename = self._parse_filename
        linenum = self._parse_linenum

        def set_type(error):
            type_ = TYPES.get(type_name) or self.types.get(type_name)
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
            self._error(f"Invalid {def_type} base type '{base_type.type_name}'", filename, linenum)

    def _validate_enum_base_type(self, unused_enum_type, base_type, filename, linenum, def_type=None):
        if not isinstance(Typedef.base_type(base_type), TypeEnum):
            if def_type is None:
                def_type = 'enum'
            self._error(f"Invalid {def_type} base type '{base_type.type_name}'", filename, linenum)

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

    def _finalize_struct_base_type(self, action, struct_type, filename, linenum):
        if struct_type.base_types is not None and not self._finalize_circular_base_type(struct_type, filename, linenum):
            members = {}
            if action is None or struct_type is action.output_type:
                struct_members = struct_type.members
            else:
                struct_members = action.input_members
            for member in struct_members():
                member_count = members[member.name] = members.get(member.name, 0) + 1
                if member_count == 2:
                    self._error("Redefinition of member '" + member.name + "' from base type", filename, linenum)

    def _finalize_enum_base_type(self, unused_action, enum_type, filename, linenum):
        if enum_type.base_types is not None and not self._finalize_circular_base_type(enum_type, filename, linenum):
            values = {}
            for value in enum_type.values():
                value_count = values[value.value] = values.get(value.value, 0) + 1
                if value_count == 2:
                    self._error("Redefinition of enumeration value '" + value.value + "' from base type", filename, linenum)

    # Record an error
    def _error(self, msg, filename=None, linenum=None):
        self.errors.append(f'{filename or self._parse_filename}:{linenum or self._parse_linenum}: error: {msg}')

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
        has_attrs = False
        op_lt, op_lte, op_gt, op_gte, op_eq, op_len_lt, op_len_lte, op_len_gt, op_len_gte, op_len_eq = \
            None, None, None, None, None, None, None, None, None, None
        if attrs_string is not None:
            for attr_string in RE_FIND_ATTRS.findall(attrs_string):
                has_attrs = True
                match_attr = RE_ATTR_GROUP.match(attr_string)
                attr_op = match_attr.group('op')
                attr_length_op = match_attr.group('lop') if attr_op is None else None

                if attr_op is not None:
                    attr_value = float(match_attr.group('opnum'))
                    if attr_op == '<':
                        op_lt = attr_value
                    elif attr_op == '<=':
                        op_lte = attr_value
                    elif attr_op == '>':
                        op_gt = attr_value
                    elif attr_op == '>=':
                        op_gte = attr_value
                    else:  # ==
                        op_eq = attr_value
                else:  # attr_length_op is not None:
                    attr_value = int(match_attr.group('lopnum'))
                    if attr_length_op == '<':
                        op_len_lt = attr_value
                    elif attr_length_op == '<=':
                        op_len_lte = attr_value
                    elif attr_length_op == '>':
                        op_len_gt = attr_value
                    elif attr_length_op == '>=':
                        op_len_gte = attr_value
                    else:  # ==
                        op_len_eq = attr_value

        if not has_attrs:
            return None
        return StructMemberAttributes(op_eq, op_lt, op_lte, op_gt, op_gte, op_len_eq, op_len_lt, op_len_lte, op_len_gt, op_len_gte)

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
            line_part_no_continuation = RE_LINE_CONT.sub('', line_part)
            if line_continuation or line_part_no_continuation is not line_part:
                line_continuation.append(line_part_no_continuation)
            if line_part_no_continuation is not line_part:
                continue
            if line_continuation:
                line = ''.join(line_continuation)
                del line_continuation[:]
            else:
                line = line_part

            # Match syntax
            match_name, match = 'comment', RE_COMMENT.search(line)
            if match is None:
                match_name, match = 'group', RE_GROUP.search(line)
            if match is None:
                match_name, match = 'action', RE_ACTION.search(line)
            if match is None:
                match_name, match = 'definition', RE_DEFINITION.search(line)
            if match is None and self._action is not None:
                match_name, match = 'section', RE_SECTION.search(line)
            if match is None and self._action is not None:
                match_name, match = 'section_plain', RE_SECTION_PLAIN.search(line)
            if match is None and isinstance(self._type, TypeEnum):
                match_name, match = 'value', RE_VALUE.search(line)
            if match is None and isinstance(self._type, TypeStruct):
                match_name, match = 'member', RE_MEMBER.search(line)
            if match is None and self._urls is not None:
                match_name, match = 'url', RE_URL.search(line)
            if match is None:
                match_name, match = 'typedef', RE_TYPEDEF.search(line)
            if match is None:
                match_name = None

            # Comment?
            if match_name == 'comment':
                doc_string = match.group('doc')
                if doc_string is not None:
                    self._doc.append(doc_string)

            # Documentation group?
            elif match_name == 'group':
                doc_group = match.group('group')
                if doc_group is not None:
                    self._doc_group = doc_group.strip()
                else:
                    self._doc_group = None

            # Action?
            elif match_name == 'action':
                action_id = match.group('id')

                # Action already defined?
                if action_id in self.actions:
                    self._error("Redefinition of action '" + action_id + "'")

                # Create the new action
                self._action = ActionModel(action_id, doc=self._doc, doc_group=self._doc_group)
                self._action_sections = set()
                self._urls = None
                self._type = None
                self._doc = []
                self.actions[self._action.name] = self._action

            # Definition?
            elif match_name == 'definition':
                definition_string = match.group('type')
                definition_id = match.group('id')
                definition_base_ids = match.group('base_ids')
                if definition_base_ids is not None:
                    definition_base_ids = RE_BASE_IDS_SPLIT.split(definition_base_ids)

                # Struct definition
                if definition_string in ('struct', 'union'):

                    # Type already defined?
                    if definition_id in TYPES or definition_id in self.types:
                        self._error("Redefinition of type '" + definition_id + "'")

                    # Create the new struct type
                    self._action = None
                    self._urls = None
                    self._type = TypeStruct(type_name=definition_id, union=(definition_string == 'union'), doc=self._doc)
                    if definition_base_ids is not None:
                        self._type.base_types = [None for _ in definition_base_ids]
                        for base_index, base_id in enumerate(definition_base_ids):
                            self._set_type(self._type, self._type.base_types, base_index, base_id, None, self._validate_struct_base_type)
                        self._finalize_checks.append(
                            partial(self._finalize_struct_base_type, None, self._type, self._parse_filename, self._parse_linenum)
                        )
                    self._doc = []
                    self.types[self._type.type_name] = self._type

                # Enum definition
                else:  # definition_string == 'enum':

                    # Type already defined?
                    if definition_id in TYPES or definition_id in self.types:
                        self._error("Redefinition of type '" + definition_id + "'")

                    # Create the new enum type
                    self._action = None
                    self._urls = None
                    self._type = TypeEnum(type_name=definition_id, doc=self._doc)
                    if definition_base_ids is not None:
                        self._type.base_types = [None for _ in definition_base_ids]
                        for base_index, base_id in enumerate(definition_base_ids):
                            self._set_type(self._type, self._type.base_types, base_index, base_id, None, self._validate_enum_base_type)
                        self._finalize_checks.append(
                            partial(self._finalize_enum_base_type, None, self._type, self._parse_filename, self._parse_linenum)
                        )
                    self._doc = []
                    self.types[self._type.type_name] = self._type

            # Section?
            elif match_name == 'section':
                section_string = match.group('type')
                section_base_ids = match.group('base_ids')
                if section_base_ids is not None:
                    section_base_ids = RE_BASE_IDS_SPLIT.split(section_base_ids)

                # Action section redefinition?
                if section_string in self._action_sections:
                    self._error(f'Redefinition of action {section_string}')
                self._action_sections.add(section_string)

                # Set the action section type
                self._urls = None
                if section_string == 'path':
                    self._type = self._action.path_type
                    validate_base_type_fn, finalize_base_type_fn = self._validate_struct_base_type, self._finalize_struct_base_type
                elif section_string == 'query':
                    self._type = self._action.query_type
                    validate_base_type_fn, finalize_base_type_fn = self._validate_struct_base_type, self._finalize_struct_base_type
                elif section_string == 'input':
                    self._type = self._action.input_type
                    validate_base_type_fn, finalize_base_type_fn = self._validate_struct_base_type, self._finalize_struct_base_type
                elif section_string == 'output':
                    self._type = self._action.output_type
                    validate_base_type_fn, finalize_base_type_fn = self._validate_struct_base_type, self._finalize_struct_base_type
                else: # section_string == 'errors':
                    self._type = self._action.error_type
                    validate_base_type_fn, finalize_base_type_fn = self._validate_enum_base_type, self._finalize_enum_base_type

                if section_base_ids is not None:
                    self._type.base_types = [None for _ in section_base_ids]
                    for base_index, base_id in enumerate(section_base_ids):
                        self._set_type(
                            self._type, self._type.base_types, base_index, base_id, None,
                            partial(validate_base_type_fn, def_type=f'action {section_string}')
                        )
                    self._finalize_checks.append(
                        partial(finalize_base_type_fn, self._action, self._type, self._parse_filename, self._parse_linenum)
                    )

            # Plain section?
            elif match_name == 'section_plain':
                section_string = match.group('type')

                # Action section redefinition?
                if section_string in self._action_sections:
                    self._error(f'Redefinition of action {section_string}')
                self._action_sections.add(section_string)

                # Set the action section data
                assert section_string == 'url'
                self._urls = self._action.urls
                self._type = None

            # Enum value?
            elif match_name == 'value':
                value_string = match.group('id')

                # Redefinition of enum value?
                if value_string in self._type.values(include_base_types=False):
                    self._error("Redefinition of enumeration value '" + value_string + "'")

                # Add the enum value
                self._type.add_value(value_string, doc=self._doc)
                self._doc = []

            # Struct member?
            elif match_name == 'member':
                optional = match.group('optional') is not None
                nullable = match.group('nullable') is not None
                member_name = match.group('id')

                # Member name already defined?
                if self._action is None or self._type is self._action.output_type:
                    struct_members = self._type.members
                else:
                    struct_members = self._action.input_members
                if member_name in (mem.name for mem in struct_members(include_base_types=False)):
                    self._error("Redefinition of member '" + member_name + "'")

                # Create the member
                member = self._type.add_member(member_name, None, optional=optional, nullable=nullable, attr=None, doc=self._doc)
                self._parse_typedef(member, 'type', 'attr', match)
                self._doc = []

            # URL?
            elif match_name == 'url':
                method = match.group('method')
                path = match.group('path')
                url = (method if method != '*' else None, path)

                # Duplicate URL?
                if url in self._urls:
                    self._error(f'Duplicate URL: {method} {"" if path is None else path}')

                # Add the URL
                self._urls.append(url)
                self._doc = []

            # Typedef?
            elif match_name == 'typedef':
                typedef_name = match.group('id')

                # Type already defined?
                if typedef_name in TYPES or typedef_name in self.types:
                    self._error("Redefinition of type '" + typedef_name + "'")

                # Create the typedef
                typedef = Typedef(None, attr=None, type_name=typedef_name, doc=self._doc)
                self._parse_typedef(typedef, 'type', 'attr', match)
                self.types[typedef_name] = typedef

                # Reset current action/type
                self._action = None
                self._urls = None
                self._type = None
                self._doc = []

            # Unrecognized line syntax
            else:
                self._error('Syntax error')
