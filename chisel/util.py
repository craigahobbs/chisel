#
# Copyright (C) 2012-2016 Craig Hobbs
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

from datetime import date, datetime, timedelta, tzinfo
from decimal import Decimal
from itertools import islice
from json import JSONEncoder as json_JSONEncoder
import os
import re
import sys
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


def load_modules(module_path, module_ext='.py', exclude_submodules=None):
    """
    Recursively load Python modules
    """

    # Does the path exist?
    if not os.path.isdir(module_path):
        raise IOError('{0!r} not found or is not a directory'.format(module_path))

    # Where is this module on the system path?
    module_dir_parts = module_path.split(os.sep)

    def find_module_name_index():
        for sys_path in sys.path:
            for ix_module_part in range(len(module_dir_parts) - 1, 0, -1):
                module_name_parts = module_dir_parts[ix_module_part:]
                if not any(not part.isidentifier() for part in module_name_parts):
                    sys_module_path = os.path.join(sys_path, *module_name_parts)
                    if os.path.isdir(sys_module_path) and os.path.samefile(module_path, sys_module_path):
                        # Make sure the module package is import-able
                        module_name = '.'.join(module_name_parts)
                        try:
                            __import__(module_name)
                        except ImportError:
                            pass
                        else:
                            return len(module_dir_parts) - len(module_name_parts)
        raise ImportError('{0!r} not found on system path'.format(module_path))
    ix_module_name = find_module_name_index()

    # Recursively find module files
    exclude_submodules_dot = None if exclude_submodules is None else [x + '.' for x in exclude_submodules]
    for dirpath, dummy_dirnames, filenames in os.walk(module_path):

        # Skip Python 3.x cache directories
        if os.path.basename(dirpath) == '__pycache__':
            continue

        # Is the sub-package excluded?
        subpackage_parts = dirpath.split(os.sep)
        subpackage_name = '.'.join(islice(subpackage_parts, ix_module_name, None))
        if exclude_submodules is not None and \
           (subpackage_name in exclude_submodules or any(subpackage_name.startswith(x) for x in exclude_submodules_dot)):
            continue

        # Load each sub-module file in the directory
        for filename in filenames:

            # Skip non-module files
            (basename, ext) = os.path.splitext(filename)
            if ext != module_ext:
                continue

            # Skip package __init__ files
            if basename == '__init__':
                continue

            # Is the sub-module excluded?
            submodule_name = subpackage_name + '.' + basename
            if exclude_submodules is not None and \
               (submodule_name in exclude_submodules or any(submodule_name.startswith(x) for x in exclude_submodules)):
                continue

            # Load the sub-module
            yield __import__(submodule_name, globals(), locals(), ['.'])
