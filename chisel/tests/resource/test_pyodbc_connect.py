#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Replace pyodbc with mock
import sys
import pyodbc
sys.modules["pyodbc"] = pyodbc

from chisel.resource.pyodbc_connect import PyodbcResourceType

# Restore pyodbc
del sys.modules["pyodbc"]

import unittest


# Test PyodbcResource functionality
class TestResourcePyodbc(unittest.TestCase):

    # Test PyodbcResource usage
    def test_resource_url_request(self):

        # Create the resource type (default autocommit)
        resourceType = PyodbcResourceType()
        self.assertEqual(resourceType.name, "pyodbc")

        # Create a resource
        resource = resourceType.open("MyConnectionString")
        self.assertEqual(resource.connectionString, "MyConnectionString")
        self.assertTrue(resource.autocommit)
        self.assertTrue(not resource.isClosed)
        resourceType.close(resource)
        self.assertTrue(resource.isClosed)

        # Create the resource type (autocommit = False)
        resourceType = PyodbcResourceType(autocommit = False)
        self.assertEqual(resourceType.name, "pyodbc")

        # Create a resource
        resource = resourceType.open("MyConnectionString2")
        self.assertEqual(resource.connectionString, "MyConnectionString2")
        self.assertTrue(not resource.autocommit)
        self.assertTrue(not resource.isClosed)
        resourceType.close(resource)
        self.assertTrue(resource.isClosed)
