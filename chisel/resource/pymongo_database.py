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

import pymongo
import pymongo.database

import re


# pymongo_database resource type
class PymongoDatabaseResourceType(object):
    __slots__ = ()

    @staticmethod
    def open(resourceString):
        return PymongoDatabaseResource(resourceString)

    @staticmethod
    def close(resource):
        pass


# pymongo_database resource
class PymongoDatabaseResource(pymongo.database.Database):
    __slots__ = ()

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

    _reMongoUri = re.compile('^mongodb://((?P<userinfo>.+?)@)?(?P<hosts>.+?)(/(?P<database>.+?))(\?(?P<options>.+))?$')
    _readPreferences = {
        'primary': pymongo.ReadPreference.PRIMARY,
        'primary_preferred': pymongo.ReadPreference.PRIMARY_PREFERRED,
        'secondary': pymongo.ReadPreference.SECONDARY,
        'secondary_preferred': pymongo.ReadPreference.SECONDARY_PREFERRED,
        'nearest': pymongo.ReadPreference.NEAREST
        }

    def __init__(self, resourceString):

        # Parse the mongo URI
        mMongoUri = self._reMongoUri.search(resourceString)
        if not mMongoUri:
            raise self.InvalidURI('Unrecognized mongo database URI')
        userinfo = mMongoUri.group('userinfo')
        hosts = mMongoUri.group('hosts')
        database = mMongoUri.group('database')
        _options = mMongoUri.group('options')

        # Remove the readPreference option to work around pymongo uri_parser bug
        options = []
        readPreference = None
        if _options:
            for option in _options.split('&'):
                if option.startswith('readPreference='):
                    readPreference = self._readPreferences.get(option.split('=')[1])
                    if not readPreference:
                        raise self.ConfigurationError('Not a valid read preference')
                else:
                    options.append(option)

        # Rebuild the URI
        mongoUri = 'mongodb://'
        if userinfo:
            mongoUri += userinfo + '@'
        mongoUri += hosts
        if userinfo: # Only add database if there is user info - avoids pymongo warn
            mongoUri += '/' + database
        if options:
            mongoUri += ('?' if userinfo else '/?') + '&'.join(options)

        # Connect to the database
        conn = pymongo.Connection(mongoUri)
        if readPreference:
            conn.read_preference = readPreference
        pymongo.database.Database.__init__(self, conn, database)
