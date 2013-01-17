#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
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
class PymongoClientResource(pymongo.MongoClient):

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

        pymongo.MongoClient.__init__(self, resourceString)
