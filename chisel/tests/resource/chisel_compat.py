#
# Copyright (C) 2012-2013 Craig Hobbs
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

from chisel.compat import *


# Mock urllib2
class urllib2(object):

    # Mock urllib2.Request
    class Request(object):

        def __init__(self, hostUrl):

            self.hostUrl = hostUrl
            self.data = []
            self.header = []
            self.unredirected_header = []

        def add_data(self, data):

            self.data.append(data)

        def add_header(self, key, val):

            self.header.append((key, val))

        def add_unredirected_header(self, key, val):

            self.unredirected_header.append((key, val))


    # Mock urllib2.urlopen
    @staticmethod
    def urlopen(request, data = None, timeout = None):

        parts = [request.hostUrl]
        parts.extend([str(x) for x in request.header])
        parts.extend([str(x) for x in request.unredirected_header])
        parts.extend(request.data)
        return StringIO('\n'.join(parts))


    # Mock url error
    class URLError(Exception):
        pass
