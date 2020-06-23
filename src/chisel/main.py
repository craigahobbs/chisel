# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel Specification Langauge compiler and schema validator tool
"""

import argparse
import json
import sys

from .schema import validate_type, validate_types
from .spec import SpecParser
from .util import JSONEncoder


def main():
    """
    Chisel Specification Langauge compiler and schema validator tool main entry point
    """

    # Command line arguments
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(required=True, dest='command')
    parser_spec = subparsers.add_parser('compile', help='Parse a Chisel Specification Language file and output its Chisel type model JSON')
    parser_spec.add_argument('infile', nargs='?', help='Optional Chisel Specification Language file path. Default is stdin.')
    parser_spec.add_argument('outfile', nargs='?', help='Optional JSON Chisel schema type model output file path. Default is stdout.')
    parser_spec.add_argument('--compact', action='store_true', help='Write the JSON in a compact format')
    parser_validate = subparsers.add_parser('validate', help='Validate a JSON file with a Chisel schema')
    parser_validate.add_argument('infile', nargs='?', help='Optional path of JSON file to validate. Default is stdin.')
    parser_validate.add_argument('outfile', nargs='?', help='Optional path of output JSON file. Default is stdout.')
    parser_validate.add_argument('--spec', help='Path of Chisel Specification Language file')
    parser_validate.add_argument('--spec-str', metavar='SPEC', help='Chisel Specification Language string')
    parser_validate.add_argument('--model', help='Path of Chisel type model JSON file')
    parser_validate.add_argument('--model-str', metavar='MODEL', help='Chisel type model JSON string')
    parser_validate.add_argument('--type', required=True, help='Name of type to validate')
    args = arg_parser.parse_args()

    # Spec parse command?
    if args.command == 'compile':

        # Parse the spec
        parser = SpecParser()
        if args.infile is not None and args.infile != '-':
            with open(args.infile, 'r') as spec_file:
                parser.parse(spec_file)
        else:
            parser.parse(sys.stdin)

        # Write the JSON
        json_encoder = JSONEncoder(indent=None if args.compact else 4, sort_keys=True)
        if args.outfile is not None and args.outfile != '-':
            with open(args.outfile, 'w') as json_file:
                json_file.write(json_encoder.encode(parser.types))
        else:
            sys.stdout.write(json_encoder.encode(parser.types))

    # Validate command?
    else: # args.command == 'validate'
        if sum(arg is not None for arg in (args.spec, args.spec_str, args.model, args.model_str)) != 1:
            arg_parser.error('Must specify either --spec, --model, --spec-str, or --model-str')

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
        else: # args.model_str is not None
            types = validate_types(json.loads(args.model_str))

        # Validate the input JSON
        if args.infile is not None and args.infile != '-':
            with open(args.infile, 'r') as input_file:
                value = json.load(input_file)
        else:
            value = json.load(sys.stdin)
        value = validate_type(types, args.type, value)

        # Write the validated value JSON
        json_encoder = JSONEncoder(indent=4, sort_keys=True)
        if args.outfile is not None and args.outfile != '-':
            with open(args.outfile, 'w') as output_file:
                output_file.write(json_encoder.encode(value))
        else:
            sys.stdout.write(json_encoder.encode(value))
