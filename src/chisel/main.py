# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel Specification Langauge compiler and schema validator tool
"""

import argparse
import json
import sys

from .schema import get_type_model, validate_type, validate_types
from .spec import SpecParser
from .util import JSONEncoder


def main():
    """
    Chisel Specification Langauge compiler and schema validator tool main entry point
    """

    # Command line arguments
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(required=True, dest='command')
    parser_spec = subparsers.add_parser('compile', help='Parse specification language files and output their type model JSON')
    parser_spec.add_argument('paths', nargs='*', help='One or more specification language file paths. If none, defaults is stdin.')
    parser_spec.add_argument('-o', metavar='PATH', dest='output', help='Optional JSON type model output file path. Default is stdout.')
    parser_spec.add_argument('--compact', action='store_true', help='Generate compact JSON')
    parser_validate = subparsers.add_parser('validate', help='Validate JSON files with a type model')
    parser_validate.add_argument('paths', nargs='*', help='One or more JSON file paths to validate. If none, defaults is stdin.')
    parser_validate.add_argument('--spec', help='Specification language file path')
    parser_validate.add_argument('--spec-str', metavar='SPEC', help='Specification language string')
    parser_validate.add_argument('--model', help='JSON type model file path')
    parser_validate.add_argument('--model-str', metavar='MODEL', help='JSON type model string')
    parser_validate.add_argument('--type', required=True, help='Name of type to validate')
    parser_model = subparsers.add_parser('model', help='Dump the type model')
    parser_model.add_argument('-o', metavar='PATH', dest='output', help='Optional JSON type model output file path. Default is stdout.')
    parser_model.add_argument('--compact', action='store_true', help='Generate compact JSON')
    args = arg_parser.parse_args()

    # Spec parse command?
    if args.command == 'compile':

        # Parse the spec
        parser = SpecParser()
        if not args.paths:
            parser.parse(sys.stdin)
        else:
            for path in args.paths:
                with open(path, 'r') as spec_file:
                    parser.parse(spec_file, finalize=False)
            parser.finalize()

        # Write the JSON
        json_encoder = JSONEncoder(indent=None if args.compact else 4, sort_keys=True)
        if args.output is not None:
            with open(args.output, 'w') as json_file:
                json_file.write(json_encoder.encode(parser.types))
        else:
            sys.stdout.write(json_encoder.encode(parser.types))

    # Validate command?
    elif args.command == 'validate':

        # Parse the spec or model
        if args.spec is not None:
            parser = SpecParser()
            parser.load(args.spec)
            types = parser.types
        elif args.model is not None:
            with open(args.model, 'r') as model_file:
                types = json.load(model_file)
            types = validate_types(types)
        elif args.spec_str is not None:
            types = SpecParser(args.spec_str).types
        elif args.model_str is not None:
            types = validate_types(json.loads(args.model_str))
        else:
            types = get_type_model()

        # Validate the input JSON
        if not args.paths:
            value = json.load(sys.stdin)
        else:
            for path in args.paths:
                with open(path, 'r') as input_file:
                    value = json.load(input_file)
                validate_type(types, args.type, value)

    # Model command?
    else: # args.command == 'model'
        json_encoder = JSONEncoder(indent=None if args.compact else 4, sort_keys=True)
        types = get_type_model()
        if args.output is not None:
            with open(args.output, 'w') as json_file:
                json_file.write(json_encoder.encode(types))
        else:
            sys.stdout.write(json_encoder.encode(types))
