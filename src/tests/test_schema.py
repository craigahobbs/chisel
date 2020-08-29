# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from chisel import ValidationError, get_referenced_types, get_type_model, validate_types, validate_type

from . import TestCase


class TestTypeModel(TestCase):

    def test_get_type_model(self):
        types = get_type_model()
        types2 = get_type_model()
        self.assertDictEqual(types, types2)
        self.assertIsNot(types, types2)


class TestReferencedTypes(TestCase):

    def test_get_referenced_types(self):
        types = {
            'my_action': {
                'action': {
                    'name': 'my_action',
                    'path': 'my_action_path',
                    'query': 'my_action_query',
                    'input': 'my_action_input',
                    'output': 'my_action_output',
                    'errors': 'my_action_errors'
                }
            },
            'my_action_path': {
                'struct': {
                    'name': 'my_action_path',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'string'}}
                    ]
                }
            },
            'my_action_query': {
                'struct': {
                    'name': 'my_action_query',
                    'members': [
                        {'name': 'b', 'type': {'array': {'type': {'user': 'MyEnum'}}}}
                    ]
                }
            },
            'my_action_input': {
                'struct': {
                    'name': 'my_action_input',
                    'members': [
                        {'name': 'c', 'type': {'dict': {'type': {'user': 'MyStruct'}}}}
                    ]
                }
            },
            'my_action_output': {
                'struct': {
                    'name': 'my_action_output',
                    'members': [
                        {'name': 'd', 'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'MyEnum2'}}}}
                    ]
                }
            },
            'my_action_errors': {
                'enum': {
                    'name': 'my_action_errors',
                    'values': [
                        {'name': 'A'}
                    ]
                }
            },
            'MyEnum': {'enum': {'name': 'MyEnum'}},
            'MyEnum2': {'enum': {'name': 'MyEnum2'}},
            'MyEnumNoref': {'enum': {'name': 'MyEnumNoref'}},
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'user': 'MyTypedef'}},
                        {'name': 'b', 'type': {'user': 'MyStructEmpty'}}
                    ]
                }
            },
            'MyStructEmpty': {'struct': {'name': 'MyStructEmpty'}},
            'MyStructNoref': {'struct': {'name': 'MyStructNoref'}},
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyTypedef2'}
                }
            },
            'MyTypedef2': {
                'typedef': {
                    'name': 'MyTypedef2',
                    'type': {'builtin': 'int'}
                }
            },
            'MyTypedefNoref': {
                'typedef': {
                    'name': 'MyTypedefNoref',
                    'type': {'builtin': 'int'}
                }
            }
        }

        referenced_types = dict(types)
        del referenced_types['MyEnumNoref']
        del referenced_types['MyStructNoref']
        del referenced_types['MyTypedefNoref']

        self.assertDictEqual(
            get_referenced_types(types, 'my_action'),
            referenced_types
        )

    def test_get_referenced_types_empty_action(self):
        types = {
            'my_action': {
                'action': {
                    'name': 'my_action'
                }
            },
            'MyTypedefNoref': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'}
                }
            }
        }

        referenced_types = dict(types)
        del referenced_types['MyTypedefNoref']

        self.assertDictEqual(
            get_referenced_types(types, 'my_action'),
            referenced_types
        )

    def test_get_referenced_types_circular(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'user': 'MyStruct2'}}
                    ]
                }
            },
            'MyStruct2': {
                'struct': {
                    'name': 'MyStruct2',
                    'members': [
                        {'name': 'a', 'type': {'user': 'MyStruct'}}
                    ]
                }
            }
        }
        self.assertDictEqual(
            get_referenced_types(types, 'MyStruct'),
            types
        )


class TestValidateType(TestCase):

    @staticmethod
    def _validate_type(type_, obj):
        types = {
            'MyTypedef': {
                'typedef': {
                    'type': type_
                }
            }
        }
        return validate_type(types, 'MyTypedef', obj)

    def test_unknown(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type({}, 'Unknown', None)
        self.assertEqual(str(cm_exc.exception), "Unknown type 'Unknown'")

    def test_string(self):
        obj = 'abc'
        self.assertEqual(self._validate_type({'builtin': 'string'}, obj), obj)

    def test_string_error(self):
        obj = 7
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'string'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int'), expected type 'string'")

    def test_int(self):
        obj = 7
        self.assertIs(self._validate_type({'builtin': 'int'}, obj), obj)

    def test_int_float(self):
        obj = 7.
        self.assertEqual(self._validate_type({'builtin': 'int'}, obj), 7)

    def test_int_decimal(self):
        obj = Decimal('7')
        self.assertEqual(self._validate_type({'builtin': 'int'}, obj), 7)

    def test_int_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'int'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'int'")

    def test_int_error_float(self):
        obj = 7.5
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'int'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7.5 (type 'float'), expected type 'int'")

    def test_int_error_decimal(self):
        obj = Decimal('7.5')
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'int'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value Decimal('7.5') (type 'Decimal'), expected type 'int'")

    def test_int_error_bool(self):
        obj = True
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'int'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value True (type 'bool'), expected type 'int'")

    def test_float(self):
        obj = 7.5
        self.assertIs(self._validate_type({'builtin': 'float'}, obj), obj)

    def test_float_int(self):
        obj = 7
        self.assertEqual(self._validate_type({'builtin': 'float'}, obj), 7.)

    def test_float_decimal(self):
        obj = Decimal('7.5')
        self.assertEqual(self._validate_type({'builtin': 'float'}, obj), 7.5)

    def test_float_string(self):
        obj = '7.5'
        self.assertEqual(self._validate_type({'builtin': 'float'}, obj), 7.5)

    def test_float_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'float'")

    def test_float_error_nan(self):
        obj = 'nan'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'nan' (type 'str'), expected type 'float'")

    def test_float_error_inf(self):
        obj = 'inf'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'inf' (type 'str'), expected type 'float'")

    def test_float_error_bool(self):
        obj = True
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value True (type 'bool'), expected type 'float'")

    def test_bool(self):
        obj = False
        self.assertIs(self._validate_type({'builtin': 'bool'}, obj), obj)

    def test_bool_true(self):
        obj = 'true'
        self.assertEqual(self._validate_type({'builtin': 'bool'}, obj), True)

    def test_bool_false(self):
        obj = 'false'
        self.assertEqual(self._validate_type({'builtin': 'bool'}, obj), False)

    def test_bool_error(self):
        obj = 0
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'bool'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 0 (type 'int'), expected type 'bool'")

    def test_bool_error_string(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'bool'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'bool'")

    def test_date(self):
        obj = date(2013, 5, 26)
        self.assertIs(self._validate_type({'builtin': 'date'}, obj), obj)

    def test_date_datetime(self):
        obj = datetime(2020, 6, 17, 13, 11, tzinfo=timezone.utc)
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(
            str(cm_exc.exception),
            "Invalid value datetime.datetime(2020, 6, 17, 13, 11, tzinfo=datetime.timezone.utc) (type 'datetime'), expected type 'date'"
        )

    def test_date_string(self):
        obj = '2013-05-26'
        self.assertEqual(self._validate_type({'builtin': 'date'}, obj), date(2013, 5, 26))

    def test_date_string_datetime(self):
        obj = '2013-05-26T13:11:00-07:00'
        self.assertEqual(self._validate_type({'builtin': 'date'}, obj), date(2013, 5, 26))

    def test_date_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'date'")

    def test_date_error(self):
        obj = 0
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 0 (type 'int'), expected type 'date'")

    def test_datetime(self):
        obj = datetime(2013, 5, 26, 13, 11, tzinfo=timezone(-timedelta(hours=7)))
        self.assertIs(self._validate_type({'builtin': 'datetime'}, obj), obj)

    def test_datetime_date(self):
        obj = date(2020, 6, 17)
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value datetime.date(2020, 6, 17) (type 'date'), expected type 'datetime'")

    def test_datetime_string(self):
        obj = '2013-05-26T13:11:00-07:00'
        self.assertEqual(
            self._validate_type({'builtin': 'datetime'}, obj),
            datetime(2013, 5, 26, 13, 11, tzinfo=timezone(-timedelta(hours=7)))
        )

    def test_datetime_string_date(self):
        obj = '2013-05-26'
        self.assertEqual(
            self._validate_type({'builtin': 'datetime'}, obj),
            datetime(2013, 5, 26, tzinfo=timezone.utc)
        )

    def test_datetime_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'datetime'")

    def test_datetime_error(self):
        obj = 0
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 0 (type 'int'), expected type 'datetime'")

    def test_uuid(self):
        obj = UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3')
        self.assertIs(self._validate_type({'builtin': 'uuid'}, obj), obj)

    def test_uuid_string(self):
        obj = 'AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'
        self.assertEqual(self._validate_type({'builtin': 'uuid'}, obj), UUID(obj))

    def test_uuid_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'uuid'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'uuid'")

    def test_uuid_error(self):
        obj = 0
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'uuid'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 0 (type 'int'), expected type 'uuid'")

    def test_object(self):
        obj = object()
        self.assertIs(self._validate_type({'builtin': 'object'}, obj), obj)

    def test_object_string(self):
        obj = 'abc'
        self.assertIs(self._validate_type({'builtin': 'object'}, obj), obj)

    def test_object_int(self):
        obj = 7
        self.assertIs(self._validate_type({'builtin': 'object'}, obj), obj)

    def test_object_bool(self):
        obj = False
        self.assertIs(self._validate_type({'builtin': 'object'}, obj), obj)

    def test_array(self):
        obj = [1, 2, 3]
        self.assertListEqual(self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj), obj)

    def test_array_nullable(self):
        obj = [1, None, 3]
        self.assertListEqual(self._validate_type({'array': {'type': {'builtin': 'int'}, 'attr': {'nullable': True}}}, obj), obj)

        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member '1', expected type 'int'")

    def test_array_nullable_as_string(self):
        obj = ['1', 'null', '3']
        self.assertListEqual(
            self._validate_type({'array': {'type': {'builtin': 'int'}, 'attr': {'nullable': True}}}, obj),
            [1, None, 3]
        )

        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'null' (type 'str') for member '1', expected type 'int'")

    def test_array_empty_string(self):
        obj = []
        self.assertListEqual(self._validate_type({'array': {'type': {'builtin': 'int'}}}, ''), obj)

    def test_array_attributes(self):
        obj = [1, 2, 3]
        self.assertListEqual(self._validate_type({'array': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj), obj)

    def test_array_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'array'")

    def test_array_error_value(self):
        obj = [1, 'abc', 3]
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member '1', expected type 'int'")

    def test_array_error_value_nested(self):
        obj = [[1, 2], [1, 'abc', 3]]
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'array': {'type': {'builtin': 'int'}}}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member '1.1', expected type 'int'")

    def test_dict(self):
        obj = {'a': 1, 'b': 2, 'c': 3}
        self.assertDictEqual(self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj), obj)

    def test_dict_nullable(self):
        obj = {'a': 1, 'b': None, 'c': 3}
        self.assertDictEqual(self._validate_type({'dict': {'type': {'builtin': 'int'}, 'attr': {'nullable': True}}}, obj), obj)

        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'b', expected type 'int'")

    def test_dict_nullable_as_string(self):
        obj = {'a': '1', 'b': 'null', 'c': '3'}
        self.assertDictEqual(
            self._validate_type({'dict': {'type': {'builtin': 'int'}, 'attr': {'nullable': True}}}, obj),
            {'a': 1, 'b': None, 'c': 3}
        )

        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'null' (type 'str') for member 'b', expected type 'int'")

    def test_dict_key_nullable(self):
        obj = {'a': 1, None: 2, 'c': 3}
        self.assertDictEqual(self._validate_type({'dict': {'type': {'builtin': 'int'}, 'keyAttr': {'nullable': True}}}, obj), obj)

        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'string'")

    def test_dict_key_nullable_as_string(self):
        obj = {'a': 1, 'null': 2, 'c': 3}
        self.assertDictEqual(
            self._validate_type({'dict': {'type': {'builtin': 'int'}, 'keyAttr': {'nullable': True}}}, obj),
            {None: 2, 'a': 1, 'c': 3}
        )
        self.assertDictEqual(self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj), obj)

    def test_dict_empty_string(self):
        obj = {}
        self.assertDictEqual(self._validate_type({'dict': {'type': {'builtin': 'int'}}}, ''), obj)

    def test_dict_attributes(self):
        obj = {'a': 1, 'b': 2, 'c': 3}
        self.assertDictEqual(self._validate_type({'dict': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj), obj)

    def test_dict_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'dict'")

    def test_dict_error_value(self):
        obj = {'a': 1, 'b': 'abc', 'c': 3}
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member 'b', expected type 'int'")

    def test_dict_error_value_nested(self):
        obj = [{'a': 1}, {'a': 1, 'b': 'abc', 'c': 3}]
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'dict': {'type': {'builtin': 'int'}}}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member '1.b', expected type 'int'")

    def test_dict_key_type(self):
        types = {
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum',
                    'values': [
                        {'name': 'A'},
                        {'name': 'B'}
                    ]
                }
            },
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'MyEnum'}}}
                }
            }
        }

        obj = {'A': 1, 'B': 2}
        self.assertDictEqual(validate_type(types, 'MyTypedef', obj), obj)

        obj = {'A': 1, 'C': 2}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'C' (type 'str'), expected type 'MyEnum'")

    def test_dict_key_attr(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'builtin': 'string'}, 'keyAttr': {'lenLT': 10}}}
                }
            }
        }

        obj = {'abc': 1, 'abcdefghi': 2}
        self.assertDictEqual(validate_type(types, 'MyTypedef', obj), obj)

        obj = {'abc': 1, 'abcdefghij': 2}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abcdefghij' (type 'str'), expected type 'string' [len < 10]")

    def test_struct(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'string'}},
                        {'name': 'b', 'type': {'builtin': 'int'}},
                        {'name': 'c', 'type': {'builtin': 'float'}},
                        {'name': 'd', 'type': {'builtin': 'bool'}},
                        {'name': 'e', 'type': {'builtin': 'date'}},
                        {'name': 'f', 'type': {'builtin': 'datetime'}},
                        {'name': 'g', 'type': {'builtin': 'uuid'}},
                        {'name': 'h', 'type': {'builtin': 'object'}},
                        {'name': 'i', 'type': {'user': 'MyStruct2'}},
                        {'name': 'j', 'type': {'user': 'enum'}},
                        {'name': 'k', 'type': {'user': 'typedef'}}
                    ]
                }
            },
            'MyStruct2': {
                'struct': {
                    'name': 'MyStruct2',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'string'}},
                        {'name': 'b', 'type': {'builtin': 'int'}}
                    ]
                }
            },
            'enum': {
                'enum': {
                    'name': 'enum',
                    'values': [
                        {'name': 'A'},
                        {'name': 'B'}
                    ]
                }
            },
            'typedef': {
                'typedef': {
                    'name': 'typedef',
                    'type': {'builtin': 'int'},
                    'attr': {'gt': 0}
                }
            }
        }

        obj = {
            'a': 'abc',
            'b': 7,
            'c': 7.1,
            'd': True,
            'e': date.fromisoformat('2020-06-13'),
            'f': datetime.fromisoformat('2020-06-13T13:25:00-07:00'),
            'g': UUID('a3597528-a253-4c76-bc2d-8da0026cc838'),
            'h': {'foo': 'bar'},
            'i': {
                'a': 'abc',
                'b': 7
            },
            'j': 'A',
            'k': 1
        }
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj_transform = obj
        obj = {
            'a': 'abc',
            'b': '7', # transform
            'c': '7.1', # transform
            'd': 'true',
            'e': '2020-06-13',
            'f': '2020-06-13T13:25:00-07:00',
            'g': 'a3597528-a253-4c76-bc2d-8da0026cc838',
            'h': {'foo': 'bar'},
            'i': {
                'a': 'abc',
                'b': '7' # transform
            },
            'j': 'A',
            'k': '1' # transform
        }
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj_transform)

    def test_struct_empty_string(self):
        types = {
            'Empty': {
                'struct': {
                    'name': 'Empty'
                }
            }
        }
        obj = ''
        self.assertDictEqual(validate_type(types, 'Empty', obj), {})

    def test_struct_string_error(self):
        types = {
            'Empty': {
                'struct': {
                    'name': 'Empty'
                }
            }
        }
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'Empty', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'Empty'")

    def test_struct_union(self):
        types = {
            'MyUnion': {
                'struct': {
                    'name': 'MyUnion',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'string'}}
                    ],
                    'union': True
                }
            }
        }

        obj = {'a': 7}
        self.assertDictEqual(validate_type(types, 'MyUnion', obj), obj)

        obj = {'b': 'abc'}
        self.assertDictEqual(validate_type(types, 'MyUnion', obj), obj)

        obj = {}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyUnion', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value {} (type 'dict'), expected type 'MyUnion'")

        obj = {'c': 7}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyUnion', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member 'c'")

    def test_struct_optional(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'string'}, 'optional': True},
                        {'name': 'c', 'type': {'builtin': 'float'}, 'optional': False}
                    ]
                }
            }
        }

        obj = {'a': 7, 'b': 'abc', 'c': 7.1}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj = {'a': 7, 'c': 7.1}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj = {'a': 7}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Required member 'c' missing")

    def test_struct_nullable(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'int'}, 'attr': {'nullable': True}},
                        {'name': 'c', 'type': {'builtin': 'string'}, 'attr': {'nullable': True}},
                        {'name': 'd', 'type': {'builtin': 'float'}, 'attr': {'nullable': False}}
                    ]
                }
            }
        }

        obj = {'a': 7, 'b': 8, 'c': 'abc', 'd': 7.1}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj = {'a': 7, 'b': None, 'c': None, 'd': 7.1}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj = {'a': 7, 'b': None, 'c': 'null', 'd': 7.1}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj = {'a': 7, 'b': 'null', 'c': None, 'd': 7.1}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'null' (type 'str') for member 'b', expected type 'int'")

        obj = {'a': None, 'b': None, 'c': None, 'd': 7.1}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'a', expected type 'int'")

        obj = {'a': 7, 'b': None, 'c': None, 'd': None}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'd', expected type 'float'")

        obj = {'a': 7, 'c': None, 'd': 7.1}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Required member 'b' missing")

    def test_struct_nullable_attr(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'int'}, 'attr': {'nullable': True, 'lt': 5}}
                    ]
                }
            }
        }

        obj = {'a': 7, 'b': 4}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

        obj = {'a': 7, 'b': 5}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 5 (type 'int') for member 'b', expected type 'int' [< 5]")

        obj = {'a': 7, 'b': None}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

    def test_struct_member_attr(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}}
                    ]
                }
            }
        }
        obj = {'a': 4}
        self.assertDictEqual(validate_type(types, 'MyStruct', obj), obj)

    def test_struct_member_attr_invalid(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}}
                    ]
                }
            }
        }
        obj = {'a': 7}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int') for member 'a', expected type 'int' [< 5]")

    def test_struct_error_invalid_value(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'MyStruct'")

    def test_struct_error_optional_none_value(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'optional': True},
                    ]
                }
            }
        }
        obj = {'a': None}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'a', expected type 'int'")

    def test_struct_error_member_validation(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = {'a': 'abc'}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member 'a', expected type 'int'")

    def test_struct_error_nested_member_validation(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'user': 'MyStruct2'}}
                    ]
                }
            },
            'MyStruct2': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'b', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = {'a': {'b': 'abc'}}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member 'a.b', expected type 'int'")

    def test_struct_error_unknown_member(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = {'a': 7, 'b': 8}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member 'b'")

    def test_struct_error_unknown_member_nested(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            },
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'user': 'MyStruct'}}}
                }
            }
        }
        obj = [{'a': 5}, {'a': 7, 'b': 'abc'}]
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member '1.b'")

    def test_struct_error_unknown_member_empty(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct'
                }
            }
        }
        obj = {'b': 8}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member 'b'")

    def test_struct_error_unknown_member_long(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = {'a': 7, 'b' * 2000: 8}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member '" + 'b' * 99)

    def test_struct_error_missing_member(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                    ]
                }
            }
        }
        obj = {}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyStruct', obj)
        self.assertEqual(str(cm_exc.exception), "Required member 'a' missing")

    def test_enum(self):
        types = {
            'enum': {
                'enum': {
                    'name': 'enum',
                    'values': [
                        {'name': 'a'},
                        {'name': 'b'}
                    ]
                }
            }
        }

        obj = 'a'
        self.assertEqual(validate_type(types, 'enum', obj), obj)

        obj = 'c'
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'enum', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'c' (type 'str'), expected type 'enum'")

    def test_typedef(self):
        types = {
            'typedef': {
                'typedef': {
                    'name': 'typedef',
                    'type': {'builtin': 'int'},
                    'attr': {'gte': 5}
                }
            }
        }
        obj = 5
        self.assertIs(validate_type(types, 'typedef', obj), obj)

        obj = 4
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'typedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 4 (type 'int'), expected type 'typedef' [>= 5]")

        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'typedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'typedef'")

        obj = 'null'
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'typedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'null' (type 'str'), expected type 'int'")

    def test_typedef_no_attr(self):
        types = {
            'typedef': {
                'typedef': {
                    'name': 'typedef',
                    'type': {'builtin': 'int'}
                }
            }
        }
        obj = 5
        self.assertIs(validate_type(types, 'typedef', obj), obj)

    def test_typedef_type_error(self):
        types = {
            'typedef': {
                'typedef': {
                    'name': 'typedef',
                    'type': {'builtin': 'int'},
                    'attr': {'gte': 5}
                }
            }
        }
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'typedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'int'")

    def test_typedef_attr_eq(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'},
                    'attr': {'eq': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', 5)
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 7)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int'), expected type 'MyTypedef' [== 5]")

    def test_typedef_attr_nullable(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'},
                    'attr': {'nullable': True}
                }
            }
        }
        self.assertEqual(validate_type(types, 'MyTypedef', 5), 5)
        self.assertEqual(validate_type(types, 'MyTypedef', None), None)
        self.assertEqual(validate_type(types, 'MyTypedef', 'null'), None)
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 'abc')
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'int'")

    def test_typedef_attr_lt(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'},
                    'attr': {'lt': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', 3)
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 5)
        self.assertEqual(str(cm_exc.exception), "Invalid value 5 (type 'int'), expected type 'MyTypedef' [< 5]")
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 7)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int'), expected type 'MyTypedef' [< 5]")

    def test_typedef_attr_lte(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'},
                    'attr': {'lte': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', 5)
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 7)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int'), expected type 'MyTypedef' [<= 5]")

    def test_typedef_attr_gt(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'},
                    'attr': {'gt': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', 7)
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 3)
        self.assertEqual(str(cm_exc.exception), "Invalid value 3 (type 'int'), expected type 'MyTypedef' [> 5]")
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 5)
        self.assertEqual(str(cm_exc.exception), "Invalid value 5 (type 'int'), expected type 'MyTypedef' [> 5]")

    def test_typedef_attr_gte(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'builtin': 'int'},
                    'attr': {'gte': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', 5)
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 3)
        self.assertEqual(str(cm_exc.exception), "Invalid value 3 (type 'int'), expected type 'MyTypedef' [>= 5]")

    def test_typedef_attr_len_eq(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}},
                    'attr': {'lenEq': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5])
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3] (type 'list'), expected type 'MyTypedef' [len == 5]")

    def test_typedef_attr_len_lt(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}},
                    'attr': {'lenLT': 5}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3, 4, 5] (type 'list'), expected type 'MyTypedef' [len < 5]")
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3, 4, 5, 6, 7] (type 'list'), expected type 'MyTypedef' [len < 5]")

    def test_typedef_attr_len_lte(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}},
                    'attr': {'lenLTE': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5])
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3, 4, 5, 6, 7] (type 'list'), expected type 'MyTypedef' [len <= 5]")

    def test_typedef_attr_len_gt(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}},
                    'attr': {'lenGT': 5}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3, 4, 5] (type 'list'), expected type 'MyTypedef' [len > 5]")
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3] (type 'list'), expected type 'MyTypedef' [len > 5]")

    def test_typedef_attr_len_gte(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}},
                    'attr': {'lenGTE': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5])
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3] (type 'list'), expected type 'MyTypedef' [len >= 5]")

    def test_action(self):
        types = {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyAction', {})
        self.assertEqual(str(cm_exc.exception), "Invalid value {} (type 'dict'), expected type 'MyAction'")

    def test_invalid_model(self):
        types = {
            'MyBadBuiltin': {
                'typedef': {
                    'name': 'MyBadBuiltin',
                    'type': {'builtin': 'foobar'}
                }
            },
            'MyBadType': {
                'typedef': {
                    'name': 'MyBadType',
                    'type': {'bad_type_key': 'foobar'}
                }
            },
            'MyBadUser': {
                'typedef': {
                    'name': 'MyBadUser',
                    'type': {'user': 'MyBadUserKey'}
                }
            },
            'MyBadUserKey': {
                'bad_user_key': {}
            }
        }
        self.assertEqual(validate_type(types, 'MyBadBuiltin', 'abc'), 'abc')
        self.assertEqual(validate_type(types, 'MyBadType', 'abc'), 'abc')
        self.assertEqual(validate_type(types, 'MyBadUser', 'abc'), 'abc')


class TestValidateTypes(TestCase):

    def test_validate_types(self):
        types = get_type_model()
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_error(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyStruct': {
                    'struct': {}
                }
            })
        self.assertEqual(str(cm_exc.exception), "Required member 'MyStruct.struct.name' missing")

    def test_validate_types_inconsistent_struct_type_name(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyStruct': {
                    'struct': {
                        'name': 'MyStruct2'
                    }
                }
            })
        self.assertEqual(str(cm_exc.exception), "Inconsistent type name 'MyStruct2' for 'MyStruct'")

    def test_validate_types_unknown_member_type(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyStruct': {
                    'struct': {
                        'name': 'MyStruct',
                        'members': [
                            {'name': 'a', 'type': {'user': 'UnknownType'}}
                        ]
                    }
                }
            })
        self.assertEqual(str(cm_exc.exception), "Unknown type 'UnknownType' from 'MyStruct' member 'a'")

    def test_validate_types_duplicate_member(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyStruct': {
                    'struct': {
                        'name': 'MyStruct',
                        'members': [
                            {'name': 'a', 'type': {'builtin': 'string'}},
                            {'name': 'b', 'type': {'builtin': 'int'}},
                            {'name': 'a', 'type': {'builtin': 'int'}}
                        ]
                    }
                }
            })
        self.assertEqual(str(cm_exc.exception), "Redefinition of 'MyStruct' member 'a'")

    def test_validate_types_empty_enum(self):
        types = {
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum'
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_inconsistent_enum_type_name(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyEnum': {
                    'enum': {
                        'name': 'MyEnum2'
                    }
                }
            })
        self.assertEqual(str(cm_exc.exception), "Inconsistent type name 'MyEnum2' for 'MyEnum'")

    def test_validate_types_enum_duplicate_value(self):
        types = {
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum',
                    'values': [
                        {'name': 'A'},
                        {'name': 'B'},
                        {'name': 'A'}
                    ]
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Redefinition of 'MyEnum' value 'A'")

    def test_validate_types_array(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}}
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_array_attributes(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}, 'attr': {'gt': 0}}}
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_array_invalid_attribute(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}, 'attr': {'lenGT': 0}}}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Invalid attribute 'len > 0' from 'MyTypedef'")

    def test_validate_types_array_unknown_type(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'user': 'Unknown'}}}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Unknown type 'Unknown' from 'MyTypedef'")

    def test_validate_types_dict(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}}}
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_dict_key_type(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'MyEnum'}}}
                }
            },
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum',
                    'values': [
                        {'name': 'A'},
                        {'name': 'B'}
                    ]
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_dict_attributes(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'attr': {'gt': 0}}}
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_dict_key_attributes(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'builtin': 'string'}, 'keyAttr': {'lenGT': 0}}}
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_dict_invalid_attribute(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'attr': {'lenGT': 0}}}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Invalid attribute 'len > 0' from 'MyTypedef'")

    def test_validate_types_dict_invalid_key_attribute(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'builtin': 'string'}, 'keyAttr': {'gt': 0}}}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Invalid attribute '> 0' from 'MyTypedef'")

    def test_validate_types_dict_unknown_type(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'user': 'Unknown'}}}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Unknown type 'Unknown' from 'MyTypedef'")

    def test_validate_types_dict_unknown_key_type(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'Unknown'}}}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), '''\
Invalid dictionary key type from 'MyTypedef'
Unknown type 'Unknown' from 'MyTypedef'\
''')

    def test_validate_types_user_type_invalid_attribute(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyStruct'},
                    'attr': {'lt': 0}
                }
            },
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct'
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Invalid attribute '< 0' from 'MyTypedef'")

    def test_validate_types_user_type_nullable(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyStruct'},
                    'attr': {'nullable': True}
                }
            },
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct'
                }
            }
        }
        self.assertDictEqual(validate_types(types), types)

    def test_validate_types_typedef_attributes(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyTypedef2'},
                    'attr': {'gt': 0}
                }
            },
            'MyTypedef2': {
                'typedef': {
                    'name': 'MyTypedef2',
                    'type': {'builtin': 'int'}
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_inconsistent_typedef_type_name(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyTypedef': {
                    'typedef': {
                        'name': 'MyTypedef2',
                        'type': {'builtin': 'int'}
                    }
                }
            })
        self.assertEqual(str(cm_exc.exception), "Inconsistent type name 'MyTypedef2' for 'MyTypedef'")

    def test_validate_types_typedef_unknown_type(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyTypedef2'}
                }
            },
            'MyTypedef2': {
                'typedef': {
                    'name': 'MyTypedef2',
                    'type': {'user': 'MyTypedef3'}
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Unknown type 'MyTypedef3' from 'MyTypedef2'")

    def test_validate_types_action_empty_struct(self):
        types = {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction_query'
                }
            },
            'MyAction_query': {
                'struct': {
                    'name': 'MyAction_query'
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_inconsistent_action_type_name(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyAction': {
                    'action': {
                        'name': 'MyAction2'
                    }
                }
            })
        self.assertEqual(str(cm_exc.exception), "Inconsistent type name 'MyAction2' for 'MyAction'")

    def test_validate_types_action_unknown_type(self):
        types = {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'Unknown'
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Unknown type 'Unknown' from 'MyAction'")

    def test_validate_types_action_action(self):
        types = {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction2'
                }
            },
            'MyAction2': {
                'action': {
                    'name': 'MyAction2'
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), "Invalid reference to action 'MyAction2' from 'MyAction'")

    def test_validate_types_action_duplicate_member(self):
        types = {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction_query',
                    'input': 'MyAction_input'
                }
            },
            'MyAction_query': {
                'struct': {
                    'name': 'MyAction_query',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'c', 'type': {'builtin': 'int'}}
                    ]
                }
            },
            'MyAction_input': {
                'struct': {
                    'name': 'MyAction_input',
                    'members': [
                        {'name': 'b', 'type': {'builtin': 'int'}},
                        {'name': 'c', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), '''\
Redefinition of 'MyAction_input' member 'c'
Redefinition of 'MyAction_query' member 'c'\
''')

    def test_validate_types_member_attributes(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'gt': 0, 'lte': 10}}
                    ]
                }
            }
        }
        self.assertDictEqual(types, validate_types(types))

    def test_validate_types_invalid_member_attributes(self):
        types = {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'gt': 0, 'lte': 10, 'lenGT': 0, 'lenLTE': 10}}
                    ]
                }
            }
        }
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types(types)
        self.assertEqual(str(cm_exc.exception), '''\
Invalid attribute 'len <= 10' from 'MyStruct' member 'a'
Invalid attribute 'len > 0' from 'MyStruct' member 'a'\
''')
