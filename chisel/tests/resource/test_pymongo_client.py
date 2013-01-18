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
        self.assertTrue(isinstance(mongoClient, pymongo.Connection))

        # Close the client (does nothing)
        resourceType.close(mongoClient)
