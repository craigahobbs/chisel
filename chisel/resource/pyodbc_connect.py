#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from ..app import ResourceType

import pyodbc


# pyodbc.connect resource type
class PyodbcConnectResourceType(ResourceType):

    def __init__(self, autocommit = True):

        self.autocommit = autocommit
        resourceTypeName = "pyodbc_connect" if autocommit else "pyodbc_connect_noautocommit"
        ResourceType.__init__(self, resourceTypeName, self._open, self._close)

    def _open(self, resourceString):

        return pyodbc.connect(resourceString, autocommit = self.autocommit)

    def _close(self, resource):

        resource.close()
