#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct


# Specification class
class Spec:

    def __init__(self):

        self.actions = {}
        self.types = {}


# Action class
class Action:

    def __init__(self, name):

        self.name = name
        self.inputType = TypeStruct()
        self.outputType = TypeStruct()


# Struct member
class Member:

    def __init__(self, name, type):

        self.name = name
        self.type = type
        self.isOptional = False


# Type validation exception
class ValidationError(Exception):

    def __init__(self, msg):

        Exception.__init__(self, msg)

    @classmethod
    def memberError(cls, typeInst, value, member):

        memberDescription = (" for member '%s'" % (".".join(member))) if member else ""
        msg = "Invalid value %r (type %r)%s, expected '%s'" % \
            (value, type(value).__name__, memberDescription, typeInst.__class__.__name__)
        return cls(msg)


# Struct type class
class TypeStruct:

    TypeName = None

    def __init__(self):

        self.members = []

    def validate(self, value, isLoose = False, _member = ()):

        # Convert value to Struct, if necessary
        if isinstance(value, dict):
            value = Struct(value)
        elif not isinstance(value, Struct):
            raise ValidationError.memberError(self, value, _member)

        # Validate members
        memberNames = {}
        for member in self.members:

            # Index the member names
            memberNames[member.name] = member

            # Is the required member not present?
            memberValue = value[member.name]
            if not member.isOptional and memberValue is None:
                raise ValidationError("Required member %r missing" % (member.name))

            # Validate the member value
            memberValueNew = member.type.validate(value[member.name], isLoose, _member = _member + (member.name,))
            if memberValueNew is not memberValue:
                value[member.name] = memberValueNew

        # Check for invalid members
        for valueKey in value:
            if valueKey not in memberNames:
                raise ValidationError("Invalid member %r" % (member.name))

        return value


# Array type class
class TypeArray:

    TypeName = None

    def __init__(self, type):

        self.type = type

    def validate(self, value, isLoose = False, _member = ()):

        # Validate list value type
        if not isinstance(value, list):
            raise ValidationError.memberError(self, value, _member)

        # Validate the list contents
        for ix in xrange(0, len(value)):
            arrayValue = value[ix]
            arrayValueNew = self.type.validate(arrayValue, isLoose, _member = _member + (str(ix),))
            if arrayValueNew is not arrayValue:
                value[ix] = arrayValueNew

        return value


# "string" type class
class TypeString:

    TypeName = "string"

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, str):
            return value
        else:
            raise ValidationError.memberError(self, value, _member)


# "int" type class
class TypeInt:

    TypeName = "int"

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, int):
            return value
        elif isinstance(value, float) and int(value) == value:
            return int(value)
        elif isLoose and isinstance(value, str):
            return int(value)
        else:
            raise ValidationError.memberError(self, value, _member)


# "float" type class
class TypeFloat:

    TypeName = "float"

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, float):
            return value
        elif isinstance(value, int):
            return float(value)
        elif isLoose and isinstance(value, str):
            return float(value)
        else:
            raise ValidationError.memberError(self, value, _member)


# "bool" type class
class TypeBool:

    TypeName = "bool"

    def validate(self, value, isLoose = False, _member = ()):

        if isinstance(value, bool):
            return value
        elif isLoose and isinstance(value, str) and value in ("true", "false"):
            return value in ("true")
        else:
            raise ValidationError.memberError(self, value, _member)
