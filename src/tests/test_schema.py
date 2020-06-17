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

    @staticmethod
    def test_validate_types():
        types = get_type_model()
        validate_types(types)

    def test_validate_types_error(self):
        with self.assertRaises(ValidationError) as cm_exc:
            validate_types({
                'MyStruct': {
                    'struct': {}
                }
            })
        self.assertEqual(str(cm_exc.exception), "Required member 'MyStruct.struct.name' missing")

    def test_validate_types_post_error(self):
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
        self.assertEqual(str(cm_exc.exception), "Unknown member type 'UnknownType'")


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
                        {'name': 'd', 'type': {'dict': {'type': {'builtin': 'int'}, 'key_type': {'user': 'MyEnum2'}}}}
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

    def test_string(self):
        obj = 'abc'
        obj2 = self._validate_type({'builtin': 'string'}, obj)
        self.assertIs(obj2, obj)

    def test_string_error(self):
        obj = 7
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'string'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int'), expected type 'string'")

    def test_int(self):
        obj = 7
        obj2 = self._validate_type({'builtin': 'int'}, obj)
        self.assertIs(obj2, obj)

    def test_int_float(self):
        obj = 7.
        obj2 = self._validate_type({'builtin': 'int'}, obj)
        self.assertEqual(obj2, obj)

    def test_int_decimal(self):
        obj = Decimal('7')
        obj2 = self._validate_type({'builtin': 'int'}, obj)
        self.assertEqual(obj2, obj)

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
        obj2 = self._validate_type({'builtin': 'float'}, obj)
        self.assertIs(obj2, obj)

    def test_float_int(self):
        obj = 7
        obj2 = self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(obj2, obj)

    def test_float_decimal(self):
        obj = Decimal('7.5')
        obj2 = self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(obj2, obj)

    def test_float_string(self):
        obj = '7.5'
        obj2 = self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(obj2, 7.5)

    def test_float_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'float'")

        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'float'")

    def test_float_error_nan(self):
        obj = 'nan'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value nan (type 'float'), expected type 'float'")

    def test_float_error_inf(self):
        obj = 'inf'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value inf (type 'float'), expected type 'float'")

    def test_float_error_bool(self):
        obj = True
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'float'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value True (type 'bool'), expected type 'float'")

    def test_bool(self):
        obj = False
        obj2 = self._validate_type({'builtin': 'bool'}, obj)
        self.assertIs(obj2, obj)

    def test_bool_transform(self):
        for obj, expected in (('false', False), ('true', True)):
            obj2 = self._validate_type({'builtin': 'bool'}, obj)
            self.assertEqual(obj2, expected)

    def test_bool_error(self):
        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'bool'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'bool'")

    def test_bool_error_string(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'bool'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'bool'")

    def test_date(self):
        obj = date.fromisoformat('2013-05-26')
        obj2 = self._validate_type({'builtin': 'date'}, obj)
        self.assertIs(obj2, obj)

    def test_date_datetime(self):
        obj = datetime(2020, 6, 17, 13, 11, tzinfo=timezone.utc)
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(
            str(cm_exc.exception),
            "Invalid value datetime.datetime(2020, 6, 17, 13, 11, tzinfo=datetime.timezone.utc) (type 'datetime'), expected type 'date'"
        )

    def test_date_datetime_date(self):
        obj = datetime(2020, 6, 17, tzinfo=timezone.utc)
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(
            str(cm_exc.exception),
            "Invalid value datetime.datetime(2020, 6, 17, 0, 0, tzinfo=datetime.timezone.utc) (type 'datetime'), expected type 'date'"
        )

    def test_date_string(self):
        obj = '2013-05-26'
        obj2 = self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(obj2, date.fromisoformat(obj))

    def test_date_string_datetime(self):
        obj = '2013-05-26T13:11:00-07:00'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value '2013-05-26T13:11:00-07:00' (type 'str'), expected type 'date'")

    def test_date_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'date'")

    def test_date_error(self):
        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'date'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'date'")

    def test_datetime(self):
        obj = datetime.fromisoformat('2013-05-26T13:11:00-07:00')
        obj2 = self._validate_type({'builtin': 'datetime'}, obj)
        self.assertIs(obj2, obj)

    def test_datetime_date(self):
        obj = date(2020, 6, 17)
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value datetime.date(2020, 6, 17) (type 'date'), expected type 'datetime'")

    def test_datetime_string(self):
        obj = '2013-05-26T13:11:00-07:00'
        obj2 = self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(obj2, datetime(2013, 5, 26, 13, 11, tzinfo=timezone(-timedelta(hours=7))))

    def test_datetime_string_date(self):
        obj = '2013-05-26'
        obj2 = self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(obj2, datetime(2013, 5, 26, tzinfo=timezone.utc))

    def test_datetime_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'datetime'")

    def test_datetime_error(self):
        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'datetime'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'datetime'")

    def test_uuid(self):
        obj = UUID('AED91C7B-DCFD-49B3-A483-DBC9EA2031A3')
        obj2 = self._validate_type({'builtin': 'uuid'}, obj)
        self.assertIs(obj2, obj)

    def test_uuid_string(self):
        obj = 'AED91C7B-DCFD-49B3-A483-DBC9EA2031A3'
        obj2 = self._validate_type({'builtin': 'uuid'}, obj)
        self.assertEqual(obj2, UUID(obj))

    def test_uuid_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'uuid'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'uuid'")

    def test_uuid_error(self):
        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'uuid'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'uuid'")

    def test_object(self):
        for obj in (object(), 'abc', 7, False):
            obj2 = self._validate_type({'builtin': 'object'}, obj)
            self.assertIs(obj2, obj)

    def test_object_error(self):
        obj = None
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'builtin': 'object'}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType'), expected type 'object'")

    def test_array(self):
        obj = [1, 2, 3]
        obj2 = self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertListEqual(obj2, obj)

    def test_array_empty_string(self):
        obj = ''
        obj2 = self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertListEqual(obj2, [])

    def test_array_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'array': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'array'")

    def test_array_attributes(self):
        obj = [1, 2, 3]
        obj2 = self._validate_type({'array': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj)
        self.assertListEqual(obj2, obj)

    def test_dict(self):
        obj = {'a': 1, 'b': 2, 'c': 3}
        obj2 = self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertDictEqual(obj2, obj)

    def test_dict_empty_string(self):
        obj = ''
        obj2 = self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertDictEqual(obj2, {})

    def test_dict_string_error(self):
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            self._validate_type({'dict': {'type': {'builtin': 'int'}}}, obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'dict'")

    def test_dict_attributes(self):
        obj = {'a': 1, 'b': 2, 'c': 3}
        obj2 = self._validate_type({'dict': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj)
        self.assertDictEqual(obj2, obj)

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
                    'type': {'dict': {'type': {'builtin': 'int'}, 'key_type': {'user': 'MyEnum'}}}
                }
            }
        }

        obj = {'A': 1, 'B': 2}
        obj2 = validate_type(types, 'MyTypedef', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'A': 1, 'C': 2}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'C' (type 'str'), expected type 'MyEnum'")

    def test_dict_key_attr(self):
        types = {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'key_type': {'builtin': 'string'}, 'key_attr': {'len_lt': 10}}}
                }
            }
        }

        obj = {'abc': 1, 'abcdefghi': 2}
        obj2 = validate_type(types, 'MyTypedef', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'abc': 1, 'abcdefghij': 2}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abcdefghij' (type 'str'), expected type 'string' [len < 10]")

    def test_struct(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'string'}},
                        {'name': 'b', 'type': {'builtin': 'int'}},
                        {'name': 'c', 'type': {'builtin': 'float'}},
                        {'name': 'd', 'type': {'builtin': 'bool'}},
                        {'name': 'e', 'type': {'builtin': 'date'}},
                        {'name': 'f', 'type': {'builtin': 'datetime'}},
                        {'name': 'g', 'type': {'builtin': 'uuid'}},
                        {'name': 'h', 'type': {'builtin': 'object'}},
                        {'name': 'i', 'type': {'user': 'struct2'}},
                        {'name': 'j', 'type': {'user': 'enum'}},
                        {'name': 'k', 'type': {'user': 'typedef'}}
                    ]
                }
            },
            'struct2': {
                'struct': {
                    'name': 'struct2',
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
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

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
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj_transform)

    def test_struct_empty_string(self):
        types = {
            'Empty': {
                'struct': {
                    'name': 'Empty'
                }
            }
        }
        obj = ''
        obj2 = validate_type(types, 'Empty', obj)
        self.assertDictEqual(obj2, {})

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
            'union': {
                'struct': {
                    'name': 'union',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'string'}}
                    ],
                    'union': True
                }
            }
        }

        obj = {'a': 7}
        obj2 = validate_type(types, 'union', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'b': 'abc'}
        obj2 = validate_type(types, 'union', obj)
        self.assertDictEqual(obj2, obj)

        obj = {}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'union', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value {} (type 'dict'), expected type 'union'")

        obj = {'c': 7}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'union', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member 'c'")

    def test_struct_optional(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'string'}, 'optional': True},
                        {'name': 'c', 'type': {'builtin': 'float'}, 'optional': False}
                    ]
                }
            }
        }

        obj = {'a': 7, 'b': 'abc', 'c': 7.1}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'a': 7, 'c': 7.1}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'a': 7}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Required member 'c' missing")

    def test_struct_nullable(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'int'}, 'nullable': True},
                        {'name': 'c', 'type': {'builtin': 'string'}, 'nullable': True},
                        {'name': 'd', 'type': {'builtin': 'float'}, 'nullable': False}
                    ]
                }
            }
        }

        obj = {'a': 7, 'b': 8, 'c': 'abc', 'd': 7.1}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'a': 7, 'b': None, 'c': None, 'd': 7.1}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'a': 7, 'b': None, 'c': 'null', 'd': 7.1}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'a': 7, 'b': 'null', 'c': None, 'd': 7.1}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'null' (type 'str') for member 'b', expected type 'int'")

        obj = {'a': None, 'b': None, 'c': None, 'd': 7.1}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'a', expected type 'int'")

        obj = {'a': 7, 'b': None, 'c': None, 'd': None}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'd', expected type 'float'")

        obj = {'a': 7, 'c': None, 'd': 7.1}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Required member 'b' missing")

    def test_struct_nullable_attr(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}, 'nullable': True}
                    ]
                }
            }
        }

        obj = {'a': 7, 'b': 4}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

        obj = {'a': 7, 'b': 5}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 5 (type 'int') for member 'b', expected type 'int' [< 5]")

        obj = {'a': 7, 'b': None}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

    def test_struct_member_attributes_valid(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}}
                    ]
                }
            }
        }
        obj = {'a': 4}
        obj2 = validate_type(types, 'struct', obj)
        self.assertDictEqual(obj2, obj)

    def test_struct_member_attributes_invalid(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}}
                    ]
                }
            }
        }
        obj = {'a': 7}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 7 (type 'int') for member 'a', expected type 'int' [< 5]")

    def test_struct_error_invalid_value(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = 'abc'
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str'), expected type 'struct'")

    def test_struct_error_optional_none_value(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'optional': True},
                    ]
                }
            }
        }
        obj = {'a': None}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value None (type 'NoneType') for member 'a', expected type 'int'")

    def test_struct_error_member_validation(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = {'a': 'abc'}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member 'a', expected type 'int'")

    def test_struct_error_nested_member_validation(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'user': 'struct2'}}
                    ]
                }
            },
            'struct2': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'b', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
        obj = {'a': {'b': 'abc'}}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 'abc' (type 'str') for member 'a.b', expected type 'int'")

    def test_struct_error_unknown_member(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                    ]
                }
            }
        }
        obj = {'a': 7, 'b': 8}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member 'b'")

    def test_struct_error_unknown_member_empty(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct'
                }
            }
        }
        obj = {'b': 8}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member 'b'")

    def test_struct_error_unknown_member_long(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                    ]
                }
            }
        }
        obj = {'a': 7, 'b' * 2000: 8}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
        self.assertEqual(str(cm_exc.exception), "Unknown member '" + 'b' * 99)

    def test_struct_error_missing_member(self):
        types = {
            'struct': {
                'struct': {
                    'name': 'struct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                    ]
                }
            }
        }
        obj = {}
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'struct', obj)
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
        obj2 = validate_type(types, 'enum', obj)
        self.assertEqual(obj2, obj)

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
        obj2 = validate_type(types, 'typedef', obj)
        self.assertIs(obj2, obj)

        obj = 4
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'typedef', obj)
        self.assertEqual(str(cm_exc.exception), "Invalid value 4 (type 'int'), expected type 'typedef' [>= 5]")

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
        obj2 = validate_type(types, 'typedef', obj)
        self.assertIs(obj2, obj)

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
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 5)
        self.assertEqual(str(cm_exc.exception), "Invalid value 5 (type 'int'), expected type 'MyTypedef' [> 5]")
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', 3)
        self.assertEqual(str(cm_exc.exception), "Invalid value 3 (type 'int'), expected type 'MyTypedef' [> 5]")

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
                    'attr': {'len_eq': 5}
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
                    'attr': {'len_lt': 5}
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
                    'attr': {'len_lte': 5}
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
                    'attr': {'len_gt': 5}
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
                    'attr': {'len_gte': 5}
                }
            }
        }
        validate_type(types, 'MyTypedef', [1, 2, 3, 4, 5])
        with self.assertRaises(ValidationError) as cm_exc:
            validate_type(types, 'MyTypedef', [1, 2, 3])
        self.assertEqual(str(cm_exc.exception), "Invalid value [1, 2, 3] (type 'list'), expected type 'MyTypedef' [len >= 5]")

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
        self.assertIsNone(validate_type(types, 'MyBadBuiltin', None))
        self.assertIsNone(validate_type(types, 'MyBadType', None))
        self.assertIsNone(validate_type(types, 'MyBadUser', None))
