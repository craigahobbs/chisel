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

from .compat import basestring_, iteritems, long_

from datetime import datetime, timedelta, tzinfo
import time
import re
from uuid import UUID


# JSON encoding for datetime objects
class JsonDatetime(float):
    __slots__ = ('value', 'json')

    _reTimeZeros = re.compile('(T\d{2}(:(?!00)\d{2})*)((:00)*)')
    _reTzZulu = re.compile('[+-]00:00$')
    _reTzZeros = re.compile(':00$')

    def __new__(cls, value):
        return float.__new__(cls, 0)

    def __init__(self, value):
        if value.tzinfo is None:
            self.value = value.replace(tzinfo = tzlocal)
        else:
            self.value = value

        # Format as ISO 8601 and trim-down as much as possible
        iso = self._reTimeZeros.sub('\\1', self.value.isoformat())
        isoZulu = self._reTzZulu.sub('Z', iso)
        if isoZulu is not iso:
            iso = isoZulu
        else:
            iso = self._reTzZeros.sub('', iso)

        self.json = '"' + iso + '"'

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json


# Floating point number with precision for JSON encoding
class JsonFloat(float):
    __slots__ = ('json',)

    def __new__(cls, value, prec):
        return float.__new__(cls, value)

    def __init__(self, value, prec):
        self.json = format(value, '.' + str(prec) + 'f').rstrip('0').rstrip('.')

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json


# JSON encoding for UUID objects
class JsonUUID(float):
    __slots__ = ('value', 'json')

    def __new__(cls, value):
        return float.__new__(cls, 0)

    def __init__(self, value):
        self.value = value
        self.json = '"' + str(value) + '"'

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json


# Fake JSON float types
FAKE_FLOAT_TYPES = (JsonDatetime, JsonUUID)


# Validation mode
VALIDATE_DEFAULT = 0
VALIDATE_QUERY_STRING = 1
VALIDATE_JSON_INPUT = 2
VALIDATE_JSON_OUTPUT = 3

# Immutable validation modes
IMMUTABLE_VALIDATION_MODES = (VALIDATE_DEFAULT, VALIDATE_JSON_OUTPUT)


# Type validation exception
class ValidationError(Exception):

    def __init__(self, msg, member = None):
        Exception.__init__(self, msg)
        self.member = member

    @classmethod
    def _flattenMembers(cls, members):
        for member2 in members:
            if isinstance(member2, tuple):
                for member3 in cls._flattenMembers(member2):
                    yield member3
            else:
                yield member2

    @classmethod
    def memberSyntax(cls, members):
        if members:
            return ''.join((('.' + x) if isinstance(x, basestring_) else ('[' + repr(x) + ']')) for x in cls._flattenMembers(members)).lstrip('.')
        return None

    @classmethod
    def memberError(cls, typeInst, value, members, constraintSyntax = None):
        memberSyntax = cls.memberSyntax(members)
        msg = 'Invalid value ' + repr(value) + " (type '" + value.__class__.__name__ + "')" + \
              ((" for member '" + memberSyntax + "'") if memberSyntax else '') + \
              ", expected type '" + typeInst.typeName + "'" + \
              ((' [' + constraintSyntax + ']') if constraintSyntax else '')
        return ValidationError(msg, member = memberSyntax)


# Struct type
class TypeStruct(object):
    __slots__ = ('typeName', 'isUnion', '_members', '_membersDict', 'doc')

    class Member(object):
        __slots__ = ('name', 'typeInst', 'isOptional', 'doc')

        def __init__(self, name, typeInst, isOptional = False, doc = None):
            self.name = name
            self.typeInst = typeInst
            self.isOptional = isOptional
            self.doc = [] if doc is None else doc

    def __init__(self, typeName = None, isUnion = False, doc = None):
        self.typeName = typeName if typeName else ('union' if isUnion else 'struct')
        self.isUnion = isUnion
        self._members = []
        self._membersDict = {}
        self.doc = [] if doc is None else doc

    def addMember(self, name, typeInst, isOptional = False, doc = None):
        member = self.Member(name, typeInst, isOptional or self.isUnion, doc)
        self._members.append(member)
        self._membersDict[name] = member
        return member

    @property
    def members(self):
        return self._members

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, dict):
            valueX = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            valueX = {}
        else:
            raise ValidationError.memberError(self, value, _member)

        # Valid union?
        if self.isUnion:
            if len(valueX) != 1:
                raise ValidationError.memberError(self, value, _member)

        # Result a copy?
        valueCopy = None if mode in IMMUTABLE_VALIDATION_MODES else {}

        # Validate all member values
        try:
            membersDict = self._membersDict
            for memberName, memberValue in iteritems(valueX):
                memberValueX = membersDict[memberName].typeInst.validate(memberValue, mode, (_member, memberName))
                if valueCopy is not None:
                    valueCopy[memberName] = memberValueX
        except KeyError:
            raise ValidationError("Unknown member '" + ValidationError.memberSyntax((_member, memberName)) + "'")

        # Any missing required members?
        if len(self._members) != len(valueX):
            for member in self._members:
                if not member.isOptional and member.name not in valueX:
                    raise ValidationError("Required member '" + ValidationError.memberSyntax((_member, member.name)) + "' missing")

        return value if valueCopy is None else valueCopy


# Array type
class TypeArray(object):
    __slots__ = ('typeName', 'typeInst', 'constraint_len_lt', 'constraint_len_lte', 'constraint_len_gt', 'constraint_len_gte', 'constraint_len_eq')

    def __init__(self, typeInst, typeName = 'array'):
        self.typeName = typeName
        self.typeInst = typeInst
        self.constraint_len_lt = None
        self.constraint_len_lte = None
        self.constraint_len_gt = None
        self.constraint_len_gte = None
        self.constraint_len_eq = None

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, list) or isinstance(value, tuple):
            valueX = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            valueX = []
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check length constraints
        if self.constraint_len_lt is not None and not len(valueX) < self.constraint_len_lt:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len < ' + repr(JsonFloat(self.constraint_len_lt, 6)))
        if self.constraint_len_lte is not None and not len(valueX) <= self.constraint_len_lte:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len <= ' + repr(JsonFloat(self.constraint_len_lte, 6)))
        if self.constraint_len_gt is not None and not len(valueX) > self.constraint_len_gt:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len > ' + repr(JsonFloat(self.constraint_len_gt, 6)))
        if self.constraint_len_gte is not None and not len(valueX) >= self.constraint_len_gte:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len >= ' + repr(JsonFloat(self.constraint_len_gte, 6)))
        if self.constraint_len_eq is not None and not len(valueX) == self.constraint_len_eq:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len == ' + repr(JsonFloat(self.constraint_len_eq, 6)))

        # Result a copy?
        valueCopy = None if mode in IMMUTABLE_VALIDATION_MODES else []

        # Validate the list contents
        typeInst = self.typeInst
        ixArrayValue = 0
        for arrayValue in valueX:
            arrayValue = typeInst.validate(arrayValue, mode, (_member, ixArrayValue))
            if valueCopy is not None:
                valueCopy.append(arrayValue)
            ixArrayValue += 1

        return value if valueCopy is None else valueCopy


# Dict type
class TypeDict(object):
    __slots__ = ('typeName', 'typeInst', 'constraint_len_lt', 'constraint_len_lte', 'constraint_len_gt', 'constraint_len_gte', 'constraint_len_eq')

    def __init__(self, typeInst, typeName = 'dict'):
        self.typeName = typeName
        self.typeInst = typeInst
        self.constraint_len_lt = None
        self.constraint_len_lte = None
        self.constraint_len_gt = None
        self.constraint_len_gte = None
        self.constraint_len_eq = None

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, dict):
            valueX = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            valueX = {}
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check length constraints
        if self.constraint_len_lt is not None and not len(valueX) < self.constraint_len_lt:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len < ' + repr(JsonFloat(self.constraint_len_lt, 6)))
        if self.constraint_len_lte is not None and not len(valueX) <= self.constraint_len_lte:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len <= ' + repr(JsonFloat(self.constraint_len_lte, 6)))
        if self.constraint_len_gt is not None and not len(valueX) > self.constraint_len_gt:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len > ' + repr(JsonFloat(self.constraint_len_gt, 6)))
        if self.constraint_len_gte is not None and not len(valueX) >= self.constraint_len_gte:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len >= ' + repr(JsonFloat(self.constraint_len_gte, 6)))
        if self.constraint_len_eq is not None and not len(valueX) == self.constraint_len_eq:
            raise ValidationError.memberError(self, valueX, _member, constraintSyntax = 'len == ' + repr(JsonFloat(self.constraint_len_eq, 6)))

        # Result a copy?
        valueCopy = None if mode in IMMUTABLE_VALIDATION_MODES else {}

        # Validate the dict key/value pairs
        typeInst = self.typeInst
        for dictKey, dictValue in iteritems(valueX):

            # Dict keys must be strings
            if not isinstance(dictKey, basestring_):
                raise ValidationError.memberError(TypeString(), dictKey, (_member, dictKey))

            # Validate the value
            dictValueX = typeInst.validate(dictValue, mode, (_member, dictKey))
            if valueCopy is not None:
                valueCopy[dictKey] = dictValueX

        return value if valueCopy is None else valueCopy


# Enumeration type
class TypeEnum(object):
    __slots__ = ('typeName', 'values', 'doc')

    class Value(object):
        __slots__ = ('value', 'doc')

        def __init__(self, valueString, doc = None):
            self.value = valueString
            self.doc = [] if doc is None else doc

        def __eq__(self, other):
            return self.value == other

    def __init__(self, typeName = 'enum', doc = None):
        self.typeName = typeName
        self.values = []
        self.doc = [] if doc is None else doc

    def addValue(self, valueString, doc = None):
        value = self.Value(valueString, doc)
        self.values.append(value)
        return value

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate the value
        if value not in self.values:
            raise ValidationError.memberError(self, value, _member)

        return value


# String type
class TypeString(object):
    __slots__ = ('typeName', 'constraint_len_lt', 'constraint_len_lte', 'constraint_len_gt', 'constraint_len_gte', 'constraint_len_eq')

    def __init__(self, typeName = 'string'):
        self.typeName = typeName
        self.constraint_len_lt = None
        self.constraint_len_lte = None
        self.constraint_len_gt = None
        self.constraint_len_gte = None
        self.constraint_len_eq = None

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate the value
        if not isinstance(value, basestring_):
            raise ValidationError.memberError(self, value, _member)

        # Check length constraints
        if self.constraint_len_lt is not None and not len(value) < self.constraint_len_lt:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = 'len < ' + repr(JsonFloat(self.constraint_len_lt, 6)))
        if self.constraint_len_lte is not None and not len(value) <= self.constraint_len_lte:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = 'len <= ' + repr(JsonFloat(self.constraint_len_lte, 6)))
        if self.constraint_len_gt is not None and not len(value) > self.constraint_len_gt:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = 'len > ' + repr(JsonFloat(self.constraint_len_gt, 6)))
        if self.constraint_len_gte is not None and not len(value) >= self.constraint_len_gte:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = 'len >= ' + repr(JsonFloat(self.constraint_len_gte, 6)))
        if self.constraint_len_eq is not None and not len(value) == self.constraint_len_eq:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = 'len == ' + repr(JsonFloat(self.constraint_len_eq, 6)))

        return value


# Int type
class TypeInt(object):
    __slots__ = ('typeName', 'constraint_lt', 'constraint_lte', 'constraint_gt', 'constraint_gte')

    def __init__(self, typeName = 'int'):
        self.typeName = typeName
        self.constraint_lt = None
        self.constraint_lte = None
        self.constraint_gt = None
        self.constraint_gte = None

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if (isinstance(value, int) or isinstance(value, long_)) and not isinstance(value, bool):
            valueX = value
        elif isinstance(value, float) and not isinstance(value, FAKE_FLOAT_TYPES):
            valueX = int(value)
            if valueX != value:
                raise ValidationError.memberError(self, value, _member)
        elif mode == VALIDATE_QUERY_STRING and isinstance(value, basestring_):
            try:
                valueX = int(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check constraints
        if self.constraint_lt is not None and not valueX < self.constraint_lt:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '< ' + repr(JsonFloat(self.constraint_lt, 6)))
        if self.constraint_lte is not None and not valueX <= self.constraint_lte:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '<= ' + repr(JsonFloat(self.constraint_lte, 6)))
        if self.constraint_gt is not None and not valueX > self.constraint_gt:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '> ' + repr(JsonFloat(self.constraint_gt, 6)))
        if self.constraint_gte is not None and not valueX >= self.constraint_gte:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '>= ' + repr(JsonFloat(self.constraint_gte, 6)))

        return value if mode in IMMUTABLE_VALIDATION_MODES else valueX


# Float type
class TypeFloat(object):
    __slots__ = ('typeName', 'constraint_lt', 'constraint_lte', 'constraint_gt', 'constraint_gte')

    def __init__(self, typeName = 'float'):
        self.typeName = typeName
        self.constraint_lt = None
        self.constraint_lte = None
        self.constraint_gt = None
        self.constraint_gte = None

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, float) and not isinstance(value, FAKE_FLOAT_TYPES):
            valueX = value
        elif (isinstance(value, int) or isinstance(value, long_)) and not isinstance(value, bool):
            valueX = float(value)
        elif mode == VALIDATE_QUERY_STRING and isinstance(value, basestring_):
            try:
                valueX = float(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)

        # Check constraints
        if self.constraint_lt is not None and not valueX < self.constraint_lt:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '< ' + repr(JsonFloat(self.constraint_lt, 6)))
        if self.constraint_lte is not None and not valueX <= self.constraint_lte:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '<= ' + repr(JsonFloat(self.constraint_lte, 6)))
        if self.constraint_gt is not None and not valueX > self.constraint_gt:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '> ' + repr(JsonFloat(self.constraint_gt, 6)))
        if self.constraint_gte is not None and not valueX >= self.constraint_gte:
            raise ValidationError.memberError(self, value, _member, constraintSyntax = '>= ' + repr(JsonFloat(self.constraint_gte, 6)))

        return value if mode in IMMUTABLE_VALIDATION_MODES else valueX


# Bool type
class TypeBool(object):
    __slots__ = ('typeName',)

    VALUES = {
        'true' : True,
        'false': False
    }

    def __init__(self, typeName = 'bool'):
        self.typeName = typeName

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, bool):
            return value
        elif mode == VALIDATE_QUERY_STRING and isinstance(value, basestring_):
            try:
                return self.VALUES[value]
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)


# Uuid type
class TypeUuid(object):
    __slots__ = ('typeName',)

    def __init__(self, typeName = 'uuid'):
        self.typeName = typeName

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, UUID):
            if mode == VALIDATE_JSON_OUTPUT:
                raise ValidationError.memberError(self, value, _member, constraintSyntax = 'JsonUUID object required')
            return value
        elif mode == VALIDATE_JSON_OUTPUT and isinstance(value, JsonUUID):
            return value
        elif mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, basestring_):
            try:
                return UUID(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)


# Datetime type
class TypeDatetime(object):
    __slots__ = ('typeName',)

    def __init__(self, typeName = 'datetime'):
        self.typeName = typeName

    def validate(self, value, mode = VALIDATE_DEFAULT, _member = ()):

        # Validate and translate the value
        if isinstance(value, datetime):
            if mode == VALIDATE_JSON_OUTPUT:
                raise ValidationError.memberError(self, value, _member, constraintSyntax = 'JsonDatetime object required')

            # Set a time zone, if necessary
            if mode not in IMMUTABLE_VALIDATION_MODES and value.tzinfo is None:
                return value.replace(tzinfo = tzlocal)

            return value
        elif mode == VALIDATE_JSON_OUTPUT and isinstance(value, JsonDatetime):
            return value
        elif mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, basestring_):
            try:
                return parseISO8601Datetime(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)


# GMT tzinfo class for parseISO8601Datetime (from Python docs)
_timedelta_zero = timedelta(0)

class _TZUTC(tzinfo): # pragma: no cover
    __slots__ = ()

    def utcoffset(self, dt):
        return _timedelta_zero

    def dst(self, dt):
        return _timedelta_zero

    def tzname(self, dt):
        return 'UTC'

tzutc = _TZUTC()


# Local time zone tzinfo class (from Python docs)
class _TZLocal(tzinfo): # pragma: no cover
    __slots__ = ()

    def utcoffset(self, dt):
        if self._isdst(dt):
            return self._dstOffset()
        else:
            return self._stdOffset()

    def dst(self, dt):
        if self._isdst(dt):
            return self._dstOffset() - self._stdOffset()
        else:
            return _timedelta_zero

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

tzlocal = _TZLocal()


# ISO 8601 regex
_reISO8601 = re.compile('^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})' +
                       '(T(?P<hour>\d{2})(:(?P<min>\d{2})(:(?P<sec>\d{2})([.,](?P<fracsec>\d{1,7}))?)?)?' +
                       '(Z|(?P<offsign>[+-])(?P<offhour>\d{2})(:?(?P<offmin>\d{2}))?))?\s*$')

# Static helper function to parse ISO 8601 date/time
def parseISO8601Datetime(s):

    # Match ISO 8601?
    m = _reISO8601.search(s)
    if not m:
        raise ValueError('Expected ISO 8601 date/time')

    # Extract ISO 8601 components
    year = int(m.group('year'))
    month = int(m.group('month'))
    day = int(m.group('day'))
    hour = int(m.group('hour'))
    minute = int(m.group('min')) if m.group('min') else 0
    sec = int(m.group('sec')) if m.group('sec') else 0
    microsec = int(float('.' + m.group('fracsec')) * 1000000) if m.group('fracsec') else 0
    offhour = int(m.group('offsign') + m.group('offhour')) if m.group('offhour') else 0
    offmin = int(m.group('offsign') + m.group('offmin')) if m.group('offmin') else 0

    return (datetime(year, month, day, hour, minute, sec, microsec, tzutc) -
            timedelta(hours = offhour, minutes = offmin))
