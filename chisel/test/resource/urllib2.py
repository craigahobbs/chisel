#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from StringIO import StringIO


# Mock urllib2.Request
class Request:

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
def urlopen(request):

    parts = [request.hostUrl]
    parts.extend([str(x) for x in request.header])
    parts.extend([str(x) for x in request.unredirected_header])
    parts.extend(request.data)
    return StringIO("\n".join(parts))
