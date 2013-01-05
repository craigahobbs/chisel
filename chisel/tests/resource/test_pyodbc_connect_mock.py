#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel.resource.pyodbc_connect_mock import PyodbcConnectResourceTypeMock, SimpleExecuteCallback

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
        rowSets.addRowSets("MyQuery ? ? ?", (1, 2, 3),
                           [(("a", "b", "c"),
                             [(1, 2, 3),
                              (4, 5, 6)])])

        # Create the connection
        conn = resourceType.open("MyConnectionString")

        # Test non-matching query/args failure
        try:
            conn.execute("ThierQuery")
        except conn.DatabaseError:
            pass
        else:
            self.fail()

        # Test execute cursor iteration
        rows = []
        for row in conn.execute("MyQuery ? ? ?", 1, 2, 3):
            rows.append(row)
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
        except conn.DatabaseError:
            pass
        else:
            self.fail()

        # Test failure after close
        resourceType.close(conn)
        self.assertTrue(conn.isClosed)

        try:
            resourceType.close(conn)
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            conn.cursor()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            conn.execute("MyQuery ? ? ?", 9, 10, 11)
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

    # Test PyodbcCursorMock
    def test_resource_pyodbc_connect_mock_cursor(self):

        # Setup resource type mock
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets)
        rowSets.addRowSets("MyQuery ? ? ?", (1, 2, 3),
                           [(("a", "b"),
                             [(1, 2),
                              (3, 4)]),
                            (("c",),
                             [(5,),
                              (6,)])])
        rowSets.addRowSets("MyOtherQuery ?", (4,),
                           [((), [])])

        # Mismatched column names and data
        try:
            rowSets.addRowSets("Bad", (),
                               [(("a", "b"),
                                 [(1, 2),
                                  (3, 4, 5)])])
        except:
            pass
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
            rows.append(row)
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
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            rows[0][2]
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Call nextset and fetchone
        cursor.nextset()
        rows = [cursor.fetchone()]
        for row in cursor:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].c, 5)
        self.assertEqual(rows[0][0], 5)
        self.assertEqual(rows[1].c, 6)
        self.assertEqual(rows[1][0], 6)

        # Too many fetchone calls
        try:
            cursor.fetchone()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Too many nextset calls
        try:
            cursor.nextset()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Don't reuse cursors
        try:
            cursor.execute("ThierQuery")
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Close the cursor
        cursor.close()
        self.assertTrue(cursor.isClosed)

        # Reuse connection
        cursor = conn.execute("MyOtherQuery ?", 4)

        # Don't commit autocommit connections
        try:
            cursor.commit()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Test failure after close
        cursor = conn.cursor()
        resourceType.close(conn)
        self.assertTrue(conn.isClosed)

        try:
            cursor.execute("MyQuery")
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            cursor.fetchone()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            cursor.nextset()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            cursor.commit()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            cursor.close()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

    # Test PyodbcCursorMock noautcommit
    def test_resource_pyodbc_connect_mock_noautocommit(self):

        # Setup resource type mock
        rowSets = SimpleExecuteCallback()
        resourceType = PyodbcConnectResourceTypeMock(rowSets, autocommit = False)
        rowSets.addRowSets("MyQuery ?", (1,),
                           [((), [])])

        # Connect
        conn = resourceType.open("MyConnectionString")
        cursor = conn.cursor()

        # Don't commit before execute
        try:
            cursor.commit()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Exectute, commit
        cursor.execute("MyQuery ?", 1)
        cursor.commit()

        # Don't commit more than once
        try:
            cursor.commit()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Don't operate following commit
        try:
            cursor.nextset()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        try:
            cursor.fetchone()
        except conn.ProgrammingError:
            pass
        else:
            self.fail()

        # Close
        resourceType.close(conn)
