#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#


# Mock pymongo exceptions
class errors:

    class AutoReconnect(Exception):
        pass

    class CollectionInvalid(Exception):
        pass

    class ConfigurationError(Exception):
        pass

    class ConnectionFailure(Exception):
        pass

    class DuplicateKeyError(Exception):
        pass

    class InvalidName(Exception):
        pass

    class InvalidOperation(Exception):
        pass

    class InvalidURI(Exception):
        pass

    class OperationFailure(Exception):
        pass

    class PyMongoError(Exception):
        pass

    class TimeoutError(Exception):
        pass

    class UnsupportedOption(Exception):
        pass


# Mock pymongo.MongoClient
class MongoClient:

    def __init__(self, mongoUri):

        self.mongoUri = mongoUri
