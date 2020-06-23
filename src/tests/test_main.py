# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

from io import StringIO
import json
import os
import unittest.mock as unittest_mock

from chisel import SpecParserError, ValidationError
from chisel.main import main
import chisel.__main__

from . import TestCase


class TestMain(TestCase):

    TEST_SPEC = '''\
struct MyStruct
    int a
    optional bool b
'''

    TEST_MODEL = '''\
{
    "MyStruct": {
        "struct": {
            "members": [
                {
                    "name": "a",
                    "type": {
                        "builtin": "int"
                    }
                },
                {
                    "name": "b",
                    "optional": true,
                    "type": {
                        "builtin": "bool"
                    }
                }
            ],
            "name": "MyStruct"
        }
    }
}'''

    TEST_VALUE = '''\
{
    "a": "5",
    "b": "true"
}'''

    TEST_VALUE_AFTER = '''\
{
    "a": 5,
    "b": true
}'''

    def test_package_main(self):
        self.assertTrue(chisel.__main__)

    def test_compile(self):
        test_files = [
            ('test.chsl', self.TEST_SPEC)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'test.chsl')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'compile', input_path, output_path]
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), self.TEST_MODEL)

    def test_compile_compact(self):
        test_files = [
            ('test.chsl', self.TEST_SPEC)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'test.chsl')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'compile', input_path, output_path, '--compact']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), json.dumps(json.loads(self.TEST_MODEL)))

    def test_compile_stdin_stdout(self):
        argv = ['python3 -m chisel', 'compile']
        with unittest_mock.patch('sys.stdin', new=StringIO(self.TEST_SPEC)), \
             unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            main()

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), self.TEST_MODEL)

    def test_compile_stdin_dash(self):
        with self.create_test_files([]) as input_dir:
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'compile', '-', output_path]
            with unittest_mock.patch('sys.stdin', new=StringIO(self.TEST_SPEC)), \
                 unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stderr.getvalue(), '')
            self.assertEqual(stdout.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), self.TEST_MODEL)

    def test_compile_stdout_dash(self):
        argv = ['python3 -m chisel', 'compile', '-', '-']
        with unittest_mock.patch('sys.stdin', new=StringIO(self.TEST_SPEC)), \
             unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            main()

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), self.TEST_MODEL)

    def test_compile_error(self):
        argv = ['python3 -m chisel', 'compile']
        with unittest_mock.patch('sys.stdin', new=StringIO('asdf')), \
             unittest_mock.patch('sys.stdout', new=StringIO()), \
             unittest_mock.patch('sys.stderr', new=StringIO()), \
             unittest_mock.patch('sys.argv', argv):
            with self.assertRaises(SpecParserError):
                main()

    def test_validate_spec(self):
        test_files = [
            ('test.chsl', self.TEST_SPEC),
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            spec_path = os.path.join(input_dir, 'test.chsl')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--spec', spec_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), self.TEST_VALUE_AFTER)

    def test_validate_error(self):
        test_files = [
            ('test.chsl', self.TEST_SPEC),
            ('value.json', '{}')
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            spec_path = os.path.join(input_dir, 'test.chsl')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--spec', spec_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(ValidationError):
                    main()

    def test_validate_spec_error(self):
        test_files = [
            ('test.chsl', 'asdf'),
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            spec_path = os.path.join(input_dir, 'test.chsl')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--spec', spec_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(SpecParserError):
                    main()

    def test_validate_value_error(self):
        test_files = [
            ('test.chsl', self.TEST_SPEC),
            ('value.json', 'asdf')
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            spec_path = os.path.join(input_dir, 'test.chsl')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--spec', spec_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(ValueError):
                    main()

    def test_validate_model(self):
        test_files = [
            ('model.json', self.TEST_MODEL),
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            model_path = os.path.join(input_dir, 'model.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--model', model_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), self.TEST_VALUE_AFTER)

    def test_validate_model_error(self):
        test_files = [
            ('model.json', '{}'),
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            model_path = os.path.join(input_dir, 'model.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--model', model_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(ValidationError):
                    main()

    def test_validate_model_error_json(self):
        test_files = [
            ('model.json', 'asdf'),
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            model_path = os.path.join(input_dir, 'model.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--model', model_path, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(json.JSONDecodeError):
                    main()

    def test_validate_spec_str(self):
        test_files = [
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--spec-str', self.TEST_SPEC, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), self.TEST_VALUE_AFTER)

    def test_validate_spec_str_error(self):
        test_files = [
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--spec-str', 'asdf', '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(SpecParserError):
                    main()

    def test_validate_model_str(self):
        test_files = [
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--model-str', self.TEST_MODEL, '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as output_file:
                self.assertEqual(output_file.read(), self.TEST_VALUE_AFTER)

    def test_validate_model_str_error(self):
        test_files = [
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--model-str', '{}', '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(ValidationError):
                    main()

    def test_validate_model_str_error_json(self):
        test_files = [
            ('value.json', self.TEST_VALUE)
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'value.json')
            output_path = os.path.join(input_dir, 'test.json')
            argv = ['python3 -m chisel', 'validate', input_path, output_path, '--model-str', 'asdf', '--type', 'MyStruct']
            with unittest_mock.patch('sys.stdout', new=StringIO()), \
                 unittest_mock.patch('sys.stderr', new=StringIO()), \
                 unittest_mock.patch('sys.argv', argv):
                with self.assertRaises(json.JSONDecodeError):
                    main()

    def test_validate_no_spec(self):
        argv = ['python3 -m chisel', 'validate', 'value.json', 'test.json', '--type', 'MyStruct']
        with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            with self.assertRaises(SystemExit):
                main()

        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '''\
usage: python3 -m chisel [-h] {compile,validate} ...
python3 -m chisel: error: Must specify either --spec, --model, --spec-str, or --model-str
''')

    def test_validate_stdin_stdout(self):
        argv = ['python3 -m chisel', 'validate', '--spec-str', self.TEST_SPEC, '--type', 'MyStruct']
        with unittest_mock.patch('sys.stdin', new=StringIO(self.TEST_VALUE)), \
             unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            main()

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), '''\
{
    "a": 5,
    "b": true
}''')

    def test_validate_stdin_dash(self):
        argv = ['python3 -m chisel', 'validate', '-', '--spec-str', self.TEST_SPEC, '--type', 'MyStruct']
        with unittest_mock.patch('sys.stdin', new=StringIO(self.TEST_VALUE)), \
             unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            main()

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), '''\
{
    "a": 5,
    "b": true
}''')

    def test_validate_stdout_dash(self):
        argv = ['python3 -m chisel', 'validate', '-', '-', '--spec-str', self.TEST_SPEC, '--type', 'MyStruct']
        with unittest_mock.patch('sys.stdin', new=StringIO(self.TEST_VALUE)), \
             unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            main()

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), '''\
{
    "a": 5,
    "b": true
}''')

    def test_validate_no_type(self):
        argv = ['python3 -m chisel', 'validate', '--spec-str', self.TEST_SPEC]
        with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            with self.assertRaises(SystemExit):
                main()

        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '''\
usage: python3 -m chisel validate [-h] [--spec SPEC] [--spec-str SPEC]
                                  [--model MODEL] [--model-str MODEL] --type
                                  TYPE
                                  [infile] [outfile]
python3 -m chisel validate: error: the following arguments are required: --type
''')

    def test_validate_no_command(self):
        argv = ['python3 -m chisel']
        with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
             unittest_mock.patch('sys.argv', argv):
            with self.assertRaises(SystemExit):
                main()

        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '''\
usage: python3 -m chisel [-h] {compile,validate} ...
python3 -m chisel: error: the following arguments are required: command
''')
