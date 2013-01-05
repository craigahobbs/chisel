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

        # Create a connection
        conn = resourceType.open("MyConnectionString")
        self.assertEqual(conn._connection.connectionString, "MyConnectionString")
        self.assertTrue(conn._connection.autocommit)
        self.assertTrue(not conn._connection.isClosed)

        # Create a cursor and execute
        conn.cursor()
        conn.execute("MyQuery ? ? ?", 1, 2, 3)

        # Close the connection
        resourceType.close(conn)
        self.assertTrue(conn._connection.isClosed)

        # Create the resource type (autocommit = False)
        resourceType = PyodbcConnectResourceType(autocommit = False)
        self.assertEqual(resourceType.name, "pyodbc_connect_noautocommit")

        # Create a connection
        conn = resourceType.open("MyConnectionString2")
        self.assertEqual(conn._connection.connectionString, "MyConnectionString2")
        self.assertTrue(not conn._connection.autocommit)
        self.assertTrue(not conn._connection.isClosed)

        # Close the connection
        resourceType.close(conn)
        self.assertTrue(conn._connection.isClosed)
