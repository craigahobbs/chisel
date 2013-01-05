#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from ..app import ResourceType

import datetime
import decimal


# pyodbc_connect resource type mock
class PyodbcConnectResourceTypeMock(ResourceType):

    # executeCallback(query, *args), returns [(columnNames, columnDatas), ...]
    def __init__(self, executeCallback, autocommit = True):

        self.executeCallback = executeCallback
        self.autocommit = autocommit
        resourceTypeName = "pyodbc_connect" if autocommit else "pyodbc_connect_noautocommit"
        ResourceType.__init__(self, resourceTypeName, self._open, self._close)

    def _open(self, resourceString):

        return PyodbcConnectionMock(resourceString, self.executeCallback, self.autocommit)

    def _close(self, resource):

        resource.close()


# pyodbc connection mock
class PyodbcConnectionMock:

    class Error(StandardError):
        pass

    class DatabaseError(Error):
        pass

    class DataError(DatabaseError):
        pass

    class OperationalError(DatabaseError):
        pass

    class IntegrityError(DatabaseError):
        pass

    class InternalError(DatabaseError):
        pass

    class ProgrammingError(DatabaseError):
        pass

    def __init__(self, resourceString, executeCallback, autocommit):

        self.resourceString = resourceString
        self.executeCallback = executeCallback
        self.autocommit = autocommit
        self.isClosed = False

    def close(self):

        if self.isClosed:
            raise self.ProgrammingError()

        self.isClosed = True

    def cursor(self):

        if self.isClosed:
            raise self.ProgrammingError()

        return PyodbcCursorMock(self)

    def execute(self, query, *args):

        if self.isClosed:
            raise self.ProgrammingError()

        cursor = self.cursor()
        return cursor.execute(query, *args)


# pyodbc row mock
class PyodbcRowMock:

    def __init__(self, columnNames, columnData):

        assert len(columnNames) == len(columnData)
        self.columnNames = columnNames
        self.columnData = columnData

    def __getitem__(self, ixColumn):

        try:
            return self.columnData[ixColumn]
        except:
            raise PyodbcConnectionMock.ProgrammingError()

    def __getattr__(self, columnName):

        try:
            ixColumn = self.columnNames.index(columnName)
            return self.columnData[ixColumn]
        except:
            raise PyodbcConnectionMock.ProgrammingError()


# Assert rowSets is properly formed - [(columnNames, columnDatas), ...]
def assertRowSets(rowSets):

    for rowSet in rowSets:
        assert len(rowSet) == 2
        assert isinstance(rowSet[0], (tuple, list))
        for columnName in rowSet[0]:
            assert isinstance(columnName, str)
        assert isinstance(rowSet[1], (tuple, list))
        for columnData in rowSet[1]:
            assert isinstance(columnData, (tuple, list))
            assert len(rowSet[0]) == len(columnData)
            for data in columnData:
                assert isinstance(data, (type(None),
                                         str,
                                         bytearray,
                                         bool,
                                         datetime.date,
                                         datetime.time,
                                         datetime.datetime,
                                         int,
                                         long,
                                         float,
                                         decimal.Decimal))


# pyodbc cursor mock
class PyodbcCursorMock:

    def __init__(self, connection):

        self.connection = connection
        self._reset()

    def _reset(self):

        self.isClosed = False
        self.isCommit = False
        self.rowSets = None
        self.ixRowSet = 0
        self.ixRow = 0

    def close(self):

        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError()

        self.isClosed = True

    def commit(self):

        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError()
        if self.isCommit:
            raise self.connection.ProgrammingError()
        if self.connection.autocommit:
            raise self.connection.ProgrammingError()
        if self.rowSets is None:
            raise self.connection.ProgrammingError()

        self.isCommit = True

    def execute(self, query, *args):

        assert isinstance(query, str)

        if self.rowSets is not None:
            raise self.connection.ProgrammingError()
        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError()

        # Call the execute callback
        self.rowSets = self.connection.executeCallback(query, *args)
        assertRowSets(self.rowSets)

        return iter(self)

    def nextset(self):

        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError()
        if self.isCommit:
            raise self.connection.ProgrammingError()
        if self.rowSets is None or self.ixRowSet + 1 >= len(self.rowSets):
            raise self.connection.ProgrammingError()

        self.ixRowSet += 1
        self.ixRow = 0

    def fetchone(self):

        try:
            return self.next()
        except StopIteration:
            raise self.connection.ProgrammingError()

    def __iter__(self):

        return self

    def next(self):

        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError()
        if self.isCommit:
            raise self.connection.ProgrammingError()

        if self.ixRow >= len(self.rowSets[self.ixRowSet]):
            raise StopIteration

        rowSet = self.rowSets[self.ixRowSet]
        row = PyodbcRowMock(rowSet[0], rowSet[1][self.ixRow])
        self.ixRow += 1
        return row


# Simple execute callback
class SimpleExecuteCallback:

    def __init__(self):

        self.executes = {}

    def addRowSets(self, query, args, rowSets):

        assert isinstance(args, tuple)
        assertRowSets(rowSets)

        key = (query, args)
        if key not in self.executes:
            self.executes[key] = []
        self.executes[key].append(rowSets)

    def __call__(self, query, *args):

        key = (query, args)
        if key in self.executes and len(self.executes[key]) > 0:
            return self.executes[key].pop(0)
        else:
            raise PyodbcConnectionMock.DatabaseError()
