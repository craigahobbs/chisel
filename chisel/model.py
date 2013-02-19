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

from .compat import basestring_, long_, xrange_
from .struct import Struct

from datetime import datetime, timedelta, tzinfo
from decimal import Decimal
import time
import re
from uuid import UUID


# Python json module "default" function
def jsonDefault(obj):

    # Unwrap structs
    if isinstance(obj, Struct):
        obj = obj()

    # Control serialization of specific types
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            dt = datetime(obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second, obj.microsecond, TypeDatetime.TZLocal())
        else:
            dt = obj
        return dt.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    else:
        return obj


# Floating point number with precision for JSON encoding
class JsonFloat(float):

    def __new__(cls, value, prec):

        return float.__new__(cls, value)

    def __init__(self, value, prec):

        self._formatString = "." + str(prec) + "f"

    def __repr__(self):

        return format(self, self._formatString).rstrip("0").rstrip(".")

    def __str__(self):

        return self.__repr__()


# Type validation exception
class ValidationError(Exception):

    def __init__(self, msg, member = None):

        Exception.__init__(self, msg)
        self.member = member

    @classmethod
    def memberSyntax(cls, members):

        if members:
            return "".join([((".%s" if isinstance(x, basestring_) else "[%d]") % (x,)) for x in members]).lstrip(".")
        else:
            return None

    @classmethod
    def memberError(cls, typeInst, value, members):

        # Unwrap structs
        if isinstance(value, Struct):
            value = value()

        # Format the error string
        memberSyntax = cls.memberSyntax(members)
        msg = "Invalid value %r (type '%s')%s, expected type '%s'" % \
            (value, value.__class__.__name__, " for member '%s'" % (memberSyntax,) if memberSyntax else "", typeInst.typeName)

        return ValidationError(msg, member = memberSyntax)


# Struct type
class TypeStruct:

    class Member:
        def __init__(self, name, typeInst, isOptional = False, doc = None):
            self.name = name
            self.typeInst = typeInst
            self.isOptional = isOptional
            self.doc = [] if doc is None else doc

    def __init__(self, typeName = "struct", doc = None):

        self.typeName = typeName
        self.members = []
        self.doc = [] if doc is None else doc

    def validate(self, value, acceptString = False, _member = ()):

        # Unwrap structs
        valueInner = value() if isinstance(value, Struct) else value

        # Validate dict value type
        if not isinstance(valueInner, dict):
            raise ValidationError.memberError(self, valueInner, _member)

        # Validate members
        memberNames = {}
        for member in self.members:

            # Index the member names
            memberNames[member.name] = member

            # Is the required member not present?
            memberValue = valueInner.get(member.name)
            if memberValue is None:
                if not member.isOptional:
                    raise ValidationError("Required member '%s' missing" % (ValidationError.memberSyntax((_member + (member.name,)))))
            else:
                # Validate the member value
                memberValueNew = member.typeInst.validate(memberValue, acceptString = acceptString, _member = _member + (member.name,))
                if memberValueNew is not memberValue:
                    valueInner[member.name] = memberValueNew

        # Check for invalid members
        for valueKey in valueInner:
            if valueKey not in memberNames:
                raise ValidationError("Invalid member '%s'" % (ValidationError.memberSyntax((_member + (valueKey,)))))

        return value


# Array type
class TypeArray:

    def __init__(self, typeInst, typeName = "array"):

        self.typeName = typeName
        self.typeInst = typeInst

    def validate(self, value, acceptString = False, _member = ()):

        # Unwrap structs
        valueInner = value() if isinstance(value, Struct) else value

        # Validate list value type
        if acceptString and isinstance(value, basestring_) and len(value) == 0:
            return []
        elif not isinstance(valueInner, (list, tuple)):
            raise ValidationError.memberError(self, valueInner, _member)

        # Validate the list contents
        for ix in xrange_(0, len(valueInner)):
            arrayValue = valueInner[ix]
            arrayValueNew = self.typeInst.validate(arrayValue, acceptString = acceptString, _member = _member + (ix,))
            if arrayValueNew is not arrayValue:
                valueInner[ix] = arrayValueNew

        return value


# Dict type
class TypeDict:

    def __init__(self, typeInst, typeName = "dict"):

        self.typeName = typeName
        self.typeInst = typeInst

    def validate(self, value, acceptString = False, _member = ()):

        # Unwrap structs
        valueInner = value() if isinstance(value, Struct) else value

        # Validate dict value type
        if acceptString and isinstance(value, basestring_) and len(value) == 0:
            return {}
        elif not isinstance(valueInner, dict):
            raise ValidationError.memberError(self, valueInner, _member)

        # Validate the dict key/value pairs
        for key in valueInner:

            # Dict keys must be strings
            if not isinstance(key, basestring_):
                raise ValidationError.memberError(TypeString(), key, _member + (key,))

            # Validate the value
            dictValue = valueInner[key]
            dictValueNew = self.typeInst.validate(dictValue, acceptString = acceptString, _member = _member + (key,))
            if dictValueNew is not dictValue:
                valueInner[key] = dictValueNew

        return value


# Enumeration type
class TypeEnum:

    class Value:

        def __init__(self, value, doc = None):

            self.value = value
            self.doc = [] if doc is None else doc

        def __eq__(self, other):

            return self.value == other

    def __init__(self, typeName = "enum", doc = None):

        self.typeName = typeName
        self.values = []
        self.doc = [] if doc is None else doc

    def validate(self, value, acceptString = False, _member = ()):

        if not isinstance(value, basestring_) or value not in self.values:
            raise ValidationError.memberError(self, value, _member)
        else:
            return value


# String type
class TypeString:

    def __init__(self, typeName = "string"):

        self.typeName = typeName
        self.constraint_len_lt = None
        self.constraint_len_lte = None
        self.constraint_len_gt = None
        self.constraint_len_gte = None

    def validate(self, value, acceptString = False, _member = ()):

        if isinstance(value, basestring_):
            result = value
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check contraints
        if self.constraint_len_lt is not None and not len(result) < self.constraint_len_lt:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_len_lte is not None and not len(result) <= self.constraint_len_lte:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_len_gt is not None and not len(result) > self.constraint_len_gt:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_len_gte is not None and not len(result) >= self.constraint_len_gte:
            raise ValidationError.memberError(self, value, _member)

        return result


# Int type
class TypeInt:

    def __init__(self, typeName = "int"):

        self.typeName = typeName
        self.constraint_lt = None
        self.constraint_lte = None
        self.constraint_gt = None
        self.constraint_gte = None

    def validate(self, value, acceptString = False, _member = ()):

        if isinstance(value, (int, long_)) and not isinstance(value, bool):
            result = value
        elif isinstance(value, (float, Decimal)):
            result = int(value)
            if result != value:
                raise ValidationError.memberError(self, value, _member)
        elif acceptString and isinstance(value, basestring_):
            try:
                result = int(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check contraints
        if self.constraint_lt is not None and not result < self.constraint_lt:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_lte is not None and not result <= self.constraint_lte:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_gt is not None and not result > self.constraint_gt:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_gte is not None and not result >= self.constraint_gte:
            raise ValidationError.memberError(self, value, _member)

        return result


# Float type
class TypeFloat:

    def __init__(self, typeName = "float"):

        self.typeName = typeName
        self.constraint_lt = None
        self.constraint_lte = None
        self.constraint_gt = None
        self.constraint_gte = None

    def validate(self, value, acceptString = False, _member = ()):

        if isinstance(value, float):
            result = value
        elif isinstance(value, (int, long_, Decimal)) and not isinstance(value, bool):
            result = float(value)
        elif acceptString and isinstance(value, basestring_):
            try:
                result = float(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check contraints
        if self.constraint_lt is not None and not result < self.constraint_lt:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_lte is not None and not result <= self.constraint_lte:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_gt is not None and not result > self.constraint_gt:
            raise ValidationError.memberError(self, value, _member)
        if self.constraint_gte is not None and not result >= self.constraint_gte:
            raise ValidationError.memberError(self, value, _member)

        return result


# Bool type
class TypeBool:

    def __init__(self, typeName = "bool"):

        self.typeName = typeName

    def validate(self, value, acceptString = False, _member = ()):

        if isinstance(value, bool):
            return value
        elif acceptString and isinstance(value, basestring_) and value in ("true", "false"):
            return value in ("true")
        else:
            raise ValidationError.memberError(self, value, _member)


# Datetime type
class TypeDatetime:

    def __init__(self, typeName = "datetime"):

        self.typeName = typeName

    def validate(self, value, acceptString = False, _member = ()):

        if isinstance(value, datetime):
            return value
        elif isinstance(value, basestring_):
            try:
                return self.parseISO8601Datetime(value)
            except ValueError:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)

    # ISO 8601 regex
    _reISO8601 = re.compile("^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})" +
                            "(T(?P<hour>\d{2}):(?P<min>\d{2}?):(?P<sec>\d{2})([.,](?P<fracsec>\d{1,7}))?" +
                            "(Z|(?P<offsign>[+-])(?P<offhour>\d{2})(:?(?P<offmin>\d{2}))?))?\s*$")

    # GMT tzinfo class for parseISO8601Datetime
    class TZUTC(tzinfo):

        def utcoffset(self, dt):
            return timedelta(0)

        def dst(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return "UTC"

    # Local time zone tzinfo class (for jsonDefault)
    class TZLocal(tzinfo):

        def utcoffset(self, dt):
            if self._isdst(dt):
                return self._dstOffset()
            else:
                return self._stdOffset()

        def dst(self, dt):
            if self._isdst(dt):
                return self._dstOffset() - self._stdOffset()
            else:
                return timedelta(0)

        def tzname(self, dt):
            return time.tzname[self._isdst(dt)]

        @classmethod
        def _stdOffset(cls):
            return timedelta(seconds = -time.timezone)

        @classmethod
        def _dstOffset(cls):
            if time.daylight:
                return timedelta(seconds = -time.altzone)
            else:
                return cls._stdOffset()

        @classmethod
        def _isdst(cls, dt):
            tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, 0)
            stamp = time.mktime(tt)
            tt = time.localtime(stamp)
            return tt.tm_isdst > 0

    # Static helper function to parse ISO 8601 date/time
    @classmethod
    def parseISO8601Datetime(cls, s):

        # Match ISO 8601?
        m = cls._reISO8601.search(s)
        if not m:
            raise ValueError("Expected ISO 8601 date/time")

        # Extract ISO 8601 components
        year = int(m.group("year"))
        month = int(m.group("month"))
        day = int(m.group("day"))
        hour = int(m.group("hour")) if m.group("hour") else 0
        minute = int(m.group("min")) if m.group("min") else 0
        sec = int(m.group("sec")) if m.group("sec") else 0
        microsec = int(float("." + m.group("fracsec")) * 1000000) if m.group("fracsec") else 0
        offhour = int(m.group("offsign") + m.group("offhour")) if m.group("offhour") else 0
        offmin = int(m.group("offsign") + m.group("offmin")) if m.group("offmin") else 0

        return (datetime(year, month, day, hour, minute, sec, microsec, cls.TZUTC()) -
                timedelta(hours = offhour, minutes = offmin))


# Uuid type
class TypeUuid:

    def __init__(self, typeName = "uuid"):

        self.typeName = typeName

    def validate(self, value, acceptString = False, _member = ()):

        if isinstance(value, UUID):
            return value
        elif isinstance(value, basestring_):
            try:
                return UUID(value)
            except ValueError:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)
