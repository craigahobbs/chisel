# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

from datetime import date, datetime, timezone
from decimal import Decimal
from urllib.parse import quote
from uuid import UUID

from chisel import decode_query_string, encode_query_string, JSONEncoder, parse_iso8601_date, parse_iso8601_datetime
from chisel.util import encode_query_string_items, decode_query_string_items

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


class TestUrl(TestCase):

    def test_decode_query_string(self):

        # Complex dict
        query_string = '_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6'
        obj = {'a': '7', '_a': '7', 'b': {'c': '+x y + z', 'd': ['2', '-4', '6']}}
        self.assertEqual(decode_query_string(query_string), obj)

        # Array of dicts
        query_string = 'foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear'
        obj = {'foo': [{'bar': '17', 'thud': 'blue'}, {'boo': 'bear'}]}
        self.assertEqual(decode_query_string(query_string), obj)

        # Top-level array
        query_string = '0=1&1=2&2=3'
        obj = ['1', '2', '3']
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty query string
        query_string = ''
        obj = {}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string value
        query_string = 'b='
        obj = {'b': ''}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string value at end
        query_string = 'a=7&b='
        obj = {'a': '7', 'b': ''}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string value at start
        query_string = 'b=&a=7'
        obj = {'a': '7', 'b': ''}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string value in middle
        query_string = 'a=7&b=&c=9'
        obj = {'a': '7', 'b': '', 'c': '9'}
        self.assertEqual(decode_query_string(query_string), obj)

        # Decode keys and values
        query_string = 'a%2eb.c=7%20+%207%20%3d%2014'
        obj = {'a.b': {'c': '7 + 7 = 14'}}
        self.assertEqual(decode_query_string(query_string), obj)

        # Decode unicode string
        query_string = 'a=abc%EA%80%80&b.0=c&b.1=d'
        obj = {'a': 'abc' + chr(40960), 'b': ['c', 'd']}
        self.assertEqual(decode_query_string(query_string), obj)

        # Keys and values with special characters
        query_string = 'a%26b%3Dc%2ed=a%26b%3Dc.d'
        obj = {'a&b=c.d': 'a&b=c.d'}
        self.assertEqual(decode_query_string(query_string), obj)

        # Non-initial-zero array-looking index
        query_string = 'a.1=0'
        obj = {'a': {'1': '0'}}
        self.assertEqual(decode_query_string(query_string), obj)

        # Dictionary first, then array-looking zero index
        query_string = 'a.b=0&a.0=0'
        obj = {'a': {'b': '0', '0': '0'}}
        self.assertEqual(decode_query_string(query_string), obj)

    def test_decode_query_string_degenerate(self):

        def assert_decode_error(query_string, err):
            with self.assertRaises(ValueError) as cm_exc:
                decode_query_string(query_string)
            self.assertEqual(str(cm_exc.exception), err)

        # Key with no equal
        query_string = 'a=7&b'
        assert_decode_error(query_string, "Invalid key/value pair 'b'")

        # Key with no equal - long key/value
        query_string = 'a=7&' + 'b' * 2000
        assert_decode_error(query_string, "Invalid key/value pair '" + 'b' * 999)

        # Empty string key
        query_string = 'a=7&=b'
        obj = {'a': '7', '': 'b'}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string key and value
        query_string = 'a=7&='
        obj = {'a': '7', '': ''}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string key and value with space
        query_string = 'a=7& = '
        obj = {'a': '7', ' ': ' '}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string key with no equal
        query_string = 'a=7&'
        obj = {'a': '7'}
        self.assertEqual(decode_query_string(query_string), obj)

        # Multiple empty string key with no equal
        query_string = 'a&b'
        assert_decode_error(query_string, "Invalid key/value pair 'a'")

        # Multiple empty string key with no equal
        query_string = 'a&b&c'
        assert_decode_error(query_string, "Invalid key/value pair 'a'")

        # Multiple empty string key/value
        query_string = '&'
        obj = {}
        self.assertEqual(decode_query_string(query_string), obj)

        # Multiple empty string key/value
        query_string = '&&'
        obj = {}
        self.assertEqual(decode_query_string(query_string), obj)

        # Empty string sub-key
        query_string = 'a.=5'
        obj = {'a': {'': '5'}}
        self.assertEqual(decode_query_string(query_string), obj)

        # Duplicate keys
        query_string = 'abc=21&ab=19&abc=17'
        assert_decode_error(query_string, "Duplicate key 'abc=17'")

        # Duplicate keys - long key/value
        query_string = 'a' * 2000 + '=21&ab=19&' + 'a' * 2000 + '=17'
        assert_decode_error(query_string, "Duplicate key '" + 'a' * 999)

        # Duplicate index
        query_string = 'a.0=0&a.1=1&a.0=2'
        assert_decode_error(query_string, "Duplicate key 'a.0=2'")

        # Index too large
        query_string = 'a.0=0&a.1=1&a.3=3'
        assert_decode_error(query_string, "Invalid key/value pair 'a.3=3'")

        # Index too large - long key/value
        query_string = 'a' * 2000 + '.0=0&' + 'a' * 2000 + '.1=1&' + 'a' * 2000 + '.3=3'
        assert_decode_error(query_string, "Invalid key/value pair '" + 'a' * 999)

        # Negative index
        query_string = 'a.0=0&a.1=1&a.-3=3'
        assert_decode_error(query_string, "Invalid key/value pair 'a.-3=3'")

        # First list, then dict
        query_string = 'a.0=0&a.b=0'
        assert_decode_error(query_string, "Invalid key/value pair 'a.b=0'")

        # First list, then dict - long key/value
        query_string = 'a' * 2000 + '.0=0&' + 'a' * 2000 + '.b=0'
        assert_decode_error(query_string, "Invalid key/value pair '" + 'a' * 999)

    def test_decode_query_string_items(self):

        query_string_items = []
        self.assertDictEqual(decode_query_string_items(query_string_items), {})

        query_string_items = [
            ('a&b=c', 'a&b=c'),
            ('bool', 'true'),
            ('date', '2017-08-02'),
            ('datetime', '2017-08-02T08:12:00+00:00'),
            ('dict.a', '1'),
            ('dict.b', '2'),
            ('float', '3.1459'),
            ('int', '19'),
            ('list.0', '1'),
            ('list.1', '2'),
            ('list.2', '3'),
            ('none', 'null'),
            ('uuid', '7da81f83-a656-42f1-aeb3-ab207809fb0e')
        ]
        self.assertDictEqual(decode_query_string_items(query_string_items), {
            'a&b=c': 'a&b=c',
            'bool': 'true',
            'date': '2017-08-02',
            'datetime': '2017-08-02T08:12:00+00:00',
            'dict': {'a': '1', 'b': '2'},
            'float': '3.1459',
            'int': '19',
            'list': ['1', '2', '3'],
            'none': 'null',
            'uuid': '7da81f83-a656-42f1-aeb3-ab207809fb0e'
        })

        query_string_items = [
            ('a%26b%3Dc', 'a%26b%3Dc'),
            ('bool', 'true'),
            ('date', '2017-08-02'),
            ('datetime', '2017-08-02T08%3A12%3A00%2B00%3A00'),
            ('dict.a', '1'),
            ('dict.b', '2'),
            ('float', '3.1459'),
            ('int', '19'),
            ('list.0', '1'),
            ('list.1', '2'),
            ('list.2', '3'),
            ('none', 'null'),
            ('uuid', '7da81f83-a656-42f1-aeb3-ab207809fb0e')
        ]
        self.assertDictEqual(decode_query_string_items(query_string_items, encoding='utf-8'), {
            'a&b=c': 'a&b=c',
            'bool': 'true',
            'date': '2017-08-02',
            'datetime': '2017-08-02T08:12:00+00:00',
            'dict': {'a': '1', 'b': '2'},
            'float': '3.1459',
            'int': '19',
            'list': ['1', '2', '3'],
            'none': 'null',
            'uuid': '7da81f83-a656-42f1-aeb3-ab207809fb0e'
        })

    def test_encode_query_string(self):

        # Complex dict
        obj = {'a': 7, '_a': '7', 'b': {'c': '+x y + z', 'd': [2, -4, 6]}}
        query_string = '_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6'
        self.assertEqual(encode_query_string(obj), query_string)

        # List of dicts
        obj = {'foo': [{'bar': '17', 'thud': 'blue'}, {'boo': 'bear'}]}
        query_string = 'foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear'
        self.assertEqual(encode_query_string(obj), query_string)

        # Top-level array
        obj = [1, 2, 3]
        query_string = '0=1&1=2&2=3'
        self.assertEqual(encode_query_string(obj), query_string)

        # Empty dict
        obj = {}
        query_string = ''
        self.assertEqual(encode_query_string(obj), query_string)

        # Empty array
        obj = []
        query_string = ''
        self.assertEqual(encode_query_string(obj), query_string)

        # Empty dict/dict
        obj = {'foo': {}}
        query_string = 'foo='
        self.assertEqual(encode_query_string(obj), query_string)

        # Empty dict/array
        obj = {'foo': []}
        query_string = 'foo='
        self.assertEqual(encode_query_string(obj), query_string)

        # Empty array/array
        obj = [[]]
        query_string = '0='
        self.assertEqual(encode_query_string(obj), query_string)

        # Empty array/dict
        obj = [{}]
        query_string = '0='
        self.assertEqual(encode_query_string(obj), query_string)

        # Keys and values with special characters
        obj = {'a&b=c.d': 'a&b=c.d'}
        query_string = 'a%26b%3Dc.d=a%26b%3Dc.d'
        self.assertEqual(encode_query_string(obj), query_string)

        # Unicode keys and values
        obj = {'a': 'abc' + chr(40960), 'b': ['c', 'd']}
        query_string = 'a=abc%EA%80%80&b.0=c&b.1=d'
        self.assertEqual(encode_query_string(obj), query_string)

    # Test bool query string encoding
    def test_encode_query_string_bool(self):

        obj = {'a': True}
        query_string = 'a=true'
        self.assertEqual(encode_query_string(obj), query_string)

    # Test date query string encoding
    def test_encode_query_string_date(self):

        obj = {'a': date(2013, 7, 18)}
        query_string = 'a=2013-07-18'
        self.assertEqual(encode_query_string(obj), query_string)

    # Test datetime query string encoding
    def test_encode_query_string_datetime(self):

        obj = {'a': datetime(2013, 7, 18, 12, 31, tzinfo=timezone.utc)}
        query_string = 'a=2013-07-18T12%3A31%3A00%2B00%3A00'
        self.assertEqual(encode_query_string(obj), query_string)

    # Test naive datetime query string encoding
    def test_encode_query_string_datetime_naive(self):

        obj = {'a': datetime(2013, 7, 18, 12, 31)}
        query_string = 'a=' + quote(obj['a'].replace(tzinfo=timezone.utc).isoformat(), encoding='utf-8')
        self.assertEqual(encode_query_string(obj), query_string)

    # Test uuid query string encoding
    def test_encode_query_string_uuid(self):

        obj = {'a': UUID('7da81f83-a656-42f1-aeb3-ab207809fb0e')}
        query_string = 'a=7da81f83-a656-42f1-aeb3-ab207809fb0e'
        self.assertEqual(encode_query_string(obj), query_string)

    # Test bool query string encoding
    def test_encode_query_string_null(self):

        obj = {'a': None}
        query_string = 'a=null'
        self.assertEqual(encode_query_string(obj), query_string)

    def test_encode_query_string_items(self):

        obj = {}
        self.assertListEqual(list(encode_query_string_items(obj)), [])

        obj = {
            'bool': True,
            'int': 19,
            'datetime': datetime(2017, 8, 2, 8, 12, 0, tzinfo=timezone.utc),
            'date': date(2017, 8, 2),
            'uuid': UUID('7da81f83-a656-42f1-aeb3-ab207809fb0e'),
            'none': None,
            'float': 3.1459,
            'a&b=c': 'a&b=c', # string
            'list': [1, 2, 3],
            'dict': {'a': 1, 'b': 2}
        }
        self.assertListEqual(list(encode_query_string_items(obj)), [
            ('a&b=c', 'a&b=c'),
            ('bool', 'true'),
            ('date', '2017-08-02'),
            ('datetime', '2017-08-02T08:12:00+00:00'),
            ('dict.a', '1'),
            ('dict.b', '2'),
            ('float', '3.1459'),
            ('int', '19'),
            ('list.0', '1'),
            ('list.1', '2'),
            ('list.2', '3'),
            ('none', 'null'),
            ('uuid', '7da81f83-a656-42f1-aeb3-ab207809fb0e')
        ])
        self.assertListEqual(list(encode_query_string_items(obj, encoding='utf-8')), [
            ('a%26b%3Dc', 'a%26b%3Dc'),
            ('bool', 'true'),
            ('date', '2017-08-02'),
            ('datetime', '2017-08-02T08%3A12%3A00%2B00%3A00'),
            ('dict.a', '1'),
            ('dict.b', '2'),
            ('float', '3.1459'),
            ('int', '19'),
            ('list.0', '1'),
            ('list.1', '2'),
            ('list.2', '3'),
            ('none', 'null'),
            ('uuid', '7da81f83-a656-42f1-aeb3-ab207809fb0e')
        ])
