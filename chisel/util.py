# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import date, datetime, timedelta, tzinfo
from decimal import Decimal
import importlib
from json import JSONEncoder as json_JSONEncoder
import pkgutil
import re
from time import altzone as time_altzone, daylight as time_daylight, localtime as time_localtime, \
    mktime as time_mktime, timezone as time_timezone, tzname as time_tzname
from uuid import UUID


class JSONEncoder(json_JSONEncoder):
    """
    JSON encoder class with support for encoding date, datetime, Decimal, and UUID.
    """

    def default(self, obj): # pylint: disable=method-hidden
        if isinstance(obj, datetime):
            return (obj if obj.tzinfo else obj.replace(tzinfo=TZLOCAL)).isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        return json_JSONEncoder.default(self, obj)


class _TZUTC(tzinfo):
    """
    GMT tzinfo class (from Python docs)
    """

    __slots__ = ()

    def utcoffset(self, dt):
        return TIMEDELTA_ZERO

    def dst(self, dt):
        return TIMEDELTA_ZERO

    def tzname(self, dt):
        return 'UTC'


class _TZLocal(tzinfo):
    """
    Local time zone tzinfo class (from Python docs)
    """

    __slots__ = ()

    def utcoffset(self, dt):
        if self._isdst(dt):
            return self._dst_offset()
        else:
            return self._std_offset()

    def dst(self, dt):
        if self._isdst(dt):
            return self._dst_offset() - self._std_offset()
        else:
            return TIMEDELTA_ZERO

    def tzname(self, dt):
        return time_tzname[self._isdst(dt)]

    @classmethod
    def _std_offset(cls):
        return timedelta(seconds=-time_timezone)

    @classmethod
    def _dst_offset(cls):
        if time_daylight:
            return timedelta(seconds=-time_altzone)
        else:
            return cls._std_offset()

    @classmethod
    def _isdst(cls, dt_):
        tt_ = (dt_.year, dt_.month, dt_.day, dt_.hour, dt_.minute, dt_.second, dt_.weekday(), 0, 0)
        stamp = time_mktime(tt_)
        tt_ = time_localtime(stamp)
        return tt_.tm_isdst > 0


# Datetime constants
TIMEDELTA_ZERO = timedelta(0)


# Time zone constants
TZUTC = _TZUTC()
TZLOCAL = _TZLocal()


# ISO 8601 regexes
_RE_ISO8601_DATE = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s*$')
_RE_ISO8601_DATETIME = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
                                  r'(T(?P<hour>\d{2})(:(?P<min>\d{2})(:(?P<sec>\d{2})([.,](?P<fracsec>\d{1,7}))?)?)?'
                                  r'(Z|(?P<offsign>[+-])(?P<offhour>\d{2})(:?(?P<offmin>\d{2}))?))?\s*$')


def parse_iso8601_date(string):
    """
    Parse an ISO 8601 date string
    """

    # Match ISO 8601?
    match = _RE_ISO8601_DATE.search(string)
    if not match:
        raise ValueError('Expected ISO 8601 date')

    # Extract ISO 8601 components
    year = int(match.group('year'))
    month = int(match.group('month'))
    day = int(match.group('day'))

    return date(year, month, day)


def parse_iso8601_datetime(string):
    """
    Parse an ISO 8601 date/time string
    """

    # Match ISO 8601?
    match = _RE_ISO8601_DATETIME.search(string)
    if not match:
        raise ValueError('Expected ISO 8601 date/time')

    # Extract ISO 8601 components
    year = int(match.group('year'))
    month = int(match.group('month'))
    day = int(match.group('day'))
    hour = int(match.group('hour')) if match.group('hour') else 0
    minute = int(match.group('min')) if match.group('min') else 0
    sec = int(match.group('sec')) if match.group('sec') else 0
    microsec = int(float('.' + match.group('fracsec')) * 1000000) if match.group('fracsec') else 0
    offhour = int(match.group('offsign') + match.group('offhour')) if match.group('offhour') else 0
    offmin = int(match.group('offsign') + match.group('offmin')) if match.group('offmin') else 0

    return (datetime(year, month, day, hour, minute, sec, microsec, TZUTC) -
            timedelta(hours=offhour, minutes=offmin))


def import_submodules(package, parent_package=None, exclude_submodules=None):
    """
    Generator which imports all submodules of a module, recursively, including subpackages

    :param package: package name (e.g 'chisel.util'); may be relative if parent_package is provided
    :type package: str
    :param parent_package: parent package name (e.g 'chisel')
    :type package: str
    :rtype: iterator of modules
    """

    exclude_submodules_dot = [x + '.' for x in exclude_submodules] if exclude_submodules else exclude_submodules
    package = importlib.import_module(package, parent_package)
    for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        if exclude_submodules and (name in exclude_submodules or any(name.startswith(x) for x in exclude_submodules_dot)):
            continue
        yield importlib.import_module(name)
