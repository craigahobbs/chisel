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

import pyodbc


# pyodbc_connect resource type
class PyodbcConnectResourceType(ResourceType):

    def __init__(self, autocommit = True):

        self.autocommit = autocommit
        resourceTypeName = "pyodbc_connect" if autocommit else "pyodbc_connect_noautocommit"
        ResourceType.__init__(self, resourceTypeName, self._open, self._close)

    def _open(self, resourceString):

        return PyodbcConnectResource(resourceString, self.autocommit)

    def _close(self, resource):

        resource.close()


# pyodbc_connect resource
class PyodbcConnectResource:

    DatabaseError = pyodbc.DatabaseError
    DataError = pyodbc.DataError
    OperationalError = pyodbc.OperationalError
    IntegrityError = pyodbc.IntegrityError
    InternalError = pyodbc.InternalError
    ProgrammingError = pyodbc.ProgrammingError

    def __init__(self, resourceString, autocommit):

        self._connection = pyodbc.connect(resourceString, autocommit = autocommit)

    def close(self):

        self._connection.close()

    def cursor(self):

        return self._connection.cursor()

    def execute(self, query, *args):

        return self._connection.execute(query, *args)
