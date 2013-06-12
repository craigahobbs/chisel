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

import pyodbc


# pyodbc_connect resource type
class PyodbcConnectResourceType(object):
    __slots__ = ()

    @staticmethod
    def open(resourceString):
        return PyodbcConnectResource(resourceString)

    @staticmethod
    def close(resource):
        resource.close()


# pyodbc_connect resource
class PyodbcConnectResource(object):
    __slots__ = ('_connection')

    DatabaseError = pyodbc.DatabaseError
    DataError = pyodbc.DataError
    OperationalError = pyodbc.OperationalError
    IntegrityError = pyodbc.IntegrityError
    InternalError = pyodbc.InternalError
    ProgrammingError = pyodbc.ProgrammingError

    def __init__(self, resourceString):
        self._connection = pyodbc.connect(resourceString, autocommit = True, unicode_results = True)

    def close(self):
        self._connection.close()

    def cursor(self):
        return PyodbcCursorContext(self._connection.cursor())

    def execute(self, query, *args):
        return PyodbcCursorContext(self._connection.execute(query, *args))


# pyodbc cursor context manager
class PyodbcCursorContext(object):
    __slots__ = ('cursor')

    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
