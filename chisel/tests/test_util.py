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

from datetime import date, datetime
from decimal import Decimal
import unittest
from uuid import UUID

from chisel.util import JSONEncoder, TZLOCAL, TZUTC


class TestJSONEncoder(unittest.TestCase):

    def test_types(self):
        encoder = JSONEncoder(indent=2, sort_keys=True, separators=(',', ': '))
        content = encoder.encode({
            'date': date(2016, 7, 1),
            'datetime': datetime(2016, 7, 1, 7, 56, tzinfo=TZUTC),
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
}}'''.format(datetime(2016, 7, 1, 7, 56, tzinfo=TZLOCAL).isoformat()))
