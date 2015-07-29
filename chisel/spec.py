#
# Copyright (C) 2012-2015 Craig Hobbs
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

from .model import AttributeValidationError, StructMemberAttributes, TypeArray, \
    TypeBool, TypeDate, TypeDatetime, Typedef, TypeDict, TypeEnum, TypeInt, \
    TypeFloat, TypeString, TypeStruct, TypeUuid

from itertools import chain
import re


# Action model
class ActionModel(object):
    __slots__ = ('name', 'inputType', 'outputType', 'errorType', 'doc')

    VALID_INPUT_TYPES = (TypeStruct, TypeDict)
    VALID_OUTPUT_TYPES = (TypeStruct, TypeDict)
    VALID_ERROR_TYPES = (TypeEnum,)

    def __init__(self, name, doc=None):
        self.name = name
        self.inputType = TypeStruct(typeName=name + '_Input')
        self.outputType = TypeStruct(typeName=name + '_Output')
        self.errorType = TypeEnum(typeName=name + '_Error')
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
        '_parseLines',
        '_parseFileName',
        '_parseFileLine',
        '_curAction',
        '_curActionDefs',
        '_curType',
        '_curDoc',
        '_typeRefs',
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
    _RE_DEFINITION = re.compile(r'^(?P<type>action|struct|union|enum)\s+(?P<id>' + _RE_PART_ID + r')\s*$')
    _RE_SECTION = re.compile(r'^\s+(?P<type>input|output|errors)(?:\s+(?P<id>' + _RE_PART_ID + r'))?\s*$')
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
    _RE_MEMBER = re.compile(r'^\s+(?P<optional>optional\s+)?' + _RE_PART_TYPEDEF + r'\s*$')
    _RE_VALUE = re.compile(r'^\s+"?(?P<id>(?<!")' + _RE_PART_ID + r'(?!")|(?<=").*?(?="))"?\s*$')

    # Built-in types
    _TYPES = {
        'string': TypeString,
        'int': TypeInt,
        'float': TypeFloat,
        'bool': TypeBool,
        'date': TypeDate,
        'datetime': TypeDatetime,
        'uuid': TypeUuid,
    }

    def __init__(self):
        self.types = {}
        self.actions = {}
        self.errors = []
        self._typeRefs = []
        self._curAction = None
        self._curActionDefs = None
        self._curType = None
        self._curDoc = None
        self._parseLines = None
        self._parseFileName = None
        self._parseFileLine = 0

    # Parse a specification string
    def parseString(self, spec, fileName='', finalize=True):
        self.parse(spec.splitlines(), finalize=finalize, fileName=fileName)

    # Parse a specification from a collection of spec lines (e.g an input stream)
    def parse(self, specLines, fileName='', finalize=True):

        # Set the parser state
        self._curAction = None
        self._curType = None
        self._curDoc = []
        self._parseLines = specLines
        self._parseFileName = fileName
        self._parseFileLine = 0

        # Do the work
        self._parse()
        if finalize:
            self.finalize()

    # Finalize parsing (must call after calling parse one or more times - can be repeated)
    def finalize(self):

        # Fixup type refs
        for typeRef in self._typeRefs:
            typeRef(True)
        self._typeRefs = []

        # Raise a parser exception if there are any errors
        if self.errors:
            raise SpecParserError(self.errors)

    # Set a type attribute by name
    def _setType(self, parent, parentAttr, typeName, typeAttr, typeValidationFn=None):
        fileName = self._parseFileName
        fileLine = self._parseFileLine

        def setType(error):
            typeFactory = self._TYPES.get(typeName)
            type_ = self.types.get(typeName) if typeFactory is None else typeFactory()
            if type_ is not None:
                if typeValidationFn is not None:
                    typeValidationFn(type_, fileName, fileLine)
                self._validateAttr(type_, typeAttr, fileName=fileName, fileLine=fileLine)
                setattr(parent, parentAttr, type_)
            elif error:
                self._error("Unknown member type '" + typeName + "'", fileName=fileName, fileLine=fileLine)
            return type_
        type_ = setType(False)
        if type_ is None:
            self._typeRefs.append(setType)

    # Record an error
    def _error(self, msg, fileName=None, fileLine=None):
        self.errors.append('%s:%d: error: %s' % (fileName or self._parseFileName, fileLine or self._parseFileLine, msg))

    # Validate a type's attributes
    def _validateAttr(self, type_, attr, fileName=None, fileLine=None):
        try:
            if attr is not None:
                type_.validateAttr(attr)
        except AttributeValidationError as e:
            self._error("Invalid attribute '" + e.attr + "'", fileName=fileName, fileLine=fileLine)

    # Parse an attributes string
    @classmethod
    def _parseAttr(cls, sAttrs):
        attr = None
        if sAttrs is not None:
            for sAttr in cls._RE_FIND_ATTRS.findall(sAttrs):
                mAttr = cls._RE_ATTR_GROUP.match(sAttr)
                attrOp = mAttr.group('op')
                attrLop = mAttr.group('lop') if attrOp is None else None

                if attr is None:
                    attr = StructMemberAttributes()

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
                    else:  # ==
                        attr.eq = attrValue
                else:  # attrLop is not None:
                    attrValue = int(mAttr.group('lopnum'))
                    if attrLop == '<':
                        attr.len_lt = attrValue
                    elif attrLop == '<=':
                        attr.len_lte = attrValue
                    elif attrLop == '>':
                        attr.len_gt = attrValue
                    elif attrLop == '>=':
                        attr.len_gte = attrValue
                    else:  # ==
                        attr.len_eq = attrValue
        return attr

    # Construct typedef parts
    def _parseTypedef(self, parent, parentTypeAttr, parentAttrAttr, mTypedef):
        sArrayAttr = mTypedef.group('array')
        sDictAttr = mTypedef.group('dict')

        # Array member?
        if sArrayAttr is not None:
            sValueType = mTypedef.group('type')
            valueAttr = self._parseAttr(mTypedef.group('attrs'))
            arrayType = TypeArray(None, attr=valueAttr)
            self._setType(arrayType, 'type', sValueType, valueAttr)

            arrayAttr = self._parseAttr(sArrayAttr)
            self._validateAttr(arrayType, arrayAttr)

            setattr(parent, parentTypeAttr, arrayType)
            setattr(parent, parentAttrAttr, arrayAttr)

        # Dictionary member?
        elif sDictAttr is not None:
            sValueType = mTypedef.group('dictValueType')
            if sValueType is not None:
                valueAttr = self._parseAttr(mTypedef.group('dictValueAttrs'))
                sKeyType = mTypedef.group('type')
                keyAttr = self._parseAttr(mTypedef.group('attrs'))
                dictType = TypeDict(None, attr=valueAttr, keyType=None, keyAttr=keyAttr)
                self._setType(dictType, 'type', sValueType, valueAttr)

                def validateKeyType(keyType, fileName, fileLine):
                    if not TypeDict.validKeyType(keyType):
                        self._error('Invalid dictionary key type', fileName=fileName, fileLine=fileLine)
                self._setType(dictType, 'keyType', sKeyType, keyAttr, typeValidationFn=validateKeyType)
            else:
                sValueType = mTypedef.group('type')
                valueAttr = self._parseAttr(mTypedef.group('attrs'))
                dictType = TypeDict(None, attr=valueAttr)
                self._setType(dictType, 'type', sValueType, valueAttr)

            dictAttr = self._parseAttr(sDictAttr)
            self._validateAttr(dictType, dictAttr)

            setattr(parent, parentTypeAttr, dictType)
            setattr(parent, parentAttrAttr, dictAttr)

        # Non-container member...
        else:
            sMemType = mTypedef.group('type')
            memAttr = self._parseAttr(mTypedef.group('attrs'))

            self._setType(parent, parentTypeAttr, sMemType, memAttr)
            setattr(parent, parentAttrAttr, memAttr)

    # Parse a specification from a stream
    def _parse(self):

        # Process each line
        self._parseFileLine = 0
        lineCont = []
        for linePart in chain(self._parseLines, ('',)):
            self._parseFileLine += 1

            # Line continuation?
            linePartNoCont = self._RE_LINE_CONT.sub('', linePart)
            if lineCont or linePartNoCont is not linePart:
                lineCont.append(linePartNoCont)
            if linePartNoCont is not linePart:
                continue
            elif lineCont:
                line = ''.join(lineCont)
                del lineCont[:]
            else:
                line = linePart

            # Match line syntax
            mComment = self._RE_COMMENT.search(line)
            mDefinition = self._RE_DEFINITION.search(line) if mComment is None else None
            mSection = self._RE_SECTION.search(line) if mDefinition is None else None
            mValue = self._RE_VALUE.search(line) if mSection is None else None
            mMember = self._RE_MEMBER.search(line) if mValue is None else None
            mTypedef = self._RE_TYPEDEF.search(line) if mMember is None else None

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
                    self._curAction = ActionModel(sDefId, doc=self._curDoc)
                    self._curActionDefs = set()
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
                    self._curType = TypeStruct(typeName=sDefId, isUnion=(sDefType == 'union'), doc=self._curDoc)
                    self._curDoc = []
                    self.types[self._curType.typeName] = self._curType

                # Enum definition
                else:  # sDefType == 'enum':

                    # Type already defined?
                    if sDefId in self._TYPES or sDefId in self.types:
                        self._error("Redefinition of type '" + sDefId + "'")

                    # Create the new enum type
                    self._curAction = None
                    self._curType = TypeEnum(typeName=sDefId, doc=self._curDoc)
                    self._curDoc = []
                    self.types[self._curType.typeName] = self._curType

            # Section?
            elif mSection:
                sSectType = mSection.group('type')
                sTypeId = mSection.group('id')

                # Not in an action scope?
                if self._curAction is None:
                    self._error('Action section outside of action scope')
                    continue

                # Action section redefinition?
                if sSectType in self._curActionDefs:
                    self._error('Redefinition of action ' + sSectType)
                    self._curType = None
                    continue
                self._curActionDefs.add(sSectType)

                # Set the action section type
                if sSectType == 'input':
                    if sTypeId is not None:
                        def validateInputType(inputType, fileName, fileLine):
                            if not isinstance(Typedef.baseType(inputType), ActionModel.VALID_INPUT_TYPES):
                                self._error('Invalid action input type', fileName=fileName, fileLine=fileLine)
                        self._setType(self._curAction, 'inputType', sTypeId, None, typeValidationFn=validateInputType)
                        self._curType = None
                    else:
                        self._curType = self._curAction.inputType

                elif sSectType == 'output':
                    if sTypeId is not None:
                        def validateOutputType(outputType, fileName, fileLine):
                            if not isinstance(Typedef.baseType(outputType), ActionModel.VALID_OUTPUT_TYPES):
                                self._error('Invalid action output type', fileName=fileName, fileLine=fileLine)
                        self._setType(self._curAction, 'outputType', sTypeId, None, typeValidationFn=validateOutputType)
                        self._curType = None
                    else:
                        self._curType = self._curAction.outputType

                else:  # sSectType == 'errors':
                    if sTypeId is not None:
                        def validateErrorType(errorType, fileName, fileLine):
                            if not isinstance(Typedef.baseType(errorType), ActionModel.VALID_ERROR_TYPES):
                                self._error('Invalid action errors type', fileName=fileName, fileLine=fileLine)
                        self._setType(self._curAction, 'errorType', sTypeId, None, typeValidationFn=validateErrorType)
                        self._curType = None
                    else:
                        self._curType = self._curAction.errorType

            # Enum value?
            elif mValue:
                sEnumValue = mValue.group('id')

                # Not in an enum scope?
                if not isinstance(self._curType, TypeEnum):
                    self._error('Enumeration value outside of enum scope')
                    continue

                # Duplicate enum value?
                if sEnumValue in self._curType.values:
                    self._error("Duplicate enumeration value '" + sEnumValue + "'")

                # Add the enum value
                self._curType.addValue(sEnumValue, doc=self._curDoc)
                self._curDoc = []

            # Struct member?
            elif mMember:
                isOptional = mMember.group('optional') is not None
                sMemberName = mMember.group('id')

                # Not in a struct scope?
                if not isinstance(self._curType, TypeStruct):
                    self._error('Member definition outside of struct scope')
                    continue

                # Member name already defined?
                if any(m.name == sMemberName for m in self._curType.members):
                    self._error("Redefinition of member '" + sMemberName + "'")

                # Create the member
                member = self._curType.addMember(sMemberName, None, isOptional, None, doc=self._curDoc)
                self._parseTypedef(member, 'type', 'attr', mMember)

                self._curDoc = []

            # Typedef?
            elif mTypedef:
                sTypedefId = mTypedef.group('id')

                # Type already defined?
                if sTypedefId in self._TYPES or sTypedefId in self.types:
                    self._error("Redefinition of type '" + sTypedefId + "'")

                # Create the typedef
                typedef = Typedef(None, attr=None, typeName=sTypedefId, doc=self._curDoc)
                self._parseTypedef(typedef, 'type', 'attr', mTypedef)
                self.types[sTypedefId] = typedef

                # Reset current action/type
                self._curAction = None
                self._curType = None
                self._curDoc = []

            # Unrecognized line syntax
            else:
                self._error('Syntax error')
