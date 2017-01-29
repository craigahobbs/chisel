# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from argparse import ArgumentParser
from wsgiref.simple_server import make_server

from chisel import Application, DocAction, __version__ as chisel_version
try:
    from repoze.profile import ProfileMiddleware
except ImportError:
    pass


def main():

    # Command line arguments
    parser = ArgumentParser(prog='python -m chisel')
    parser.add_argument('file', nargs='?',
                        help='a Python file that contains the WSGI application callable')
    parser.add_argument('-c', dest='application', metavar='NAME', default='application',
                        help='the name of the WSGI application callable (default is "application")')
    parser.add_argument('-p', type=int, dest='port', default=8080,
                        help='the WSGI service port (default is 8080)')
    parser.add_argument('--profile', action='store_true', dest='profile',
                        help='enable the profiler at /__profile__')
    parser.add_argument('-v', '--version', action='store_true', dest='version',
                        help='print the chisel version')
    args = parser.parse_args()

    # Version?
    if args.version:
        print(chisel_version)
        return

    # Execute WSGI application file
    if args.file:
        application_globals = {}
        with open(args.file) as wsgi_file:
            exec(compile(wsgi_file.read(), args.file, 'exec'), application_globals) # pylint: disable=exec-used
        application = application_globals[args.application]
    else:
        application = Application()
        application.add_request(DocAction())

    # Wrap with profiler application?
    if args.profile:
        application = ProfileMiddleware(application)

    # Serve the WSGI application
    print('serving on port {0}...'.format(args.port))
    make_server('', args.port, application).serve_forever()


if __name__ == '__main__':
    main()
