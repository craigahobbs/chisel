# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from chisel.util import JSONEncoder

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
{{
  "date": "2016-07-01",
  "datetime": "{0}",
  "decimal": 7.57,
  "uuid": "127ff2eb-3e1e-42a6-ab8a-f03b6eeb33e7"
}}'''.format(datetime(2016, 7, 1, 7, 56, tzinfo=timezone.utc).isoformat()))
