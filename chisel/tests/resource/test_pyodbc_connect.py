#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Replace pyodbc with mock
import sys
import pyodbc
sys.modules["pyodbc"] = pyodbc

from chisel.resource.pyodbc_connect import PyodbcConnectResourceType

# Restore pyodbc
del sys.modules["pyodbc"]

import unittest


# Test PyodbcConnectResource functionality
class TestResourcePyodbcConnect(unittest.TestCase):

    # Test PyodbcConnectResource usage
    def test_resource_pyodbc_connect(self):

        # Create the resource type (default autocommit)
        resourceType = PyodbcConnectResourceType()
        self.assertEqual(resourceType.name, "pyodbc_connect")

        # Create a resource
        resource = resourceType.open("MyConnectionString")
        self.assertEqual(resource.connectionString, "MyConnectionString")
        self.assertTrue(resource.autocommit)
        self.assertTrue(not resource.isClosed)
        resourceType.close(resource)
        self.assertTrue(resource.isClosed)

        # Create the resource type (autocommit = False)
        resourceType = PyodbcConnectResourceType(autocommit = False)
        self.assertEqual(resourceType.name, "pyodbc_connect")

        # Create a resource
        resource = resourceType.open("MyConnectionString2")
        self.assertEqual(resource.connectionString, "MyConnectionString2")
        self.assertTrue(not resource.autocommit)
        self.assertTrue(not resource.isClosed)
        resourceType.close(resource)
        self.assertTrue(resource.isClosed)
