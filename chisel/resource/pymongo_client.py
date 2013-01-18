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

import pymongo


# pymongo_client resource type
class PymongoClientResourceType(ResourceType):

    def __init__(self):

        resourceTypeName = "pymongo_client"
        ResourceType.__init__(self, resourceTypeName, self._open, self._close)

    def _open(self, resourceString):

        return PymongoClientResource(resourceString)

    def _close(self, resource):

        pass


# pymongo_client resource
class PymongoClientResource(pymongo.Connection):

    AutoReconnect = pymongo.errors.AutoReconnect
    CollectionInvalid = pymongo.errors.CollectionInvalid
    ConfigurationError = pymongo.errors.ConfigurationError
    ConnectionFailure = pymongo.errors.ConnectionFailure
    DuplicateKeyError = pymongo.errors.DuplicateKeyError
    InvalidName = pymongo.errors.InvalidName
    InvalidOperation = pymongo.errors.InvalidOperation
    InvalidURI = pymongo.errors.InvalidURI
    OperationFailure = pymongo.errors.OperationFailure
    PyMongoError = pymongo.errors.PyMongoError
    TimeoutError = pymongo.errors.TimeoutError
    UnsupportedOption = pymongo.errors.UnsupportedOption

    def __init__(self, resourceString):

        pymongo.Connection.__init__(self, resourceString)
