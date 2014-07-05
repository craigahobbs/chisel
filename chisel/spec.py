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

from .compat import StringIO
from . import model

import re


# Action model
class ActionModel(object):
    __slots__ = ('name', 'inputType', 'outputType', 'errorType', 'doc')

    def __init__(self, name, doc = None):
        self.name = name
        self.inputType = model.TypeStruct(typeName = name + '_Input')
        self.outputType = model.TypeStruct(typeName = name + '_Output')
        self.errorType = model.TypeEnum(typeName = name + '_Error')
        self.doc = [] if doc is None else doc


# Spec parser exception
class SpecParserError(Exception):
    __slots__ = ('errors',)

    def __init__(self, errors):
        Exception.__init__(self, '\n'.join(errors))
        self.errors = errors


# Type id reference - converted to types on parser finalization
class TypeRef(object):
    __slots__ = ('fileName', 'fileLine', 'parent', 'name', 'attr')

    def __init__(self, fileName, fileLine, name, parent, attr):
        self.fileName = fileName
        self.fileLine = fileLine
        self.parent = parent
        self.name = name
        self.attr = attr


# Specification language parser class
class SpecParser(object):

    __slots__ = (
        'types',
        'actions',
        'errors',
        '_parseStream',
        '_parseFileName',
        '_parseFileLine',
        '_curAction',
        '_curType',
        '_curDoc',
        '_typeRefs',
        )

    # Parser regex
    _RE_PART_ID = r'([A-Za-z]\w*)'
    _RE_PART_ATTR_GROUP = r'((?P<op><=|<|>|>=|==)\s*(?P<opnum>-?\d+(\.\d+)?)' \
                          r'|(?P<ltype>len)\s*(?P<lop><=|<|>|>=|==)\s*(?P<lopnum>\d+))'
    _RE_PART_ATTR = re.sub(r'\(\?P<[^>]+>', r'(', _RE_PART_ATTR_GROUP)
    _RE_ATTR_GROUP = re.compile(_RE_PART_ATTR_GROUP)
    _RE_FIND_ATTRS = re.compile(_RE_PART_ATTR + r'(?:\s*,\s*|\s*\Z)')
    _RE_LINE_CONT = re.compile(r'\\s*$')
    _RE_COMMENT = re.compile(r'^\s*(#-.*|#(?P<doc>.*))?$')
    _RE_DEFINITION = re.compile(r'^(?P<type>action|struct|union|enum)\s+(?P<id>' + _RE_PART_ID + r')\s*$')
    _RE_SECTION = re.compile(r'^\s+(?P<type>input|output|errors)\s*$')
    _RE_MEMBER = re.compile(r'^\s+((?P<optional>optional)\s+)?'
                            r'(\[\s*(?P<attrs>' + _RE_PART_ATTR + r'(\s*,\s*' + _RE_PART_ATTR + r')*)\s*\]\s+)?'
                            r'(?P<type>' + _RE_PART_ID + r')'
                            r'(\s*\[\s*(?P<array>(' + _RE_PART_ATTR + r'(\s*,\s*' + _RE_PART_ATTR + r')*)?)\s*\]'
                            r'|\s*{\s*(?P<dict>(' + _RE_PART_ATTR + r'(\s*,\s*' + _RE_PART_ATTR + r')*)?)\s*})?'
                            r'\s+(?P<id>' + _RE_PART_ID + r')\s*$')
    _reValue = re.compile(r'^\s+"?(?P<id>(?<!")' + _RE_PART_ID + r'(?!")|(?<=").*?(?="))"?\s*$')

    # Types
    _TYPES = {
        'string': model.TypeString,
        'int': model.TypeInt,
        'float': model.TypeFloat,
        'bool': model.TypeBool,
        'datetime': model.TypeDatetime,
        'uuid': model.TypeUuid,
        }

    def __init__(self):
        self.types = {}
        self.actions = {}
        self.errors = []
        self._typeRefs = []

    # Parse a specification file
    def parse(self, specPath, finalize = True):
        with open(specPath, 'r') as specStream:
            self.parseStream(specStream, finalize = finalize, fileName = specPath)

    # Parse a specification string
    def parseString(self, spec, fileName = '', finalize = True):
        self.parseStream(StringIO(spec), finalize = finalize, fileName = fileName)

    # Parse a specification from an input stream
    def parseStream(self, specStream, fileName = '', finalize = True):

        # Set the parser state
        self._parseStream = specStream
        self._parseFileName = fileName
        self._parseFileLine = 0
        self._curAction = None
        self._curType = None
        self._curDoc = []

        # Do the work
        self._parse()
        if finalize:
            self.finalize()

    # Finalize parsing (must call after calling parse one or more times - can be repeated)
    def finalize(self):

        # Fixup type refs
        for typeRef in self._typeRefs:
            type = self._getType(typeRef.name)
            if type is not None:
                typeRef.parent.type = type
                if typeRef.attr is not None:
                    self._validateAttr(type, typeRef.attr, fileName = typeRef.fileName, fileLine = typeRef.fileLine)
            else:
                self._error("Unknown member type '" + typeRef.name + "'", fileName = typeRef.fileName, fileLine = typeRef.fileLine)
        self._typeRefs = []

        # Raise a parser exception if there are any errors
        if self.errors:
            raise SpecParserError(self.errors)

    # Get a line from the current stream
    def _getLine(self):

        lines = []
        while True:
            line = self._parseStream.readline()
            if not line:
                break
            self._parseFileLine += 1
            isLineCont = self._RE_LINE_CONT.search(line)
            if isLineCont:
                line = self._RE_LINE_CONT.sub('', line)
            lines.append(line)
            if not isLineCont:
                break
        return ' '.join(lines) if lines else None

    # Get a type object by name
    def _getType(self, name):
        typeFactory = self._TYPES.get(name)
        return self.types.get(name) if typeFactory is None else typeFactory()

    # Record an error
    def _error(self, msg, fileName = None, fileLine = None):
        self.errors.append('%s:%d: error: %s' % (fileName or self._parseFileName, fileLine or self._parseFileLine, msg))

    # Validate a type's attributes
    def _validateAttr(self, type, attr, fileName = None, fileLine = None):
        try:
            type.validateAttr(attr)
        except model.AttributeValidationError as e:
            self._error("Invalid attribute '" + e.attr + "'", fileName = fileName, fileLine = fileLine)

    # Parse an attributes string
    @classmethod
    def _parseAttr(cls, sAttrs):
        attr = None
        if sAttrs is not None:
            for sAttr in cls._RE_FIND_ATTRS.findall(sAttrs):
                mAttr = cls._RE_ATTR_GROUP.match(sAttr[0])
                attrOp = mAttr.group('op')
                attrLop = mAttr.group('lop') if attrOp is None else None

                if attr is None:
                    attr = model.StructMemberAttributes()

                if attrOp is not None:
                    attrValue = float(mAttr.group('opnum'))
                    if attrOp == '<':
                        attr.lt = attrValue
                    elif attrOp == '<=':
                        attr.lte = attrValue
                    elif attrOp == '>':
                        attr.gt = attrValue
                    elif attrOp == '>=':
                        attr.gte = attrValue
                    else: # ==
                        attr.eq = attrValue
                else: # attrLop is not None:
                    attrValue = int(mAttr.group('lopnum'))
                    if attrLop == '<':
                        attr.len_lt = attrValue
                    elif attrLop == '<=':
                        attr.len_lte = attrValue
                    elif attrLop == '>':
                        attr.len_gt = attrValue
                    elif attrLop == '>=':
                        attr.len_gte = attrValue
                    else: # ==
                        attr.len_eq = attrValue

        return attr

    # Parse a specification from a stream
    def _parse(self):

        # Process each line
        while True:

            # Read a line (including continuation)
            line = self._getLine()
            if line is None:
                break

            # Match line syntax
            mComment = self._RE_COMMENT.search(line)
            mDefinition = self._RE_DEFINITION.search(line) if mComment is None else None
            mSection = self._RE_SECTION.search(line) if mDefinition is None else None
            mMember = self._RE_MEMBER.search(line) if mSection is None else None
            mValue = self._reValue.search(line) if mMember is None else None

            # Comment?
            if mComment:

                sDoc = mComment.group('doc')
                if sDoc is not None:
                    self._curDoc.append(sDoc.strip())

            # Definition?
            elif mDefinition:

                sDefType = mDefinition.group('type')
                sDefId = mDefinition.group('id')

                # Action definition
                if sDefType == 'action':

                    # Action already defined?
                    if sDefId in self.actions:
                        self._error("Redefinition of action '" + sDefId + "'")

                    # Create the new action
                    self._curAction = ActionModel(sDefId, doc = self._curDoc)
                    self._curType = None
                    self._curDoc = []
                    self.actions[self._curAction.name] = self._curAction

                # Struct definition
                elif sDefType == 'struct' or sDefType == 'union':

                    # Type already defined?
                    if sDefId in self._TYPES or sDefId in self.types:
                        self._error("Redefinition of type '" + sDefId + "'")

                    # Create the new struct type
                    self._curAction = None
                    self._curType = model.TypeStruct(typeName = sDefId, isUnion = (sDefType == 'union'), doc = self._curDoc)
                    self._curDoc = []
                    self.types[self._curType.typeName] = self._curType

                # Enum definition
                else: # sDefType == 'enum':

                    # Type already defined?
                    if sDefId in self._TYPES or sDefId in self.types:
                        self._error("Redefinition of type '" + sDefId + "'")

                    # Create the new enum type
                    self._curAction = None
                    self._curType = model.TypeEnum(typeName = sDefId, doc = self._curDoc)
                    self._curDoc = []
                    self.types[self._curType.typeName] = self._curType

            # Section?
            elif mSection:

                sSectType = mSection.group('type')

                # Not in an action scope?
                if not self._curAction:
                    self._error('Action section outside of action scope')
                    continue

                # Set the action section type
                if sSectType == 'input':
                    self._curType = self._curAction.inputType
                elif sSectType == 'output':
                    self._curType = self._curAction.outputType
                else: # sSectType == 'errors':
                    self._curType = self._curAction.errorType

            # Struct member?
            elif mMember:

                isOptional = mMember.group('optional') is not None
                sTypeName = mMember.group('type')
                sArrayAttr = mMember.group('array')
                sDictAttr = mMember.group('dict')
                sMemberName = mMember.group('id')

                # Not in a struct scope?
                if not isinstance(self._curType, model.TypeStruct):
                    self._error('Member definition outside of struct scope')
                    continue

                # Member name already defined?
                if any(m.name == sMemberName for m in self._curType.members):
                    self._error("Redefinition of member '" + sMemberName + "'")

                # Get the member base type
                memType = self._getType(sTypeName)
                memAttr = self._parseAttr(mMember.group('attrs'))
                if sArrayAttr is not None:
                    memType = model.TypeArray(memType, attr = memAttr)
                    memAttr = self._parseAttr(sArrayAttr)
                elif sDictAttr is not None:
                    memType = model.TypeDict(memType, attr = memAttr)
                    memAttr = self._parseAttr(sDictAttr)

                # Create the struct member
                member = self._curType.addMember(sMemberName, memType, isOptional, memAttr, doc = self._curDoc)
                self._curDoc = []

                # Validate attributes
                if sArrayAttr is not None or sDictAttr is not None:

                    # Validate collection type attributes
                    if memAttr is not None:
                        self._validateAttr(memType, memAttr)

                    # Add a typeref if collection base type is unknown
                    if memType.type is None:
                        typeRef = TypeRef(self._parseFileName, self._parseFileLine, sTypeName, memType, memType.attr)
                        self._typeRefs.append(typeRef)
                    elif memType.attr is not None:
                        # Validate collection base type attributes
                        self._validateAttr(memType.type, memType.attr)

                else:

                    # Add a typeref if type is unknown
                    if memType is None:
                        typeRef = TypeRef(self._parseFileName, self._parseFileLine, sTypeName, member, memAttr)
                        self._typeRefs.append(typeRef)
                    elif memAttr is not None:
                        # Validate the type attributes
                        self._validateAttr(memType, memAttr)

            # Enum value?
            elif mValue:

                sEnumValue = mValue.group('id')

                # Not in an enum scope?
                if not isinstance(self._curType, model.TypeEnum):
                    self._error('Enumeration value outside of enum scope')
                    continue

                # Duplicate enum value?
                if sEnumValue in self._curType.values:
                    self._error("Duplicate enumeration value '" + sEnumValue + "'")

                # Add the enum value
                self._curType.addValue(sEnumValue, doc = self._curDoc)
                self._curDoc = []

            # Unrecognized line syntax
            else:
                self._error('Syntax error')
