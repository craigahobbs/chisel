# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import re
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    """
    JSON encoder class with support for encoding date, datetime, Decimal, and UUID.
    """

    def default(self, o): # pylint: disable=method-hidden
        if isinstance(o, datetime):
            return (o if o.tzinfo else o.replace(tzinfo=timezone.utc)).isoformat()
        elif isinstance(o, date):
            return o.isoformat()
        elif isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


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

    return datetime(year, month, day, hour, minute, sec, microsec, timezone.utc) - timedelta(hours=offhour, minutes=offmin)
