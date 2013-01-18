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
import pymongo
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

        # Create a database
        mongoDatabase = resourceType.open("mongodb://MyMongoUri/MyMongoDatabase")
        self.assertEqual(mongoDatabase.conn.mongoUri, "mongodb://MyMongoUri/MyMongoDatabase")
        self.assertEqual(mongoDatabase.dbname, "MyMongoDatabase")
        self.assertTrue(isinstance(mongoDatabase, pymongo.database.Database))

        # Close the database (does nothing)
        resourceType.close(mongoDatabase)
