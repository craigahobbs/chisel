#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .model import Model, Action, Member, TypeStruct, TypeArray, TypeDict, TypeString, TypeInt, TypeFloat, TypeBool
from .struct import Struct

import re
import StringIO


# Parser regex
_rePartId = "([_A-Za-z]\w*)"
_rePartAttr = "(\\[\s*(?P<attrs>" + _rePartId + "(\s*,\s*" + _rePartId + ")*)?\\])"
_reFindAttr = re.compile(_rePartId + "(?:\s*,\s*|\s*\Z)")
_reLineCont = re.compile("\\\s*$")
_reComment = re.compile("^\s*(#.*)?$")
_reDefinition = re.compile("^(?P<type>action|struct)\s+(?P<id>" + _rePartId + ")\s*$")
_reSection = re.compile("^\s+(?P<type>input|output)\s*$")
_reMember = re.compile("^\s+(" + _rePartAttr + "\s+)?(?P<type>" + _rePartId + ")((?P<isArray>\\[\\])|(?P<isDict>{}))?\s+(?P<id>" + _rePartId + ")\s*$")

# Types
_types = {
    "string": TypeString,
    "int": TypeInt,
    "float": TypeFloat,
    "bool": TypeBool
    }

# Parse a specification
def parseSpec(inSpec, fileName = ""):

    # String input?
    if isinstance(inSpec, str):
        inSpec = StringIO.StringIO(inSpec)

    # Parser state
    model = Model()
    errors = []
    ixLine = [0]
    curAction = None
    curType = None

    # Helper to get a line
    def getLine():
        lines = []
        while True:
            line = inSpec.readline()
            if not line:
                break
            ixLine[0] += 1
            isLineCont = _reLineCont.search(line)
            if isLineCont:
                line = _reLineCont.sub("", line)
            lines.append(line)
            if not isLineCont:
                break
        return " ".join(lines) if lines else None

    # Process each line
    while True:

        # Read a line (including continuation)
        line = getLine()
        if line is None:
            break

        # Match line syntax
        mComment = _reComment.search(line)
        mDefinition = _reDefinition.search(line)
        mSection = _reSection.search(line)
        mMember = _reMember.search(line)

        # Comment?
        if mComment:

            pass

        # Definition?
        elif mDefinition:

            defType = mDefinition.group("type")
            defId = mDefinition.group("id")

            # Action definition
            if defType == "action":

                # Action already defined?
                if defId in model.actions:
                    errors.append("%s:%d: error: Action '%s' already defined" % (fileName, ixLine[0], defId))

                # Create the new action
                curAction = Action(defId)
                curType = None
                model.actions[curAction.name] = curAction

            # Struct definition
            else:

                # Type already defined?
                if defId in _types or defId in model.types:
                    errors.append("%s:%d: error: Type '%s' already defined" % (fileName, ixLine[0], defId))

                # Create the new struct type
                curAction = None
                curType = TypeStruct(defId)
                model.types[curType.typeName] = curType

        # Section?
        elif mSection:

            sectType = mSection.group("type")

            # Not in an action scope?
            if not curAction:
                errors.append("%s:%d: error: Action section outside of action scope" % (fileName, ixLine[0]))
                continue

            # Set the action section type
            curType = curAction.inputType if sectType == "input" else curAction.outputType

        # Struct member?
        elif mMember:

            memAttrs = _reFindAttr.findall(mMember.group("attrs")) if mMember.group("attrs") else []
            memIsOptional = "optional" in memAttrs
            memTypeName = mMember.group("type")
            memIsArray = mMember.group("isArray")
            memIsDict = mMember.group("isDict")
            memId = mMember.group("id")

            # Not in a struct scope?
            if not isinstance(curType, TypeStruct):
                errors.append("%s:%d: error: Member outside of struct scope" % (fileName, ixLine[0]))
                continue

            # Create the type instance
            memTypeClass = _types.get(memTypeName)
            if memTypeClass:
                memTypeInst = memTypeClass(typeName = memTypeName)
            else:
                memTypeInst = model.types.get(memTypeName)
                if not memTypeInst:
                    errors.append("%s:%d: error: Unknown member type '%s'" % (fileName, ixLine[0], memTypeName))
                    continue

            # Array or dict type?
            if memIsArray:
                memTypeInst = TypeArray(memTypeInst)
            elif memIsDict:
                memTypeInst = TypeDict(memTypeInst)

            # Unknown attributes?
            for attr in [attr for attr in memAttrs if attr not in ("optional")]:
                errors.append("%s:%d: error: Unknown attribute '%s'" % (fileName, ixLine[0], attr))

            # Member ID already defined?
            if memId in curType.members:
                errors.append("%s:%d: error: Member '%s' already defined" % (fileName, ixLine[0], memTypeName))

            # Add the struct member
            member = Member(memId, memTypeInst)
            member.isOptional = memIsOptional
            curType.members.append(member)

        # Unrecognized line syntax
        else:
            errors.append("%s:%d: error: Syntax error" % (fileName, ixLine[0]))

    return model, errors
