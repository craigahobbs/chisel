#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .model import Model, Action, Member, TypeStruct, TypeArray, TypeDict, TypeEnum, TypeString, TypeInt, TypeFloat, TypeBool
from .struct import Struct

import re


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

# Type id reference - converted to types on parser finalization
class _TypeRef:
    def __init__(self, typeName):
        self.typeName = typeName

# Specification language parser class
class SpecParser:

    def __init__(self):

        self.model = Model()
        self.errors = []

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

        # Helper to fixup struct member type refs
        def fixupTypeRefs(structTypeInst):
            for member in structTypeInst.members:
                isContainer = isinstance(member.type, TypeArray) or isinstance(member.type, TypeDict)
                if isContainer:
                    memberType = member.type.type
                else:
                    memberType = member.type
                if isinstance(memberType, _TypeRef):
                    memberType = self.model.types.get(memberType.typeName)
                    if memberType is None:
                        error("Unknown member type '%s'" % (memTypeName))
                    elif isContainer:
                        member.type.type = memberType
                    else:
                        member.type = memberType

        # Convert action type refs
        for action in self.model.actions.itervalues():
            fixupTypeRefs(action.inputType)
            fixupTypeRefs(action.outputType)

        # Convert struct type refs
        for userType in self.model.types.itervalues():
            if isinstance(userType, TypeStruct):
                fixupTypeRefs(userType)

    # Get a line from the current stream
    def _getLine(self):

        lines = []
        while True:
            line = self._parseStream.readline()
            if not line:
                break
            self._parseLine += 1
            isLineCont = _reLineCont.search(line)
            if isLineCont:
                line = _reLineCont.sub("", line)
            lines.append(line)
            if not isLineCont:
                break
        return " ".join(lines) if lines else None

    # Record an error
    def _error(self, msg):

        self.errors.append("%s:%d: error: %s" % (self._parseFileName, self._parseLine, msg))

    # Parse a specification from a stream
    def _parse(self):

        # Process each line
        while True:

            # Read a line (including continuation)
            line = self._getLine()
            if line is None:
                break

            # Match line syntax
            mComment = _reComment.search(line)
            mDefinition = _reDefinition.search(line)
            mSection = _reSection.search(line)
            mMember = _reMember.search(line)
            mValue = _reValue.search(line)

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
                    if defId in _types or defId in self.model.types:
                        error("Redefinition of type '%s'" % (defId))

                    # Create the new struct type
                    self._curAction = None
                    self._curType = TypeStruct(typeName = defId)
                    self.model.types[self._curType.typeName] = self._curType

                # Enum definition
                else:

                    # Type already defined?
                    if defId in _types or defId in self.model.types:
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

                memAttrs = _reFindAttr.findall(mMember.group("attrs")) if mMember.group("attrs") else []
                memIsOptional = "optional" in memAttrs
                memTypeName = mMember.group("type")
                memIsArray = mMember.group("isArray")
                memIsDict = mMember.group("isDict")
                memId = mMember.group("id")

                # Not in a struct scope?
                if not isinstance(self._curType, TypeStruct):
                    error("Member outside of struct scope")
                    continue

                # Create the type instance
                memTypeClass = _types.get(memTypeName)
                if memTypeClass:
                    memTypeInst = memTypeClass(typeName = memTypeName)
                else:
                    memTypeInst = _TypeRef(memTypeName)

                # Array or dict type?
                if memIsArray:
                    memTypeInst = TypeArray(memTypeInst)
                elif memIsDict:
                    memTypeInst = TypeDict(memTypeInst)

                # Unknown attributes?
                for attr in [attr for attr in memAttrs if attr not in ("optional")]:
                    error("Unknown attribute '%s'" % (attr))

                # Member ID already defined?
                if memId in self._curType.members:
                    error("Member '%s' already defined" % (memTypeName))

                # Add the struct member
                member = Member(memId, memTypeInst)
                member.isOptional = memIsOptional
                self._curType.members.append(member)

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
