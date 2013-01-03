#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel.resource.pyodbc_connect_mock import PyodbcConnectResourceTypeMock

import unittest


# Test PyodbcConnectResource functionality
class TestResourcePyodbcConnectMock(unittest.TestCase):

    # Test PyodbcConnectResourceMock usage
    def test_resource_pyodbc_connect_mock(self):

        # Create the resource type (default autocommit)
        resourceType = PyodbcConnectResourceTypeMock(None)
        self.assertEqual(resourceType.name, "pyodbc_connect")
