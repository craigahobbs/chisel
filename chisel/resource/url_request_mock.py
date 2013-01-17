#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from ..app import ResourceType

import urllib2
import urlparse


# Url request resource type mock
#
# sendCallback(url, headers, unredirected_headers, requestData) - return isSuccess, responseData
#
class UrlRequestResourceTypeMock(ResourceType):

    def __init__(self, sendCallback):

        self.sendCallback = sendCallback
        ResourceType.__init__(self, "url_request", self._open, None)

    def _open(self, resourceString):

        return UrlRequestResourceMock(resourceString, self.sendCallback)


# Url request resource mock
class UrlRequestResourceMock:

    URLError = urllib2.URLError

    def __init__(self, hostUrl, sendCallback):

        self.hostUrl = hostUrl
        self.sendCallback = sendCallback
        self.reset()

    def reset(self):

        # Reset the request parameters
        self.data = []
        self.header = []
        self.unredirected_header = []

    def send(self, url = None, timeout = None):

        # Get the mock response
        fullUrl = urlparse.urljoin(self.hostUrl, url)
        isSuccess, responseString = self.sendCallback(fullUrl, self.header, self.unredirected_header, self.data)
        if not isSuccess:
            raise self.URLError("HTTP Error 500: Internal Server Error")

        # Reset the resource
        self.reset()

        return responseString

    def add_data(self, data):

        self.data.append(data)

    def add_header(self, key, val):

        self.header.append((key, val))

    def add_unredirected_header(self, key, val):

        self.unredirected_header.append((key, val))


# Simple, recording send callback
class SimpleSendCallback:

    def __init__(self):

        self.responses = {}
        self.requests = {}

    def addResponse(self, url, responseData, isSuccess = True):

        if url not in self.responses:
            self.responses[url] = []
        self.responses[url].append((isSuccess, responseData))

    class Request:

        def __init__(self, headers, unredirected_headers, requestData, isSuccess, responseData):

            self.headers = headers
            self.unredirected_headers = unredirected_headers
            self.requestData = requestData
            self.isSuccess = isSuccess
            self.responseData = responseData

    def __call__(self, url, headers, unredirected_headers, requestData):

        if url in self.responses and len(self.responses[url]) > 0:

            isSuccess, responseData = self.responses[url].pop(0)
            if url not in self.requests:
                self.requests[url] = []
            self.requests[url].append(self.Request(headers, unredirected_headers, requestData,
                                                   isSuccess, responseData))
            return isSuccess, responseData

        else:

            return False, None

    def __len__(self):

        return len(self.requests)

    def __getitem__(self, key):

        return self.requests[key]
