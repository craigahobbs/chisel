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

from chisel.resource.pyodbc_connect_mock import PyodbcConnectResourceTypeMock, SimpleExecuteCallback, PyodbcConnectionMock

import unittest


# Test PyodbcConnectResource functionality
class TestResourcePyodbcConnectMock(unittest.TestCase):

    # Test PyodbcConnectResourceTypeMock
    def test_resource_pyodbc_connect_resource_type(self):

        # Create the resource type (default non-autocommit)
        resourceType = PyodbcConnectResourceTypeMock(None, autocommit = False)
        self.assertEqual(resourceType.name, "pyodbc_connect_noautocommit")

        # Create the resource type (default autocommit)
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets)
        self.assertEqual(resourceType.name, "pyodbc_connect")

    # Test PyodbcConnectConnectionMock
    def test_resource_pyodbc_connect_mock_connection(self):

        # Setup resource type mock
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets)
        rowSets.addRowSets("MyConnectionString", "MyQuery ? ? ?", (1, 2, 3),
                           [(("a", "b", "c"),
                             [(1, 2, 3),
                              (4, 5, 6)])])

        # Create the connection
        conn = resourceType.open("MyConnectionString")

        # Test non-matching query/args failure
        try:
            conn.execute("ThierQuery")
        except conn.DatabaseError as e:
            self.assertEqual(str(e), "No row sets for ('MyConnectionString', 'ThierQuery', ())")
        else:
            self.fail()
        self.assertEqual(rowSets.executeCount, 0)

        # Test execute cursor iteration
        rows = []
        for row in conn.execute("MyQuery ? ? ?", 1, 2, 3):
            self.assertFalse(not row)
            rows.append(row)
        self.assertEqual(rowSets.executeCount, 1)
        self.assertEqual(rows[0].a, 1)
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[0].b, 2)
        self.assertEqual(rows[0][1], 2)
        self.assertEqual(rows[0].c, 3)
        self.assertEqual(rows[0][2], 3)
        self.assertEqual(rows[1].a, 4)
        self.assertEqual(rows[1][0], 4)
        self.assertEqual(rows[1].b, 5)
        self.assertEqual(rows[1][1], 5)
        self.assertEqual(rows[1].c, 6)
        self.assertEqual(rows[1][2], 6)
        self.assertTrue(not conn.isClosed)

        # Test no-rowset failure
        try:
            conn.execute("MyQuery ? ? ?", 1, 2, 3)
        except conn.DatabaseError as e:
            self.assertEqual(str(e), "No row sets for ('MyConnectionString', 'MyQuery ? ? ?', (1, 2, 3))")
        else:
            self.fail()
        self.assertEqual(rowSets.executeCount, 1)

        # Test failure after close
        resourceType.close(conn)
        self.assertTrue(conn.isClosed)

        try:
            resourceType.close(conn)
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to close an already-closed connection")
        else:
            self.fail()

        try:
            conn.cursor()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to get a cursor on an already-closed connection")
        else:
            self.fail()

        try:
            conn.execute("MyQuery ? ? ?", 9, 10, 11)
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to execute with an already-closed connection")
        else:
            self.fail()
        self.assertEqual(rowSets.executeCount, 1)

    # Test PyodbcCursorMock
    def test_resource_pyodbc_connect_mock_cursor(self):

        # Setup resource type mock
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets)
        rowSets.addRowSets("MyConnectionString", "MyQuery ? ? ?", (1, 2, 3),
                           [(("a", "b"),
                             [(1, 2),
                              (3, 4)]),
                            (("c",),
                             [(5,),
                              (6,)])])
        rowSets.addRowSets("MyConnectionString", "MyOtherQuery ?", (4,),
                           [((), [])])

        # Mismatched column names and data
        try:
            rowSets.addRowSets("MyConnectionString", "Bad", (),
                               [(("a", "b"),
                                 [(1, 2),
                                  (3, 4, 5)])])
        except AssertionError as e:
            self.assertEqual(str(e), "Column data tuple has different length than column names tuple (('a', 'b'), (3, 4, 5))")
        else:
            self.fail()

        # Create the connection
        conn = resourceType.open("MyConnectionString")

        # Get a cursor
        cursor = conn.cursor()
        self.assertTrue(not cursor.isClosed)

        # Call execute
        cursor.execute("MyQuery ? ? ?", 1, 2, 3)
        rows = []
        for row in cursor:
            self.assertFalse(not row)
            rows.append(row)
        self.assertEqual(rowSets.executeCount, 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].a, 1)
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[0].b, 2)
        self.assertEqual(rows[0][1], 2)
        self.assertEqual(rows[1].a, 3)
        self.assertEqual(rows[1][0], 3)
        self.assertEqual(rows[1].b, 4)
        self.assertEqual(rows[1][1], 4)

        try:
            rows[0].c
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to get invalid row column name 'c'")
        else:
            self.fail()

        try:
            rows[0][2]
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to get invalid row column index 2")
        else:
            self.fail()

        # Call nextset and fetchone
        cursor.nextset()
        row = cursor.fetchone()
        self.assertFalse(not row)
        rows = [row]
        for row in cursor:
            self.assertFalse(not row)
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].c, 5)
        self.assertEqual(rows[0][0], 5)
        self.assertEqual(rows[1].c, 6)
        self.assertEqual(rows[1][0], 6)

        # Too many fetchone calls
        self.assertEqual(cursor.fetchone(), None)

        # Too many nextset calls
        try:
            cursor.nextset()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to call nextset when no more row sets available")
        else:
            self.fail()

        # Don't reuse cursors
        try:
            cursor.execute("ThierQuery")
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to execute on an already-executed-on cursor")
        else:
            self.fail()
        self.assertEqual(rowSets.executeCount, 1)

        # Close the cursor
        cursor.close()
        self.assertTrue(cursor.isClosed)

        # Reuse connection
        cursor = conn.execute("MyOtherQuery ?", 4)
        self.assertEqual(rowSets.executeCount, 2)

        # Don't commit autocommit connections
        try:
            cursor.commit()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to commit an autocommit cursor")
        else:
            self.fail()

        # Test failure after close
        cursor = conn.cursor()
        resourceType.close(conn)
        self.assertTrue(conn.isClosed)

        try:
            cursor.execute("MyQuery")
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to execute on a closed cursor")
        else:
            self.fail()
        self.assertEqual(rowSets.executeCount, 2)

        try:
            cursor.fetchone()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to iterate a closed cursor")
        else:
            self.fail()

        try:
            cursor.nextset()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to call nextset on a closed cursor")
        else:
            self.fail()

        try:
            cursor.commit()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to commit an autocommit cursor")
        else:
            self.fail()

        try:
            cursor.close()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to close an already-closed cursor")
        else:
            self.fail()

    # Test empty rowset
    def test_resource_pyodbc_connect_mock_empty_rowset(self):

        # Setup resource type mock
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets)
        rowSets.addRowSets("MyConnectionString", "MyQuery", (), [])

        # Create the connection
        conn = resourceType.open("MyConnectionString")

        # Call execute
        cursor = conn.execute("MyQuery")
        self.assertTrue(not cursor.isClosed)

        # No failure but no row either
        row = cursor.fetchone()
        self.assertEqual(row, None)

        # Close the connection
        resourceType.close(conn)

    # Test PyodbcCursorMock noautcommit
    def test_resource_pyodbc_connect_mock_noautocommit(self):

        # Setup resource type mock
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets, autocommit = False)
        rowSets.addRowSets("MyConnectionString", "MyQuery ?", (1,),
                           [((), [])])

        # Connect
        conn = resourceType.open("MyConnectionString")
        cursor = conn.cursor()

        # Don't commit before execute
        try:
            cursor.commit()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to commit cursor before execute")
        else:
            self.fail()

        # Exectute, commit
        cursor.execute("MyQuery ?", 1)
        cursor.commit()
        self.assertEqual(rowSets.executeCount, 1)

        # Don't commit more than once
        try:
            cursor.commit()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to commit an already-committed cursor")
        else:
            self.fail()

        # Don't operate following commit
        try:
            cursor.nextset()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to call nextset on a committed cursor")
        else:
            self.fail()

        try:
            cursor.fetchone()
        except conn.ProgrammingError as e:
            self.assertEqual(str(e), "Attempt to iterate a committed cursor")
        else:
            self.fail()

        # Close
        resourceType.close(conn)
