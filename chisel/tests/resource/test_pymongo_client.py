#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Replace pymongo with mock
import sys
import pymongo
sys.modules["pymongo"] = pymongo

from chisel.resource.pymongo_client import PymongoClientResourceType

# Restore pymongo
del sys.modules["pymongo"]

import unittest


# Test PymongoClientResource functionality
class TestResourcePymongoClient(unittest.TestCase):

    # Test PymongoClientResource usage
    def test_resource_pymongo_client(self):

        # Create the resource type (default autocommit)
        resourceType = PymongoClientResourceType()
        self.assertEqual(resourceType.name, "pymongo_client")

        # Create a client
        mongoClient = resourceType.open("MyMongoUri")
        self.assertEqual(mongoClient.mongoUri, "MyMongoUri")
        self.assertTrue(isinstance(mongoClient, pymongo.MongoClient))

        # Close the client (does nothing)
        resourceType.close(mongoClient)
