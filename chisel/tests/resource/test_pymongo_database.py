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

# Replace pymongo with mock
import sys
from . import pymongo
sys.modules["pymongo"] = pymongo
sys.modules["pymongo.database"] = pymongo

from chisel.resource.pymongo_database import PymongoDatabaseResourceType

# Restore pymongo
del sys.modules["pymongo"]
del sys.modules["pymongo.database"]

import unittest


# Test PymongoDatabaseResource functionality
class TestResourcePymongoDatabase(unittest.TestCase):

    # Test PymongoDatabaseResource usage
    def test_resource_pymongo_database(self):

        # Create the resource type (default autocommit)
        resourceType = PymongoDatabaseResourceType()
        self.assertEqual(resourceType.name, "pymongo_database")

        # Mongo URI with database, no user info
        mongodb = resourceType.open("mongodb://myhost/mydatabase?myoption=myvalue")
        self.assertEqual(mongodb.conn.mongoUri, "mongodb://myhost/?myoption=myvalue")
        self.assertEqual(mongodb.conn.read_preference, None)
        self.assertTrue(isinstance(mongodb, pymongo.database.Database))
        self.assertEqual(mongodb.dbname, "mydatabase")
        resourceType.close(mongodb)

        # Mongo URI with database, with user info
        mongodb = resourceType.open("mongodb://myuser:mypass@myhost/mydatabase?myoption=myvalue")
        self.assertEqual(mongodb.conn.mongoUri, "mongodb://myuser:mypass@myhost/mydatabase?myoption=myvalue")
        self.assertEqual(mongodb.conn.read_preference, None)
        self.assertTrue(isinstance(mongodb, pymongo.database.Database))
        self.assertEqual(mongodb.dbname, "mydatabase")
        resourceType.close(mongodb)

        # Mongo URI with database, with read preference
        mongodb = resourceType.open("mongodb://myhost/mydatabase?myoption=myvalue&readPreference=secondary")
        self.assertEqual(mongodb.conn.mongoUri, "mongodb://myhost/?myoption=myvalue")
        self.assertEqual(mongodb.conn.read_preference, pymongo.ReadPreference.SECONDARY)
        self.assertTrue(isinstance(mongodb, pymongo.database.Database))
        self.assertEqual(mongodb.dbname, "mydatabase")
        resourceType.close(mongodb)

        # Mongo URI with database, with read_preference #2
        mongodb = resourceType.open("mongodb://myhost/mydatabase?readPreference=secondary")
        self.assertEqual(mongodb.conn.mongoUri, "mongodb://myhost")
        self.assertEqual(mongodb.conn.read_preference, pymongo.ReadPreference.SECONDARY)
        self.assertTrue(isinstance(mongodb, pymongo.database.Database))
        self.assertEqual(mongodb.dbname, "mydatabase")
        resourceType.close(mongodb)

        # No database
        try:
            resourceType.open("mongodb://myhost")
        except pymongo.errors.InvalidURI:
            pass
        else:
            self.fail()

        # Invalid read preference
        try:
            resourceType.open("mongodb://myhost/mydatabase?readPreference=asdf")
        except pymongo.errors.ConfigurationError:
            pass
        else:
            self.fail()
