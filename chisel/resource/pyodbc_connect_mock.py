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

from ..app import ResourceType
from ..compat import long_

import datetime
import decimal


# pyodbc_connect resource type mock
class PyodbcConnectResourceTypeMock(ResourceType):

    # executeCallback(resourceString, query, *args), returns [(columnNames, columnDatas), ...]
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

    class Error(Exception):
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
            raise self.ProgrammingError("Attempt to close an already-closed connection")

        self.isClosed = True

    def cursor(self):

        if self.isClosed:
            raise self.ProgrammingError("Attempt to get a cursor on an already-closed connection")

        return PyodbcCursorMock(self)

    def execute(self, query, *args):

        if self.isClosed:
            raise self.ProgrammingError("Attempt to execute with an already-closed connection")

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
            raise PyodbcConnectionMock.ProgrammingError("Attempt to get invalid row column index %r" % (ixColumn,))

    def __getattr__(self, columnName):

        try:
            ixColumn = self.columnNames.index(columnName)
            return self.columnData[ixColumn]
        except:
            raise PyodbcConnectionMock.ProgrammingError("Attempt to get invalid row column name %r" % (columnName,))

    def __nonzero__(self):

        return True


# Assert rowSets is properly formed - [(columnNames, columnDatas), ...]
def assertRowSets(rowSets):

    assert isinstance(rowSets, (tuple, list)), \
        "Invalid rowset collection %r - list expected" % (rowSets,)
    for rowSet in rowSets:
        assert isinstance(rowSet[0], (tuple)), \
            "Invalid rowset %r - tuple expected" % (rowSet,)
        assert len(rowSet) == 2, \
            "Invalid rowset %r - rowset should have only two elements" % (rowSet,)
        assert isinstance(rowSet[0], (tuple)), \
            "Invalid column names collection %r - tuple expected" % (rowSet[1],)
        for columnName in rowSet[0]:
            assert isinstance(columnName, str), \
                "Invalid column name %r - string expected" % (columnName,)
        assert isinstance(rowSet[1], (tuple, list)), \
            "Invalid rows collection %r - list expected" % (rowSet[1],)
        for columnData in rowSet[1]:
            assert isinstance(columnData, (tuple, list)), \
                "Invalid row %r - tuple expected" % (columnData,)
            assert len(rowSet[0]) == len(columnData), \
                "Column data tuple has different length than column names tuple (%r, %r)" % (rowSet[0], columnData)
            for data in columnData:
                assert isinstance(data, (type(None),
                                         str,
                                         bytearray,
                                         bool,
                                         datetime.date,
                                         datetime.time,
                                         datetime.datetime,
                                         int,
                                         long_,
                                         float,
                                         decimal.Decimal)), \
                                         "Invalid column data %r" % (data,)


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
            raise self.connection.ProgrammingError("Attempt to close an already-closed cursor")

        self.isClosed = True

    def commit(self):

        if self.connection.autocommit:
            raise self.connection.ProgrammingError("Attempt to commit an autocommit cursor")
        if self.rowSets is None:
            raise self.connection.ProgrammingError("Attempt to commit cursor before execute")
        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError("Attempt to commit an already-closed cursor")
        if self.isCommit:
            raise self.connection.ProgrammingError("Attempt to commit an already-committed cursor")

        self.isCommit = True

    def execute(self, query, *args):

        assert isinstance(query, str)

        if self.rowSets is not None:
            raise self.connection.ProgrammingError("Attempt to execute on an already-executed-on cursor")
        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError("Attempt to execute on a closed cursor")

        # Call the execute callback
        self.rowSets = self.connection.executeCallback(self.connection.resourceString, query, *args)
        assertRowSets(self.rowSets)

        return iter(self)

    def nextset(self):

        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError("Attempt to call nextset on a closed cursor")
        if self.isCommit:
            raise self.connection.ProgrammingError("Attempt to call nextset on a committed cursor")
        if self.rowSets is None or self.ixRowSet + 1 >= len(self.rowSets):
            raise self.connection.ProgrammingError("Attempt to call nextset when no more row sets available")

        self.ixRowSet += 1
        self.ixRow = 0

    def fetchone(self):

        try:
            return self.__next__()
        except StopIteration:
            return None

    def __iter__(self):

        return self

    def __next__(self):

        if self.isClosed or self.connection.isClosed:
            raise self.connection.ProgrammingError("Attempt to iterate a closed cursor")
        if self.isCommit:
            raise self.connection.ProgrammingError("Attempt to iterate a committed cursor")
        if self.rowSets is None:
            raise self.connection.ProgrammingError("Attempt to iterate a cursor before execute")

        if self.ixRowSet >= len(self.rowSets) or self.ixRow >= len(self.rowSets[self.ixRowSet][1]):
            raise StopIteration

        rowSet = self.rowSets[self.ixRowSet]
        row = PyodbcRowMock(rowSet[0], rowSet[1][self.ixRow])
        self.ixRow += 1
        return row

    def next(self):

        return self.__next__()


# Simple execute callback
class SimpleExecuteCallback:

    def __init__(self):

        self.executes = {}
        self.executeCount = 0

    def addRowSets(self, resourceString, query, args, rowSets):

        assert isinstance(args, tuple)
        assertRowSets(rowSets)

        key = (resourceString, query, args)
        if key not in self.executes:
            self.executes[key] = []
        self.executes[key].append(rowSets)

    def __call__(self, resourceString, query, *args):

        key = (resourceString, query, args)
        if key in self.executes and len(self.executes[key]) > 0:
            self.executeCount += 1
            return self.executes[key].pop(0)
        else:
            raise PyodbcConnectionMock.DatabaseError("No row sets for %r" % (key,))
