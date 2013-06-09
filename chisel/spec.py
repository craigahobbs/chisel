#
# Copyright (C) 2012-2013 Craig Hobbs
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
from .model import TypeStruct, TypeArray, TypeDict, TypeEnum, \
    TypeString, TypeInt, TypeFloat, TypeBool, TypeDatetime, TypeUuid

import re


# Action class
class Action(object):

    def __init__(self, name, doc = None):

        self.name = name
        self.inputType = TypeStruct(typeName = name + '_Input')
        self.outputType = TypeStruct(typeName = name + '_Output')
        self.errorType = TypeEnum(typeName = name + '_Error')
        self.doc = [] if doc is None else doc


# Spec parser exception
class SpecParserError(Exception):

    def __init__(self, errors):

        Exception.__init__(self, '\n'.join(errors))
        self.errors = errors


# Specification language parser class
class SpecParser(object):

    # Parser regex
    _rePartId = '([A-Za-z]\w*)'
    _rePartAttrGroup = '((?P<optional>optional)|(?P<op><=|<|>|>=)\s*(?P<opnum>-?\d+(\.\d+)?)|' + \
        'len\s*(?P<lop><=|<|>|>=)\s*(?P<lopnum>\d+))'
    _reAttrGroup = re.compile(_rePartAttrGroup)
    _rePartAttr = re.sub('\\(\\?P<[^>]+>', '(', _rePartAttrGroup)
    _reFindAttrs = re.compile(_rePartAttr + '(?:\s*,\s*|\s*\Z)')
    _rePartAttrs = '(\\[\s*(?P<attrs>' + _rePartAttr + '(\s*,\s*' + _rePartAttr + ')*)\s*\\])'
    _reLineCont = re.compile('\\\s*$')
    _reComment = re.compile('^\s*(#-.*|#(?P<doc>.*))?$')
    _reDefinition = re.compile('^(?P<type>action|struct|enum)\s+(?P<id>' + _rePartId + ')\s*$')
    _reSection = re.compile('^\s+(?P<type>input|output|errors)\s*$')
    _reMember = re.compile('^\s+(' + _rePartAttrs + '\s+)?(?P<type>' + _rePartId +
                           ')((?P<isArray>\\[\\])|(?P<isDict>{}))?\s+(?P<id>' + _rePartId + ')\s*$')
    _reValue = re.compile('^\s+(?P<id>' + _rePartId + ')\s*$')

    # Types
    _types = {
        'string': TypeString,
        'int': TypeInt,
        'float': TypeFloat,
        'bool': TypeBool,
        'datetime': TypeDatetime,
        'uuid': TypeUuid
        }

    def __init__(self):

        self.types = {}
        self.actions = {}
        self.errors = []

        # Finalization state
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
        assert not self.errors

        # Set the parser state
        self._parseStream = specStream
        self._parseFileName = fileName
        self._parseLine = 0
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
        for member in self._typeRefs:
            typeRef = member.typeInst
            typeInst = self._getTypeInst(typeRef)
            if typeInst is not None:
                member.typeInst = typeInst
            else:
                self._error("Unknown member type '" + typeRef.typeName + "'", fileName = typeRef.fileName, fileLine = typeRef.fileLine)
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
            self._parseLine += 1
            isLineCont = self._reLineCont.search(line)
            if isLineCont:
                line = self._reLineCont.sub('', line)
            lines.append(line)
            if not isLineCont:
                break
        return ' '.join(lines) if lines else None

    # Type id reference - converted to types on parser finalization
    class _TypeRef(object):

        def __init__(self, fileName, fileLine, typeName, isArray, isDict):

            self.fileName = fileName
            self.fileLine = fileLine
            self.typeName = typeName
            self.isArray = isArray
            self.isDict = isDict

    # Get a type instance for a type ref
    def _getTypeInst(self, typeRef):

        # Get the type instance
        typeClass = self._types.get(typeRef.typeName)
        if typeClass is not None:
            typeInst = typeClass(typeName = typeRef.typeName)
        else:
            typeInst = self.types.get(typeRef.typeName)

        # Return the type instance
        if typeInst is None:
            return None
        elif typeRef.isArray:
            return TypeArray(typeInst)
        elif typeRef.isDict:
            return TypeDict(typeInst)
        else:
            return typeInst

    # Record an error
    def _error(self, msg, fileName = None, fileLine = None):
        self.errors.append('%s:%d: error: %s' % (fileName or self._parseFileName, fileLine or self._parseLine, msg))

    # Parse a specification from a stream
    def _parse(self):

        # Process each line
        while True:

            # Read a line (including continuation)
            line = self._getLine()
            if line is None:
                break

            # Match line syntax
            mComment = self._reComment.search(line)
            mDefinition = self._reDefinition.search(line)
            mSection = self._reSection.search(line)
            mMember = self._reMember.search(line)
            mValue = self._reValue.search(line)

            # Comment?
            if mComment:

                doc = mComment.group('doc')
                if doc is not None:
                    self._curDoc.append(doc.strip())

            # Definition?
            elif mDefinition:

                defType = mDefinition.group('type')
                defId = mDefinition.group('id')

                # Action definition
                if defType == 'action':

                    # Action already defined?
                    if defId in self.actions:
                        self._error("Redefinition of action '" + defId + "'")

                    # Create the new action
                    self._curAction = Action(defId, doc = self._curDoc)
                    self._curType = None
                    self._curDoc = []
                    self.actions[self._curAction.name] = self._curAction

                # Struct definition
                elif defType == 'struct':

                    # Type already defined?
                    if defId in self._types or defId in self.types:
                        self._error("Redefinition of type '" + defId + "'")

                    # Create the new struct type
                    self._curAction = None
                    self._curType = TypeStruct(typeName = defId, doc = self._curDoc)
                    self._curDoc = []
                    self.types[self._curType.typeName] = self._curType

                # Enum definition
                elif defType == 'enum':

                    # Type already defined?
                    if defId in self._types or defId in self.types:
                        self._error("Redefinition of type '" + defId + "'")

                    # Create the new enum type
                    self._curAction = None
                    self._curType = TypeEnum(typeName = defId, doc = self._curDoc)
                    self._curDoc = []
                    self.types[self._curType.typeName] = self._curType

            # Section?
            elif mSection:

                sectType = mSection.group('type')

                # Not in an action scope?
                if not self._curAction:
                    self._error('Action section outside of action scope')
                    continue

                # Set the action section type
                if sectType == 'input':
                    self._curType = self._curAction.inputType
                elif sectType == 'output':
                    self._curType = self._curAction.outputType
                elif sectType == 'errors':
                    self._curType = self._curAction.errorType

            # Struct member?
            elif mMember:

                memAttrs = self._reFindAttrs.findall(mMember.group('attrs')) if mMember.group('attrs') else []
                memTypeName = mMember.group('type')
                memIsArray = mMember.group('isArray')
                memIsDict = mMember.group('isDict')
                memId = mMember.group('id')

                # Not in a struct scope?
                if not isinstance(self._curType, TypeStruct):
                    self._error('Member definition outside of struct scope')
                    continue

                # Member ID already defined?
                if any(m.name == memId for m in self._curType.members):
                    self._error("Redefinition of member '" + memId + "'")

                # Create the struct member
                memTypeRef = self._TypeRef(self._parseFileName, self._parseLine, memTypeName, memIsArray, memIsDict)
                member = self._curType.addMember(memId, self._getTypeInst(memTypeRef) or memTypeRef, doc = self._curDoc)
                self._curDoc = []
                if isinstance(member.typeInst, self._TypeRef):
                    self._typeRefs.append(member)

                # Get the member type for setting attributes (only for built-in types!)
                if isinstance(member.typeInst, TypeArray) or isinstance(member.typeInst, TypeDict):
                    memTypeInst = member.typeInst.typeInst
                elif not isinstance(member.typeInst, TypeStruct) and not isinstance(member.typeInst, TypeEnum) and \
                        not isinstance(member.typeInst, self._TypeRef):
                    memTypeInst = member.typeInst
                else:
                    memTypeInst = None

                # Apply member attributes - type attributes only apply to built-in types
                for memAttr in memAttrs:
                    mAttr = self._reAttrGroup.match(memAttr[0])
                    if mAttr.group('optional'):
                        member.isOptional = True
                    elif mAttr.group('op'):
                        if mAttr.group('op') == '<' and hasattr(memTypeInst, 'constraint_lt'):
                            memTypeInst.constraint_lt = float(mAttr.group('opnum'))
                        elif mAttr.group('op') == '<=' and hasattr(memTypeInst, 'constraint_lte'):
                            memTypeInst.constraint_lte = float(mAttr.group('opnum'))
                        elif mAttr.group('op') == '>' and hasattr(memTypeInst, 'constraint_gt'):
                            memTypeInst.constraint_gt = float(mAttr.group('opnum'))
                        elif mAttr.group('op') == '>=' and hasattr(memTypeInst, 'constraint_gte'):
                            memTypeInst.constraint_gte = float(mAttr.group('opnum'))
                        else:
                            self._error("Invalid attribute '" + memAttr[0] + "'")
                    elif mAttr.group('lop'):
                        if mAttr.group('lop') == '<' and hasattr(memTypeInst, 'constraint_len_lt'):
                            memTypeInst.constraint_len_lt = int(mAttr.group('lopnum'))
                        elif mAttr.group('lop') == '<=' and hasattr(memTypeInst, 'constraint_len_lte'):
                            memTypeInst.constraint_len_lte = int(mAttr.group('lopnum'))
                        elif mAttr.group('lop') == '>' and hasattr(memTypeInst, 'constraint_len_gt'):
                            memTypeInst.constraint_len_gt = int(mAttr.group('lopnum'))
                        elif mAttr.group('lop') == '>=' and hasattr(memTypeInst, 'constraint_len_gte'):
                            memTypeInst.constraint_len_gte = int(mAttr.group('lopnum'))
                        else:
                            self._error("Invalid attribute '" + memAttr[0] + "'")

            # Enum value?
            elif mValue:

                memId = mValue.group('id')

                # Not in an enum scope?
                if not isinstance(self._curType, TypeEnum):
                    self._error('Enumeration value outside of enum scope')
                    continue

                # Duplicate enum value?
                if memId in self._curType.values:
                    self._error("Duplicate enumeration value '" + memId + "'")

                # Add the enum value
                self._curType.addValue(memId, doc = self._curDoc)
                self._curDoc = []

            # Unrecognized line syntax
            else:
                self._error('Syntax error')
