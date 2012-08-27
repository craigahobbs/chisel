#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct


# Specification class
class Model:

    def __init__(self):

        self.types = {}
        self.actions = {}


# Action class
class Action:

    def __init__(self, name):

        self.name = name
        self.inputType = TypeStruct()
        self.outputType = TypeStruct()


# Struct member
class Member:

    def __init__(self, name, typeInst, isOptional = False):

        self.name = name
        self.typeInst = typeInst
        self.isOptional = isOptional


# Type validation exception
class ValidationError(Exception):

    def __init__(self, msg):

        Exception.__init__(self, msg)

    @staticmethod
    def memberError(typeInst, value, member):

        if isinstance(value, Struct):
            valueTypeName = "struct"
        else:
            valueTypeName = value.__class__.__name__
        memberDescription = (" for member '%s'" % (".".join([str(x) for x in member]))) if member else ""
        msg = "Invalid value %r (type %r)%s, expected type '%s'" % \
            (value, valueTypeName, memberDescription, typeInst.typeName)
        return ValidationError(msg)


# Struct type
class TypeStruct:

    def __init__(self, typeName = "struct"):

        self.typeName = typeName
        self.members = []

    def validate(self, value, isLoose = False, _member = ()):

        # Validate dict value type
        if not isinstance(value, dict) and not isinstance(value, Struct):
            raise ValidationError.memberError(self, value, _member)

        # Validate members
        memberNames = {}
        for member in self.members:

            # Index the member names
            memberNames[member.name] = member

            # Is the required member not present?
            memberValue = (value if isinstance(value, dict) else value()).get(member.name)
            if memberValue is None:
                if not member.isOptional:
                    raise ValidationError("Required member %r missing" % (member.name))
            else:
                # Validate the member value
                memberValueNew = member.typeInst.validate(memberValue, isLoose, _member = _member + (member.name,))
                if memberValueNew is not memberValue:
                    value[member.name] = memberValueNew

        # Check for invalid members
        for valueKey in value:
            if valueKey not in memberNames:
                raise ValidationError("Invalid member %r" % (member.name))

        return value


# Array type
class TypeArray:

    def __init__(self, typeInst, typeName = "array"):

        self.typeName = typeName
        self.typeInst = typeInst

    def validate(self, value, isLoose = False, _member = ()):

        # Validate list value type
        if not isinstance(value, list):
            raise ValidationError.memberError(self, value, _member)

        # Validate the list contents
        for ix in xrange(0, len(value)):
            arrayValue = value[ix]
            arrayValueNew = self.typeInst.validate(arrayValue, isLoose, _member = _member + (str(ix),))
            if arrayValueNew is not arrayValue:
                value[ix] = arrayValueNew

        return value


# Dict type
class TypeDict:

    def __init__(self, typeInst, typeName = "dict"):

        self.typeName = typeName
        self.typeInst = typeInst

    def validate(self, value, isLoose = False, _member = ()):

        # Validate dict value type
        if not isinstance(value, dict) and not isinstance(value, Struct):
            raise ValidationError.memberError(self, value, _member)

        # Validate the dict key/value pairs
        for key in value:

            # Dict keys must be strings
            if not isinstance(key, str):
                raise ValidationError.memberError(TypeString(), key, _member + (key,))

            # Validate the value
            dictValue = value[key]
            dictValueNew = self.typeInst.validate(dictValue, isLoose, _member = _member + (key,))
            if dictValueNew is not dictValue:
                value[key] = dictValueNew

        return value


# Enumeration type
class TypeEnum:

    def __init__(self, values = None, typeName = "enum"):

        self.typeName = typeName
        self.values = values or []

    def validate(self, value, isLoose = False, _member = ()):

        if not isinstance(value, str):
            raise ValidationError.memberError(self, value, _member)
        elif value not in self.values:
            raise ValidationError("Invalid enumeration value '%s' for '%s'" % (value, self.typeName))
        else:
            return value


# String type
class TypeString:

    def __init__(self, typeName = "string"):

        self.typeName = typeName

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, str):
            return value
        else:
            raise ValidationError.memberError(self, value, _member)


# Int type
class TypeInt:

    def __init__(self, typeName = "int"):

        self.typeName = typeName

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, int):
            return value
        elif isinstance(value, float) and int(value) == value:
            return int(value)
        elif isLoose and isinstance(value, str):
            return int(value)
        else:
            raise ValidationError.memberError(self, value, _member)


# Float type
class TypeFloat:

    def __init__(self, typeName = "float"):

        self.typeName = typeName

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, float):
            return value
        elif isinstance(value, int):
            return float(value)
        elif isLoose and isinstance(value, str):
            return float(value)
        else:
            raise ValidationError.memberError(self, value, _member)


# Bool type
class TypeBool:

    def __init__(self, typeName = "bool"):

        self.typeName = typeName

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, bool):
            return value
        elif isLoose and isinstance(value, str) and value in ("true", "false"):
            return value in ("true")
        else:
            raise ValidationError.memberError(self, value, _member)
