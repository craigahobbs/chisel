#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .model import Model, Action, Member, TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool
from .struct import Struct

import re


# Specification language parser class
class SpecParser:

    # Parser regex
    _rePartId = "([_A-Za-z]\w*)"
    _rePartAttr = "(\\[\s*(?P<attrs>" + _rePartId + "(\s*,\s*" + _rePartId + ")*)?\\])"
    _reFindAttr = re.compile(_rePartId + "(?:\s*,\s*|\s*\Z)")
    _reLineCont = re.compile("\\\s*$")
    _reComment = re.compile("^\s*(#.*)?$")
    _reDefinition = re.compile("^(?P<type>action|struct|enum)\s+(?P<id>" + _rePartId + ")\s*$")
    _reSection = re.compile("^\s+(?P<type>input|output)\s*$")
    _reMember = re.compile("^\s+(" + _rePartAttr + "\s+)?(?P<type>" + _rePartId + ")((?P<isArray>\\[\\])|(?P<isDict>{}))?\s+(?P<id>" + _rePartId + ")\s*$")
    _reValue = re.compile("^\s+(?P<id>" + _rePartId + ")\s*$")

    # Types
    _types = {
        "string": TypeString,
        "int": TypeInt,
        "float": TypeFloat,
        "bool": TypeBool
        }

    def __init__(self):

        self.model = Model()
        self.errors = []

        # Finalization state
        self._typeRefs = []

    # Parse a specification from an input stream
    def parse(self, stream, fileName = ""):

        # Set the parser state
        self._parseStream = stream
        self._parseFileName = fileName
        self._parseLine = 0
        self._curAction = None
        self._curType = None

        # Do the work
        self._parse()

    # Finalize parsing (must call after calling parse one or more times)
    def finalize(self):

        # Fixup type refs
        for member in self._typeRefs:
            typeRef = member.typeInst
            typeInst = self._getTypeInst(typeRef)
            if typeInst is not None:
                member.typeInst = typeInst
            else:
                self._error("Unknown member type '%s'" % (typeRef.typeName), fileName = typeRef.fileName, fileLine = typeRef.fileLine)

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
                line = self._reLineCont.sub("", line)
            lines.append(line)
            if not isLineCont:
                break
        return " ".join(lines) if lines else None

    # Type id reference - converted to types on parser finalization
    class _TypeRef:

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
            typeInst = self.model.types.get(typeRef.typeName)

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

        self.errors.append("%s:%d: error: %s" % (fileName or self._parseFileName, fileLine or self._parseLine, msg))

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

                continue

            # Definition?
            elif mDefinition:

                defType = mDefinition.group("type")
                defId = mDefinition.group("id")

                # Action definition
                if defType == "action":

                    # Action already defined?
                    if defId in self.model.actions:
                        error("Action '%s' already defined" % (defId))

                    # Create the new action
                    self._curAction = Action(defId)
                    self._curType = None
                    self.model.actions[self._curAction.name] = self._curAction

                # Struct definition
                elif defType == "struct":

                    # Type already defined?
                    if defId in self._types or defId in self.model.types:
                        error("Redefinition of type '%s'" % (defId))

                    # Create the new struct type
                    self._curAction = None
                    self._curType = TypeStruct(typeName = defId)
                    self.model.types[self._curType.typeName] = self._curType

                # Enum definition
                else:

                    # Type already defined?
                    if defId in self._types or defId in self.model.types:
                        error("Redefinition of type '%s'" % (defId))

                    # Create the new enum type
                    self._curAction = None
                    self._curType = TypeEnum(typeName = defId)
                    self.model.types[self._curType.typeName] = self._curType

            # Section?
            elif mSection:

                sectType = mSection.group("type")

                # Not in an action scope?
                if not self._curAction:
                    error("Action section outside of action scope")
                    continue

                # Set the action section type
                self._curType = self._curAction.inputType if sectType == "input" else self._curAction.outputType

            # Struct member?
            elif mMember:

                memAttrs = self._reFindAttr.findall(mMember.group("attrs")) if mMember.group("attrs") else []
                memIsOptional = "optional" in memAttrs
                memTypeName = mMember.group("type")
                memIsArray = mMember.group("isArray")
                memIsDict = mMember.group("isDict")
                memId = mMember.group("id")

                # Not in a struct scope?
                if not isinstance(self._curType, TypeStruct):
                    error("Member outside of struct scope")
                    continue

                # Unknown attributes?
                for attr in [attr for attr in memAttrs if attr not in ("optional")]:
                    error("Unknown attribute '%s'" % (attr))

                # Member ID already defined?
                if memId in self._curType.members:
                    error("Member '%s' already defined" % (memTypeName))

                # Add the struct member
                memTypeRef = self._TypeRef(self._parseFileName, self._parseLine, memTypeName, memIsArray, memIsDict)
                member = Member(memId, self._getTypeInst(memTypeRef) or memTypeRef)
                member.isOptional = memIsOptional
                self._curType.members.append(member)
                if isinstance(member.typeInst, self._TypeRef):
                    self._typeRefs.append(member)

            # Enum value?
            elif mValue:

                memId = mValue.group("id")

                # Not in an enum scope?
                if not isinstance(self._curType, TypeEnum):
                    error("Enumeration value outside of enum scope")
                    continue

                # Duplicate enum value?
                if memId in self._curType.values:
                    error("Duplicate enumeration value '%s'" % (memId))

                # Add the enum value
                self._curType.values.append(memId)

            # Unrecognized line syntax
            else:
                error("Syntax error")
