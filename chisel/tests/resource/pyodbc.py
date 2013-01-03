#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#


# Mock pyodbc.Connection
class Connection:

    def __init__(self, connectionString, autocommit = True):

        self.connectionString = connectionString
        self.autocommit = autocommit
        self.isClosed = False

    def close(self):

        self.isClosed = True


# Mock pyodbc.connect
def connect(connectionString, autocommit = True):

    return Connection(connectionString, autocommit = autocommit)
