#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from ..app import ResourceType


# pyodbc.connect resource type mock
class PyodbcConnectResourceTypeMock(ResourceType):

    def __init__(self, executeCallback, autocommit = True):

        self._executeCallback = executeCallback
        self.autocommit = autocommit
        resourceTypeName = "pyodbc_connect" if autocommit else "pyodbc_connect_noautocommit"
        ResourceType.__init__(self, resourceTypeName, self._open, self._close)

    def _open(self, resourceString):

        return None

    def _close(self, resource):

        resource.close()
