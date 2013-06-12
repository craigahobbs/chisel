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

# Replace pyodbc with mock
import sys
from . import pyodbc
sys.modules['pyodbc'] = pyodbc

from chisel.resource.pyodbc_connect import PyodbcConnectResourceType

# Restore pyodbc
del sys.modules['pyodbc']

import unittest


# Test PyodbcConnectResource functionality
class TestResourcePyodbcConnect(unittest.TestCase):

    # Test PyodbcConnectResource usage
    def test_resource_pyodbc_connect(self):

        # Create the resource type
        resourceType = PyodbcConnectResourceType()

        # Create a connection
        conn = resourceType.open('MyConnectionString')
        self.assertEqual(conn._connection.connectionString, 'MyConnectionString')
        self.assertTrue(conn._connection.autocommit)
        self.assertTrue(not conn._connection.isClosed)

        # Create a cursor and execute
        conn.cursor()
        conn.execute('MyQuery ? ? ?', 1, 2, 3)

        # Close the connection
        resourceType.close(conn)
        self.assertTrue(conn._connection.isClosed)
