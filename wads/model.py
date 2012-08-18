#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct


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


# Struct type class
class TypeStruct:

    typeName = None

    def __init__(self):

        self.members = []

    def validate(self, value, isLoose = False):

        # Convert value to Struct, if necessary
        if isinstance(value, dict):
            value = Struct(value)
        elif not isinstance(value, Struct):
            raise ValueError("Expected struct type, got %r" % (type(value)))

        # Validate members
        memberNames = {}
        for member in self.members:

            # Index the member names
            memberNames[member.name] = member

            # Is the required member not present?
            memberValue = value[member.name]
            if not member.isOptional and memberValue is None:
                raise ValueError("Required member %r missing" % (member.name))

            # Validate the member value
            try:
                memberValueNew = member.type.validate(value[member.name])
            except ValueError, e:
                if str(e):
                    raise e
                else:
                    raise ValueError("Invalid value %r of type %r for member %r" % (memberValue, type(memberValue).__name__, member.name))
            if memberValueNew is not memberValue:
                value[member.name] = memberValueNew

        # Check for invalid members
        for valueKey in value:
            if valueKey not in memberNames:
                raise ValueError("Invalid member %r" % (member.name))

        return value


# Array type class
class TypeArray:

    TypeName = None

    def __init__(self, type):

        self.type = type

    def validate(self, value, isLoose = False):

        # Validate list value type
        if not isinstance(value, list):
            raise ValueError("Expected list type, got %r" % (type(value)))

        # Validate the list contents
        for ix in xrange(0, len(value)):
            arrayValue = value[ix]
            try:
                arrayValueNew = self.type.validate(arrayValue)
            except ValueError, e:
                if str(e):
                    raise e
                else:
                    raise ValueError("Invalid list value %r of type %r" % (arrayValue, type(arrayValue).__name__))
            if arrayValueNew is not arrayValue:
                value[ix] = arrayValueNew

        return value


# "string" type class
class TypeString:

    TypeName = "string"

    def __init__(self):

        pass

    def validate(self, value, isLoose = False):

        if isinstance(value, str):
            return value
        else:
            raise ValueError()


# "int" type class
class TypeInt:

    TypeName = "int"

    def __init__(self):

        pass

    def validate(self, value, isLoose = False):

        if isinstance(value, int):
            return value
        elif isinstance(value, float) and int(value) == value:
            return int(value)
        elif isLoose and isinstance(value, str):
            return int(value)
        else:
            raise ValueError()


# "float" type class
class TypeFloat:

    TypeName = "float"

    def __init__(self):

        pass

    def validate(self, value, isLoose = False):

        if isinstance(value, float):
            return value
        elif isinstance(value, int):
            return float(value)
        elif isLoose and isinstance(value, str):
            return float(value)
        else:
            raise ValueError()


# "bool" type class
class TypeBool:

    TypeName = "bool"

    def __init__(self):

        pass

    def validate(self, value, isLoose = False):

        if isinstance(value, bool):
            return value
        elif isLoose and isinstance(value, str) and value in ("true", "false"):
            return value in ("true")
        else:
            raise ValueError()
