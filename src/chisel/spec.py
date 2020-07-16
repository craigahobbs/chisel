# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel schema specification language parser
"""

from itertools import chain
import os
import re

from .schema import get_effective_type, validate_types_errors


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
RE_SECTION_PLAIN = re.compile(r'^\s+(?P<type>urls)\s*$')
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


class SpecParserError(Exception):
    """
    Chisel specification language parser exception

    :param list(str) errors: The list of error strings
    """

    __slots__ = ('errors',)

    def __init__(self, errors):
        super().__init__('\n'.join(errors))

        #: The list of error strings
        self.errors = errors


class SpecParser:
    """
    The parser class for the Chisel specification language. Parsing can occur at initialization time or by calling the
    :meth:`~chisel.SpecParser.parse_string` method, which can be called repeatedly.

    :param str spec: An optional specification string to parse
    :param dict types: An optional map of user type name to user type model
    :raises SpecParserError: A parsing error occurred
    """

    __slots__ = ('types', '_errors', '_filepos', '_bases')

    #: Built-in types
    BUILTIN_TYPES = {'bool', 'date', 'datetime', 'float', 'int', 'object', 'string', 'uuid'}

    def __init__(self, spec=None, types=None):

        #: The dictionary of user type name to user type model
        self.types = {} if types is None else types

        self._errors = set()
        self._filepos = {}
        self._bases = {}

        # Parse the specification string, if any
        if spec is not None:
            self.parse_string(spec)

    @property
    def errors(self):
        """
        The list of parser errors
        """

        return [error for _, _, error in sorted(self._errors)]

    def finalize(self):
        """
        Finalize a parsing operation. You only need to call this method if you set :meth:`~chisel.SpecParser.parse`
        "finalize" argument to False.

        :raises SpecParserError: If type name resolution fails
        """

        # Do the finalization
        self._finalize_bases()
        for type_name, member_name, error_msg in validate_types_errors(self.types):
            self._error(error_msg, *self._get_filepos(type_name, member_name))

        # Raise a parser exception if there are any errors
        if self._errors:
            raise SpecParserError(self.errors)

    def load(self, path, spec_ext='.chsl', finalize=True):
        """
        Recursively load and parse specification files. This method can be called repeatedly.

        :param str path: Directory or file path from which to load and parse specification files
        :param str spec_ext: The specification file extension.  The default specification file extension is ".chsl".
        :param bool finalize: If True, resolve names after parsing. Set this argument to False when bulk-parsing related
            specification files. Be sure to call :meth:`~chisel.SpecParser.finalize` when finished.
        :raises SpecParserError: A parsing error occurred
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

    def parse_string(self, spec, filename='', finalize=True):
        """
        Parse a specification string. This method can be called repeatedly.

        :param str spec: The specification string
        :param str filename: The name of file being parsed (for error messages)
        :param bool finalize: If True, resolve names after parsing. Set this argument to False when bulk-parsing related
            specification files. Be sure to call :meth:`~chisel.SpecParser.finalize` when finished.
        :raises SpecParserError: A parsing error occurred
        """

        self.parse(spec.splitlines(), finalize=finalize, filename=filename)

    def parse(self, lines, filename='', finalize=True):
        """
        Parse a specification from an iterator of line strings (e.g an input stream). This method can be called repeatedly.

        :param ~collections.abc.Iterable(str) lines: An iterator of specification line strings
        :param str filename: The name of file being parsed (for error messages)
        :param bool finalize: If True, resolve names after parsing. Set this argument to False when bulk-parsing related
            specification files. Be sure to call :meth:`~chisel.SpecParser.finalize` when finished.
        :raises SpecParserError: A parsing error occurred
        """

        # Current parser state
        action = None
        urls = None
        user_type = None
        doc = []
        doc_group = None
        linenum = 0

        # Helper function to get documentation strings
        def get_doc():
            nonlocal doc
            doc_str = None
            if doc:
                doc_str = '\n'.join(doc)
                doc = []
            return doc_str

        # Process each line
        line_continuation = []
        for line_part in chain(lines, ('',)):
            linenum += 1

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
            if match is None and action is not None:
                match_name, match = 'section', RE_SECTION.search(line)
            if match is None and action is not None:
                match_name, match = 'section_plain', RE_SECTION_PLAIN.search(line)
            if match is None and user_type is not None and 'enum' in user_type:
                match_name, match = 'value', RE_VALUE.search(line)
            if match is None and user_type is not None and 'struct' in user_type:
                match_name, match = 'member', RE_MEMBER.search(line)
            if match is None and urls is not None:
                match_name, match = 'urls', RE_URL.search(line)
            if match is None:
                match_name, match = 'typedef', RE_TYPEDEF.search(line)
            if match is None:
                match_name = None

            # Comment?
            if match_name == 'comment':
                doc_string = match.group('doc')
                if doc_string is not None:
                    doc.append(doc_string)

            # Documentation group?
            elif match_name == 'group':
                doc_group = match.group('group')
                if doc_group is not None:
                    doc_group = doc_group.strip()
                else:
                    doc_group = None

            # Action?
            elif match_name == 'action':
                action_id = match.group('id')

                # Action already defined?
                if action_id in self.types:
                    self._error(f"Redefinition of action '{action_id}'", filename, linenum)

                # Clear parser state
                urls = None
                user_type = None
                action_doc = get_doc()

                # Create the new action
                action = {
                    'name': action_id
                }
                self.types[action_id] = {'action': action}
                if action_doc is not None:
                    action['doc'] = action_doc
                if doc_group is not None:
                    action['docGroup'] = doc_group

            # Definition?
            elif match_name == 'definition':
                definition_string = match.group('type')
                definition_id = match.group('id')
                definition_base_ids = match.group('base_ids')

                # Type already defined?
                if definition_id in self.BUILTIN_TYPES or definition_id in self.types:
                    self._error(f"Redefinition of type '{definition_id}'", filename, linenum)

                # Clear parser state
                action = None
                urls = None
                definition_doc = get_doc()

                # Struct definition
                if definition_string in ('struct', 'union'):

                    # Create the new struct type
                    struct = {
                        'name': definition_id
                    }
                    user_type = self.types[definition_id] = {'struct': struct}
                    if definition_doc is not None:
                        struct['doc'] = definition_doc
                    if definition_string == 'union':
                        struct['union'] = True

                # Enum definition
                else:  # definition_string == 'enum':

                    # Create the new enum type
                    enum = {
                        'name': definition_id
                    }
                    user_type = self.types[definition_id] = {'enum': enum}
                    if definition_doc is not None:
                        enum['doc'] = definition_doc

                # Record finalization information
                self._filepos[definition_id] = (filename, linenum)
                if definition_base_ids is not None:
                    self._bases[definition_id] = RE_BASE_IDS_SPLIT.split(definition_base_ids)

            # Action section?
            elif match_name == 'section':
                section_string = match.group('type')
                section_base_ids = match.group('base_ids')

                # Action section redefinition?
                if section_string in action:
                    self._error(f'Redefinition of action {section_string}', filename, linenum)

                # Clear parser state
                urls = None

                # Set the action section type
                section_type_name = f'{action["name"]}_{section_string}'
                action[section_string] = section_type_name
                if section_string == 'errors':
                    user_type = self.types[section_type_name] = {'enum': {'name': section_type_name}}
                else:
                    user_type = self.types[section_type_name] = {'struct': {'name': section_type_name}}

                # Record finalization information
                self._filepos[section_type_name] = (filename, linenum)
                if section_base_ids is not None:
                    self._bases[section_type_name] = RE_BASE_IDS_SPLIT.split(section_base_ids)

            # Plain action section?
            elif match_name == 'section_plain':
                section_string = match.group('type')

                # Action section redefinition?
                if section_string in action:
                    self._error(f'Redefinition of action {section_string}', filename, linenum)

                # Clear parser state
                user_type = None

                # Update the parser state
                urls = []

            # Enum value?
            elif match_name == 'value':
                value_string = match.group('id')

                # Add the enum value
                enum = user_type['enum']
                if 'values' not in enum:
                    enum['values'] = []
                enum_value = {
                    'name': value_string,
                }
                enum['values'].append(enum_value)
                enum_value_doc = get_doc()
                if enum_value_doc is not None:
                    enum_value['doc'] = enum_value_doc

                # Record finalization information
                self._filepos[(enum['name'], value_string)] = (filename, linenum)

            # Struct member?
            elif match_name == 'member':
                optional = match.group('optional') is not None
                nullable = match.group('nullable') is not None
                member_name = match.group('id')

                # Add the member
                struct = user_type['struct']
                if 'members' not in struct:
                    struct['members'] = []
                member_type, member_attr = self._parse_typedef(match)
                member_doc = get_doc()
                member = {
                    'name': member_name,
                    'type': member_type
                }
                struct['members'].append(member)
                if member_attr is not None:
                    member['attr'] = member_attr
                if member_doc is not None:
                    member['doc'] = member_doc
                if optional:
                    member['optional'] = True
                if nullable:
                    member['nullable'] = True

                # Record finalization information
                self._filepos[(struct['name'], member_name)] = (filename, linenum)

            # URL?
            elif match_name == 'urls':
                method = match.group('method')
                path = match.group('path')

                # Create the action URL object
                action_url = {}
                if method != '*':
                    action_url['method'] = method
                if path is not None:
                    action_url['path'] = path

                # Duplicate URL?
                if action_url in urls:
                    self._error(f'Duplicate URL: {method} {"" if path is None else path}', filename, linenum)

                # Add the URL
                if 'urls' not in action:
                    action['urls'] = urls
                urls.append(action_url)

            # Typedef?
            elif match_name == 'typedef':
                definition_id = match.group('id')

                # Type already defined?
                if definition_id in self.BUILTIN_TYPES or definition_id in self.types:
                    self._error(f"Redefinition of type '{definition_id}'", filename, linenum)

                # Clear parser state
                action = None
                urls = None
                user_type = None
                typedef_doc = get_doc()

                # Create the typedef
                typedef_type, typedef_attr = self._parse_typedef(match)
                typedef = {
                    'name': definition_id,
                    'type': typedef_type
                }
                self.types[definition_id] = {'typedef': typedef}
                if typedef_attr is not None:
                    typedef['attr'] = typedef_attr
                if typedef_doc is not None:
                    typedef['doc'] = typedef_doc

                # Record finalization information
                self._filepos[definition_id] = (filename, linenum)

            # Unrecognized line syntax
            else:
                self._error('Syntax error', filename, linenum)

        # Finalize, if requested
        if finalize:
            self.finalize()

    def _error(self, msg, filename, linenum):
        self._errors.add((filename, linenum, f'{filename}:{linenum}: error: {msg}'))

    def _parse_typedef(self, match_typedef):
        array_attrs_string = match_typedef.group('array')
        dict_attrs_string = match_typedef.group('dict')

        # Array type?
        if array_attrs_string is not None:
            value_type_name = match_typedef.group('type')
            value_attr = self._parse_attr(match_typedef.group('attrs'))
            array_type = {
                'type': self._create_type(value_type_name)
            }
            if value_attr is not None:
                array_type['attr'] = value_attr
            return {'array': array_type}, self._parse_attr(array_attrs_string)

        # Dictionary type?
        if dict_attrs_string is not None:
            value_type_name = match_typedef.group('dictValueType')
            if value_type_name is not None:
                value_attr = self._parse_attr(match_typedef.group('dictValueAttrs'))
                key_type_name = match_typedef.group('type')
                key_attr = self._parse_attr(match_typedef.group('attrs'))
                dict_type = {
                    'type': self._create_type(value_type_name)
                }
                dict_type['keyType'] = self._create_type(key_type_name)
                if value_attr is not None:
                    dict_type['attr'] = value_attr
                if key_attr is not None:
                    dict_type['keyAttr'] = key_attr
            else:
                value_type_name = match_typedef.group('type')
                value_attr = self._parse_attr(match_typedef.group('attrs'))
                dict_type = {
                    'type': self._create_type(value_type_name)
                }
                if value_attr is not None:
                    dict_type['attr'] = value_attr
            return {'dict': dict_type}, self._parse_attr(dict_attrs_string)

        # Non-container type...
        member_type_name = match_typedef.group('type')
        return self._create_type(member_type_name), self._parse_attr(match_typedef.group('attrs'))

    @classmethod
    def _create_type(cls, type_name):
        if type_name in cls.BUILTIN_TYPES:
            return {'builtin': type_name}
        return {'user': type_name}

    @classmethod
    def _parse_attr(cls, attrs_string):
        attrs = None
        if attrs_string is not None:
            for attr_string in RE_FIND_ATTRS.findall(attrs_string):
                if attrs is None:
                    attrs = {}
                match_attr = RE_ATTR_GROUP.match(attr_string)
                attr_op = match_attr.group('op')
                attr_length_op = match_attr.group('lop') if attr_op is None else None

                if attr_op is not None:
                    attr_value = float(match_attr.group('opnum'))
                    if attr_op == '<':
                        attrs['lt'] = attr_value
                    elif attr_op == '<=':
                        attrs['lte'] = attr_value
                    elif attr_op == '>':
                        attrs['gt'] = attr_value
                    elif attr_op == '>=':
                        attrs['gte'] = attr_value
                    else:  # ==
                        attrs['eq'] = attr_value
                else:  # attr_length_op is not None:
                    attr_value = int(match_attr.group('lopnum'))
                    if attr_length_op == '<':
                        attrs['lenLT'] = attr_value
                    elif attr_length_op == '<=':
                        attrs['lenLTE'] = attr_value
                    elif attr_length_op == '>':
                        attrs['lenGT'] = attr_value
                    elif attr_length_op == '>=':
                        attrs['lenGTE'] = attr_value
                    else:  # ==
                        attrs['lenEq'] = attr_value
        return attrs

    def _finalize_bases(self):

        # Compute the base type members/values
        type_objects = []
        for type_name in self._bases:
            user_type = self.types[type_name]
            filepos = self._get_filepos(type_name)
            if 'struct' in user_type:
                type_objects.append(
                    (type_name, 'struct', 'members', self._get_base_objects(type_name, 'struct', 'members', filepos, set()))
                )
            else:
                type_objects.append(
                    (type_name, 'enum', 'values', self._get_base_objects(type_name, 'enum', 'values', filepos, set()))
                )

        # Update the members/values
        for type_name, user_type_key, object_key, objects in type_objects:
            self.types[type_name][user_type_key][object_key] = objects

        # Clear the base type state (so we don't process again)
        self._bases = {}

    def _get_filepos(self, type_name, type_key=None):
        if type_key is None:
            filepos = self._filepos.get(type_name)
        else:
            filepos = self._filepos.get((type_name, type_key))
        if filepos is None:
            filepos = ('', 1)
        return filepos

    def _get_base_objects(self, type_name, user_type_key, object_key, filepos, type_names):
        base_objects = []

        # Check for cycle
        is_cycle = type_name in type_names
        type_names.add(type_name)
        if is_cycle:
            self._error(f'Circular base type detected for type {type_name!r}', *filepos)
            return base_objects

        # Compute the base objects
        if type_name in self._bases:
            for base_name in self._bases[type_name]:
                base_type = get_effective_type(self.types, {'user': base_name})
                invalid_base = True
                if 'user' in base_type:
                    user_type = self.types[base_type['user']]
                    if user_type_key in user_type:
                        type_model = user_type[user_type_key]
                        if not type_model.get('union', False):
                            base_objects.extend(self._get_base_objects(base_type['user'], user_type_key, object_key, filepos, type_names))
                            invalid_base = False
                if invalid_base:
                    self._error(f'Invalid {user_type_key} base type {base_name!r}', *filepos)

        # Add missing filepos
        for obj in base_objects:
            filepos_key = (type_name, obj['name'])
            if filepos_key not in self._filepos:
                self._filepos[filepos_key] = filepos

        # Add the type's objects
        type_model = self.types[type_name][user_type_key]
        if object_key in type_model:
            base_objects.extend(type_model[object_key])

        return base_objects
