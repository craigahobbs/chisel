#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#


# Mock pyodbc exceptions
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


# Mock pyodbc.Connection
class Connection:

    def __init__(self, connectionString, autocommit = True):

        self.connectionString = connectionString
        self.autocommit = autocommit
        self.isClosed = False

    def close(self):

        self.isClosed = True

    def cursor(self):

        return None

    def execute(self, query, *args):

        return None


# Mock pyodbc.connect
def connect(connectionString, autocommit = True):

    return Connection(connectionString, autocommit = autocommit)
