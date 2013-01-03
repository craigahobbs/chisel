#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from ..app import ResourceType


# pyodbc.connect resource type mock
class PyodbcConnectResourceTypeMock(ResourceType):

    def __init__(self, executeCallback):

        self._executeCallback = executeCallback
        ResourceType.__init__(self, "pyodbc_connect", self._open, self._close)

    def _open(self, resourceString):

        return None

    def _close(self, resource):

        resource.close()
