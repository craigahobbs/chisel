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

from .compat import basestring_, iteritems, long_

from datetime import date, datetime, timedelta, tzinfo
from time import altzone as time_altzone, daylight as time_daylight, localtime as time_localtime, \
    mktime as time_mktime, timezone as time_timezone, tzname as time_tzname
import re
from uuid import UUID


# JSON encoding for date objects
class JsonDate(float):
    __slots__ = ('value', 'json')

    def __new__(cls, dummy_value):
        return float.__new__(cls, 0)

    # pylint: disable=super-init-not-called
    def __init__(self, value):
        if value is not self:
            self.value = value
            self.json = '"' + value.isoformat() + '"'

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json

    def __float__(self):
        return self


# JSON encoding for datetime objects
class JsonDatetime(float):
    __slots__ = ('value', 'json')

    def __new__(cls, dummy_value):
        return float.__new__(cls, 0)

    # pylint: disable=super-init-not-called
    def __init__(self, value):
        if value is not self:
            if value.tzinfo is None:
                value = value.replace(tzinfo=tzlocal)
            self.value = value
            self.json = '"' + value.isoformat() + '"'

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json

    def __float__(self):
        return self


# Floating point number with precision for JSON encoding
class JsonFloat(float):
    __slots__ = ('json',)

    def __new__(cls, value, dummy_prec=6):
        return float.__new__(cls, value)

    # pylint: disable=super-init-not-called
    def __init__(self, value, prec=6):
        if value is not self:
            self.json = format(value, '.' + str(prec) + 'f').rstrip('0').rstrip('.')

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json

    def __float__(self):
        return self


# JSON encoding for UUID objects
class JsonUUID(float):
    __slots__ = ('value', 'json')

    def __new__(cls, dummy_value):
        return float.__new__(cls, 0)

    # pylint: disable=super-init-not-called
    def __init__(self, value):
        if value is not self:
            self.value = value
            self.json = '"' + str(value) + '"'

    def __repr__(self):
        return self.json

    def __str__(self):
        return self.json

    def __float__(self):
        return self


# Fake JSON float types
FAKE_FLOAT_TYPES = (JsonDate, JsonDatetime, JsonUUID)


# Validation mode
VALIDATE_DEFAULT = 0
VALIDATE_QUERY_STRING = 1
VALIDATE_JSON_INPUT = 2
VALIDATE_JSON_OUTPUT = 3

# Immutable validation modes
IMMUTABLE_VALIDATION_MODES = (VALIDATE_DEFAULT, VALIDATE_JSON_OUTPUT)


# Type attribute exception
class AttributeValidationError(Exception):
    __slots__ = ('attr',)

    def __init__(self, attr):
        Exception.__init__(self, "Invalid attribute '" + attr + "'")
        self.attr = attr


# Type validation exception
class ValidationError(Exception):
    __slots__ = ('member',)

    def __init__(self, msg, member=None):
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
            return ''.join((('.' + x) if isinstance(x, basestring_) else ('[' + repr(x) + ']'))
                           for x in cls._flattenMembers(members)).lstrip('.')
        return None

    @classmethod
    def memberError(cls, type_, value, members, constraintSyntax=None):
        memberSyntax = cls.memberSyntax(members)
        msg = 'Invalid value ' + repr(value) + " (type '" + value.__class__.__name__ + "')" + \
              ((" for member '" + memberSyntax + "'") if memberSyntax else '') + \
              ((", expected type '" + type_.typeName + "'") if type_ else '') + \
              ((' [' + constraintSyntax + ']') if constraintSyntax else '')
        return ValidationError(msg, member=memberSyntax)


# Struct member attributes
class StructMemberAttributes(object):
    __slots__ = ('eq', 'lt', 'lte', 'gt', 'gte',
                 'len_eq', 'len_lt', 'len_lte', 'len_gt', 'len_gte')

    def __init__(self, eq=None, lt=None, lte=None, gt=None, gte=None,
                 len_eq=None, len_lt=None, len_lte=None, len_gt=None, len_gte=None):

        self.eq = eq
        self.lt = lt
        self.lte = lte
        self.gt = gt
        self.gte = gte
        self.len_eq = len_eq
        self.len_lt = len_lt
        self.len_lte = len_lte
        self.len_gt = len_gt
        self.len_gte = len_gte

    def validate(self, value, _member=()):
        if self.lt is not None and not value < self.lt:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='< ' + repr(JsonFloat(self.lt, 6)))
        if self.lte is not None and not value <= self.lte:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='<= ' + repr(JsonFloat(self.lte, 6)))
        if self.gt is not None and not value > self.gt:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='> ' + repr(JsonFloat(self.gt, 6)))
        if self.gte is not None and not value >= self.gte:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='>= ' + repr(JsonFloat(self.gte, 6)))
        if self.eq is not None and not value == self.eq:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='== ' + repr(JsonFloat(self.eq, 6)))
        if self.len_lt is not None and not len(value) < self.len_lt:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='len < ' + repr(JsonFloat(self.len_lt, 6)))
        if self.len_lte is not None and not len(value) <= self.len_lte:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='len <= ' + repr(JsonFloat(self.len_lte, 6)))
        if self.len_gt is not None and not len(value) > self.len_gt:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='len > ' + repr(JsonFloat(self.len_gt, 6)))
        if self.len_gte is not None and not len(value) >= self.len_gte:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='len >= ' + repr(JsonFloat(self.len_gte, 6)))
        if self.len_eq is not None and not len(value) == self.len_eq:
            raise ValidationError.memberError(None, value, _member, constraintSyntax='len == ' + repr(JsonFloat(self.len_eq, 6)))

    def validateAttr(self, allowValue=False, allowLength=False):
        if not allowValue:
            if self.lt is not None:
                raise AttributeValidationError('< ' + repr(JsonFloat(self.lt, 6)))
            if self.lte is not None:
                raise AttributeValidationError('<= ' + repr(JsonFloat(self.lte, 6)))
            if self.gt is not None:
                raise AttributeValidationError('> ' + repr(JsonFloat(self.gt, 6)))
            if self.gte is not None:
                raise AttributeValidationError('>= ' + repr(JsonFloat(self.gte, 6)))
            if self.eq is not None:
                raise AttributeValidationError('== ' + repr(JsonFloat(self.eq, 6)))
        if not allowLength:
            if self.len_lt is not None:
                raise AttributeValidationError('len < ' + repr(JsonFloat(self.len_lt, 6)))
            if self.len_lte is not None:
                raise AttributeValidationError('len <= ' + repr(JsonFloat(self.len_lte, 6)))
            if self.len_gt is not None:
                raise AttributeValidationError('len > ' + repr(JsonFloat(self.len_gt, 6)))
            if self.len_gte is not None:
                raise AttributeValidationError('len >= ' + repr(JsonFloat(self.len_gte, 6)))
            if self.len_eq is not None:
                raise AttributeValidationError('len == ' + repr(JsonFloat(self.len_eq, 6)))


# Typedef type (type plus attributes)
class Typedef(object):
    __slots__ = ('typeName', 'type', 'attr', 'doc')

    def __init__(self, type_, attr=None, typeName=None, doc=None):
        self.typeName = 'typedef' if typeName is None else typeName
        self.type = type_
        self.attr = attr
        self.doc = [] if doc is None else doc

    @staticmethod
    def baseType(type_):
        while isinstance(type_, Typedef):
            type_ = type_.type
        return type_

    def validateAttr(self, attr):
        self.type.validateAttr(attr)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):
        result = self.type.validate(value, mode, _member)
        if self.attr is not None:
            self.attr.validate(result, _member)
        return result


# Struct member
class StructMember(object):
    __slots__ = ('name', 'type', 'isOptional', 'attr', 'doc')

    def __init__(self, name, type_, isOptional=False, attr=None, doc=None):
        self.name = name
        self.type = type_
        self.isOptional = isOptional
        self.attr = attr
        self.doc = [] if doc is None else doc


# Struct type
class TypeStruct(object):
    __slots__ = ('typeName', 'isUnion', 'members', '_membersDict', 'doc')

    def __init__(self, typeName=None, isUnion=False, doc=None):
        self.typeName = ('union' if isUnion else 'struct') if typeName is None else typeName
        self.isUnion = isUnion
        self.members = []
        self._membersDict = {}
        self.doc = [] if doc is None else doc

    def addMember(self, name, type_, isOptional=False, attr=None, doc=None):
        member = StructMember(name, type_, isOptional or self.isUnion, attr, doc)
        self.members.append(member)
        self._membersDict[name] = member
        return member

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

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
        membersDict = self._membersDict
        for memberName, memberValue in iteritems(valueX):
            memberPath = (_member, memberName)
            member = membersDict.get(memberName)
            if member is None:
                raise ValidationError("Unknown member '" + ValidationError.memberSyntax((_member, memberName)) + "'")
            memberValueX = membersDict[memberName].type.validate(memberValue, mode, memberPath)
            if member.attr is not None:
                member.attr.validate(memberValueX, memberPath)
            if valueCopy is not None:
                valueCopy[memberName] = memberValueX

        # Any missing required members?
        if len(self.members) != len(valueX):
            for member in self.members:
                if not self.isUnion and not member.isOptional and member.name not in valueX:
                    raise ValidationError("Required member '" + ValidationError.memberSyntax((_member, member.name)) + "' missing")

        return value if valueCopy is None else valueCopy


# Array type
class TypeArray(object):
    __slots__ = ('type', 'attr')

    typeName = 'array'

    def __init__(self, type_, attr=None):
        self.type = type_
        self.attr = attr

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr(allowLength=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, list) or isinstance(value, tuple):
            valueX = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            valueX = []
        else:
            raise ValidationError.memberError(self, value, _member)

        # Result a copy?
        valueCopy = None if mode in IMMUTABLE_VALIDATION_MODES else []

        # Validate the list contents
        ixArrayValue = 0
        for arrayValue in valueX:
            memberPath = (_member, ixArrayValue)
            arrayValueX = self.type.validate(arrayValue, mode, memberPath)
            if self.attr is not None:
                self.attr.validate(arrayValueX, memberPath)
            if valueCopy is not None:
                valueCopy.append(arrayValueX)
            ixArrayValue += 1

        return value if valueCopy is None else valueCopy


# Dict type
class TypeDict(object):
    __slots__ = ('type', 'attr', 'keyType', 'keyAttr')

    typeName = 'dict'

    def __init__(self, type_, attr=None, keyType=None, keyAttr=None):
        self.type = type_
        self.attr = attr
        self.keyType = keyType or TypeString()
        self.keyAttr = keyAttr

    @classmethod
    def validKeyType(cls, keyType):
        keyTypeBase = Typedef.baseType(keyType)
        return isinstance(keyTypeBase, _TypeString) or isinstance(keyTypeBase, TypeEnum)

    def hasDefaultKeyType(self):
        return isinstance(self.keyType, _TypeString)

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr(allowLength=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, dict):
            valueX = value
        elif mode == VALIDATE_QUERY_STRING and value == '':
            valueX = {}
        else:
            raise ValidationError.memberError(self, value, _member)

        # Result a copy?
        valueCopy = None if mode in IMMUTABLE_VALIDATION_MODES else {}

        # Validate the dict key/value pairs
        for dictKey, dictValue in iteritems(valueX):
            memberPath = (_member, dictKey)

            # Validate the key
            dictKeyX = self.keyType.validate(dictKey, mode, memberPath)
            if self.keyAttr is not None:
                self.keyAttr.validate(dictKeyX, memberPath)

            # Validate the value
            dictValueX = self.type.validate(dictValue, mode, memberPath)
            if self.attr is not None:
                self.attr.validate(dictValueX, memberPath)

            # Result a copy?
            if valueCopy is not None:
                valueCopy[dictKeyX] = dictValueX

        return value if valueCopy is None else valueCopy


# Enumeration type
class EnumValue(object):
    __slots__ = ('value', 'doc')

    def __init__(self, valueString, doc=None):
        self.value = valueString
        self.doc = [] if doc is None else doc

    def __eq__(self, other):
        return self.value == other


class TypeEnum(object):
    __slots__ = ('typeName', 'values', 'doc')

    def __init__(self, typeName='enum', doc=None):
        self.typeName = typeName
        self.values = []
        self.doc = [] if doc is None else doc

    def addValue(self, valueString, doc=None):
        value = EnumValue(valueString, doc)
        self.values.append(value)
        return value

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr()

    def validate(self, value, dummy_mode=VALIDATE_DEFAULT, _member=()):

        # Validate the value
        if value not in self.values:
            raise ValidationError.memberError(self, value, _member)

        return value


# String type
class _TypeString(object):
    __slots__ = ()

    typeName = 'string'

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr(allowLength=True)

    def validate(self, value, dummy_mode=VALIDATE_DEFAULT, _member=()):

        # Validate the value
        if not isinstance(value, basestring_):
            raise ValidationError.memberError(self, value, _member)

        return value


def TypeString():
    return _TYPE_STRING

_TYPE_STRING = _TypeString()


# Int type
class _TypeInt(object):
    __slots__ = ()

    typeName = 'int'

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr(allowValue=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

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

        return value if mode in IMMUTABLE_VALIDATION_MODES else valueX


def TypeInt():
    return _TYPE_INT

_TYPE_INT = _TypeInt()


# Float type
class _TypeFloat(object):
    __slots__ = ()

    typeName = 'float'

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr(allowValue=True)

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

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

        return value if mode in IMMUTABLE_VALIDATION_MODES else valueX


def TypeFloat():
    return _TYPE_FLOAT

_TYPE_FLOAT = _TypeFloat()


# Bool type
class _TypeBool(object):
    __slots__ = ()

    typeName = 'bool'

    VALUES = {
        'true': True,
        'false': False
    }

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

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


def TypeBool():
    return _TYPE_BOOL

_TYPE_BOOL = _TypeBool()


# Uuid type
class _TypeUuid(object):
    __slots__ = ()

    typeName = 'uuid'

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, UUID):
            if mode == VALIDATE_JSON_OUTPUT:
                raise ValidationError.memberError(self, value, _member, constraintSyntax='JsonUUID object required')
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


def TypeUuid():
    return _TYPE_UUID

_TYPE_UUID = _TypeUuid()


# Date type
class _TypeDate(object):
    __slots__ = ()

    typeName = 'date'

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, date):
            if mode == VALIDATE_JSON_OUTPUT:
                raise ValidationError.memberError(self, value, _member, constraintSyntax='JsonDate object required')
            return value
        elif mode == VALIDATE_JSON_OUTPUT and isinstance(value, JsonDate):
            return value
        elif mode not in IMMUTABLE_VALIDATION_MODES and isinstance(value, basestring_):
            try:
                return parseISO8601Date(value)
            except:
                raise ValidationError.memberError(self, value, _member)
        else:
            raise ValidationError.memberError(self, value, _member)


def TypeDate():
    return _TYPE_DATE

_TYPE_DATE = _TypeDate()


# Datetime type
class _TypeDatetime(object):
    __slots__ = ()

    typeName = 'datetime'

    @staticmethod
    def validateAttr(attr):
        attr.validateAttr()

    def validate(self, value, mode=VALIDATE_DEFAULT, _member=()):

        # Validate and translate the value
        if isinstance(value, datetime):
            if mode == VALIDATE_JSON_OUTPUT:
                raise ValidationError.memberError(self, value, _member, constraintSyntax='JsonDatetime object required')

            # Set a time zone, if necessary
            if mode not in IMMUTABLE_VALIDATION_MODES and value.tzinfo is None:
                return value.replace(tzinfo=tzlocal)

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


def TypeDatetime():
    return _TYPE_DATETIME

_TYPE_DATETIME = _TypeDatetime()


# GMT tzinfo class for parseISO8601Datetime (from Python docs)
class _TZUTC(tzinfo):  # pragma: no cover
    __slots__ = ()

    def utcoffset(self, dt):
        return _timedelta_zero

    def dst(self, dt):
        return _timedelta_zero

    def tzname(self, dt):
        return 'UTC'


# Local time zone tzinfo class (from Python docs)
class _TZLocal(tzinfo):  # pragma: no cover
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
        return time_tzname[self._isdst(dt)]

    @classmethod
    def _stdOffset(cls):
        return timedelta(seconds=-time_timezone)

    @classmethod
    def _dstOffset(cls):
        if time_daylight:
            return timedelta(seconds=-time_altzone)
        else:
            return cls._stdOffset()

    @classmethod
    def _isdst(cls, dt):
        tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, 0)
        stamp = time_mktime(tt)
        tt = time_localtime(stamp)
        return tt.tm_isdst > 0


_timedelta_zero = timedelta(0)
tzutc = _TZUTC()
tzlocal = _TZLocal()


# ISO 8601 regexes
_reISO8601Date = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s*$')
_reISO8601Datetime = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
                                r'(T(?P<hour>\d{2})(:(?P<min>\d{2})(:(?P<sec>\d{2})([.,](?P<fracsec>\d{1,7}))?)?)?'
                                r'(Z|(?P<offsign>[+-])(?P<offhour>\d{2})(:?(?P<offmin>\d{2}))?))?\s*$')


# Static helper function to parse ISO 8601 date
def parseISO8601Date(s):

    # Match ISO 8601?
    m = _reISO8601Date.search(s)
    if not m:
        raise ValueError('Expected ISO 8601 date')

    # Extract ISO 8601 components
    year = int(m.group('year'))
    month = int(m.group('month'))
    day = int(m.group('day'))

    return date(year, month, day)


# Static helper function to parse ISO 8601 date/time
def parseISO8601Datetime(s):

    # Match ISO 8601?
    m = _reISO8601Datetime.search(s)
    if not m:
        raise ValueError('Expected ISO 8601 date/time')

    # Extract ISO 8601 components
    year = int(m.group('year'))
    month = int(m.group('month'))
    day = int(m.group('day'))
    hour = int(m.group('hour')) if m.group('hour') else 0
    minute = int(m.group('min')) if m.group('min') else 0
    sec = int(m.group('sec')) if m.group('sec') else 0
    microsec = int(float('.' + m.group('fracsec')) * 1000000) if m.group('fracsec') else 0
    offhour = int(m.group('offsign') + m.group('offhour')) if m.group('offhour') else 0
    offmin = int(m.group('offsign') + m.group('offmin')) if m.group('offmin') else 0

    return (datetime(year, month, day, hour, minute, sec, microsec, tzutc) -
            timedelta(hours=offhour, minutes=offmin))
