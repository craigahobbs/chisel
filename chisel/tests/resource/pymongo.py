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


# Mock pymongo.Connection
class Connection:

    def __init__(self, mongoUri):

        self.mongoUri = mongoUri
        self.read_preference = None


# Mock pymongo.database.Database
class database:

    class Database:

        def __init__(self, conn, dbname):

            self.conn = conn
            self.dbname = dbname


# Mock pymongo.ReadPreference
class ReadPreference:

    PRIMARY = 0
    PRIMARY_PREFERRED = 1
    SECONDARY = 2
    SECONDARY_ONLY = 2
    SECONDARY_PREFERRED = 3
    NEAREST = 4
