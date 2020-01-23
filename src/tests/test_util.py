# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from chisel.util import JSONEncoder, parse_iso8601_date, parse_iso8601_datetime

from . import TestCase


class TestJSONEncoder(TestCase):

    def test_types(self):
        encoder = JSONEncoder(indent=2, sort_keys=True, separators=(',', ': '))
        content = encoder.encode({
            'date': date(2016, 7, 1),
            'datetime': datetime(2016, 7, 1, 7, 56, tzinfo=timezone.utc),
            'decimal': Decimal('7.57'),
            'uuid': UUID('127FF2EB-3E1E-42A6-AB8A-F03B6EEB33E7')
        })
        self.assertEqual(content, '''\
{
  "date": "2016-07-01",
  "datetime": "2016-07-01T07:56:00+00:00",
  "decimal": 7.57,
  "uuid": "127ff2eb-3e1e-42a6-ab8a-f03b6eeb33e7"
}''')

    def test_types_no_tz(self):
        encoder = JSONEncoder(indent=2, sort_keys=True, separators=(',', ': '))
        content = encoder.encode({
            'date': date(2016, 7, 1),
            'datetime': datetime(2016, 7, 1, 7, 56),
            'decimal': Decimal('7.57'),
            'uuid': UUID('127FF2EB-3E1E-42A6-AB8A-F03B6EEB33E7')
        })
        self.assertEqual(content, '''\
{
  "date": "2016-07-01",
  "datetime": "2016-07-01T07:56:00+00:00",
  "decimal": 7.57,
  "uuid": "127ff2eb-3e1e-42a6-ab8a-f03b6eeb33e7"
}''')

    def test_types_unknown(self):
        class MyType:
            pass
        encoder = JSONEncoder(indent=2, sort_keys=True, separators=(',', ': '))
        with self.assertRaises(TypeError):
            encoder.encode({'my_type': MyType()})


class TestISO8601(TestCase):

    def test_parse_iso8601_date(self):
        self.assertEqual(parse_iso8601_date('2020-01-22'), date(2020, 1, 22))

    def test_parse_iso8601_date_invalid(self):
        with self.assertRaises(ValueError) as cm_exc:
            parse_iso8601_date('asdf')
        self.assertEqual(str(cm_exc.exception), 'Expected ISO 8601 date')

    def test_parse_iso8601_datetime(self):
        self.assertEqual(parse_iso8601_datetime('2020-01-22T09:37:00-07:00'), datetime(2020, 1, 22, 16, 37, tzinfo=timezone.utc))

    def test_parse_iso8601_datetime_zulu(self):
        self.assertEqual(parse_iso8601_datetime('2020-01-22T09:37:00Z'), datetime(2020, 1, 22, 9, 37, tzinfo=timezone.utc))

    def test_parse_iso8601_datetime_invalid(self):
        with self.assertRaises(ValueError) as cm_exc:
            parse_iso8601_datetime('asdf')
        self.assertEqual(str(cm_exc.exception), 'Expected ISO 8601 date/time')
