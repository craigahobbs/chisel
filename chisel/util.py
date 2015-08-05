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

from .compat import string_isidentifier, xrange_

from datetime import date, datetime, timedelta, tzinfo
from time import altzone as time_altzone, daylight as time_daylight, localtime as time_localtime, \
    mktime as time_mktime, timezone as time_timezone, tzname as time_tzname
import itertools
import os
import re
import sys


class TZUTC(tzinfo):
    """
    GMT tzinfo class (from Python docs)
    """

    __slots__ = ()

    def utcoffset(self, dt):
        return timedelta_zero

    def dst(self, dt):
        return timedelta_zero

    def tzname(self, dt):
        return 'UTC'


class TZLocal(tzinfo):
    """
    Local time zone tzinfo class (from Python docs)
    """

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
            return timedelta_zero

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


# Datetime constants
timedelta_zero = timedelta(0)


# Time zone constants
tzutc = TZUTC()
tzlocal = TZLocal()


# ISO 8601 regexes
_RE_ISO8601_DATE = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s*$')
_RE_ISO8601_DATETIME = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
                                  r'(T(?P<hour>\d{2})(:(?P<min>\d{2})(:(?P<sec>\d{2})([.,](?P<fracsec>\d{1,7}))?)?)?'
                                  r'(Z|(?P<offsign>[+-])(?P<offhour>\d{2})(:?(?P<offmin>\d{2}))?))?\s*$')


def parse_iso8601_date(s):
    """
    Parse an ISO 8601 date string
    """

    # Match ISO 8601?
    m = _RE_ISO8601_DATE.search(s)
    if not m:
        raise ValueError('Expected ISO 8601 date')

    # Extract ISO 8601 components
    year = int(m.group('year'))
    month = int(m.group('month'))
    day = int(m.group('day'))

    return date(year, month, day)


def parse_iso8601_datetime(s):
    """
    Parse an ISO 8601 date/time string
    """

    # Match ISO 8601?
    m = _RE_ISO8601_DATETIME.search(s)
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


def load_modules(moduleDir, moduleExt='.py', excludedSubmodules=None):
    """
    Recursively load Python modules
    """

    # Does the path exist?
    if not os.path.isdir(moduleDir):
        raise IOError('%r not found or is not a directory' % (moduleDir,))

    # Where is this module on the system path?
    moduleDirParts = moduleDir.split(os.sep)

    def findModuleNameIndex():
        for sysPath in sys.path:
            for iModulePart in xrange_(len(moduleDirParts) - 1, 0, -1):
                moduleNameParts = moduleDirParts[iModulePart:]
                if not any(not string_isidentifier(part) for part in moduleNameParts):
                    sysModulePath = os.path.join(sysPath, *moduleNameParts)
                    if os.path.isdir(sysModulePath) and os.path.samefile(moduleDir, sysModulePath):
                        # Make sure the module package is import-able
                        moduleName = '.'.join(moduleNameParts)
                        try:
                            __import__(moduleName)
                        except ImportError:
                            pass
                        else:
                            return len(moduleDirParts) - len(moduleNameParts)
        raise ImportError('%r not found on system path' % (moduleDir,))
    ixModuleName = findModuleNameIndex()

    # Recursively find module files
    excludedSubmodulesDot = None if excludedSubmodules is None else [x + '.' for x in excludedSubmodules]
    for dirpath, dummy_dirnames, filenames in os.walk(moduleDir):

        # Skip Python 3.x cache directories
        if os.path.basename(dirpath) == '__pycache__':
            continue

        # Is the sub-package excluded?
        subpkgParts = dirpath.split(os.sep)
        subpkgName = '.'.join(itertools.islice(subpkgParts, ixModuleName, None))
        if excludedSubmodules is not None and \
           (subpkgName in excludedSubmodules or any(subpkgName.startswith(x) for x in excludedSubmodulesDot)):
            continue

        # Load each sub-module file in the directory
        for filename in filenames:

            # Skip non-module files
            (basename, ext) = os.path.splitext(filename)
            if ext != moduleExt:
                continue

            # Skip package __init__ files
            if basename == '__init__':
                continue

            # Is the sub-module excluded?
            submoduleName = subpkgName + '.' + basename
            if excludedSubmodules is not None and \
               (submoduleName in excludedSubmodules or any(submoduleName.startswith(x) for x in excludedSubmodules)):
                continue

            # Load the sub-module
            yield __import__(submoduleName, globals(), locals(), ['.'])
