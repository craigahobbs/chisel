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

from ..app import ResourceType
from ..compat import urllib2, urlparse


# Url request resource type
class UrlRequestResourceType(ResourceType):

    def __init__(self):

        ResourceType.__init__(self, "url_request", UrlRequestResource, None)


# Url request resource
class UrlRequestResource(object):

    URLError = urllib2.URLError

    def __init__(self, hostUrl):

        self.hostUrl = hostUrl
        self.reset()

    def reset(self):

        # Reset the request parameters
        self.data = []
        self.header = []
        self.unredirected_header = []

    # Send a request - may raise URLError
    def send(self, url = None, timeout = None):

        # Build the request object, send the request, and read the response
        fullUrl = urlparse.urljoin(self.hostUrl, url)
        request = urllib2.Request(fullUrl)
        for data in self.data:
            request.add_data(data)
        for header in self.header:
            request.add_header(*header)
        for unredirected_header in self.unredirected_header:
            request.add_unredirected_header(*unredirected_header)
        if timeout is None:
            response = urllib2.urlopen(request)
        else:
            response = urllib2.urlopen(request, timeout = timeout)
        responseString = response.read()
        response.close()

        # Reset the resource
        self.reset()

        return responseString

    def add_data(self, data):

        self.data.append(data)

    def add_header(self, key, val):

        self.header.append((key, val))

    def add_unredirected_header(self, key, val):

        self.unredirected_header.append((key, val))
