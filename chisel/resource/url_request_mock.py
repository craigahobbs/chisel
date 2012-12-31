#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from ..app import ResourceType


# Url request resource type mock
class UrlRequestResourceTypeMock(ResourceType):

    def __init__(self):

        self.requests = []
        self.responses = {}
        ResourceType.__init__(self, "url_request", self.createResource, None)

    def addResponse(self, url, response):

        if url not in self.responses:
            self.responses[url] = []
        self.responses[url].append(response)

    def createResource(self, resourceString):

        return UrlRequestResourceMock(self, resourceString)


# Url request resource mock
class UrlRequestResourceMock:

    def __init__(self, resourceType, hostUrl):

        self.resourceType = resourceType
        self.hostUrl = hostUrl
        self.reset()

    def reset(self):

        # Reset the request parameters
        self.data = []
        self.header = []
        self.unredirected_header = []

    def send(self, url):

        # Get the mock response
        if url in self.resourceType.responses and len(self.resourceType.responses[url]) > 0:
            responseString = self.resourceType.responses[url].pop(0)
        else:
            raise Exception("No mock response found for %r" % (url))

        # Record the request/response
        self.resourceType.requests.append((url, self.header, self.unredirected_header, self.data, responseString))

        # Reset the resource
        self.reset()

        return responseString

    def add_data(self, data):

        self.data.append(data)

    def add_header(self, key, val):

        self.header.append((key, val))

    def add_unredirected_header(self, key, val):

        self.unredirected_header.append((key, val))
