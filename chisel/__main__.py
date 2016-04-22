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
