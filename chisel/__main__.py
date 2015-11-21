#
# Copyright (C) 2012-2015 Craig Hobbs
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

import argparse
from wsgiref.simple_server import make_server


def main():

    # Command line arguments
    parser = argparse.ArgumentParser(prog='python -m chisel')
    parser.add_argument('file',
                        help='a Python file that contains the WSGI application callable')
    parser.add_argument('-a', dest='application', metavar='NAME', default='application',
                        help='the name of the WSGI application callable (default is "application")')
    parser.add_argument('-p', type=int, dest='port', default=8080,
                        help='the WSGI service port (default is 8080)')
    args = parser.parse_args()

    # Execute WSGI application file
    application_globals = {}
    with open(args.file) as wsgi_file:
        exec(compile(wsgi_file.read(), args.file, 'exec'), application_globals) # pylint: disable=exec-used

    # Serve the WSGI application
    print('serving on port {0}...'.format(args.port))
    make_server('', args.port, application_globals[args.application]).serve_forever()


if __name__ == '__main__':
    main()
