#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
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

        self._connection = pyodbc.connect(resourceString, autocommit)

    def close(self):

        self._connection.close()

    def cursor(self):

        return self._connection.cursor()

    def execute(self, query, *args):

        return self._connection.execute(query, *args)
