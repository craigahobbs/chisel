#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import json
import os

from .model import Struct
from .spec import SpecParser
from .server import Application


# The chisel WSGI application
class ChiselApplication:

    def __init__(self, configPath = None):

        # Config path
        if configPath is None:
            configPath = os.environ["CHISEL_CONFIG"]

        # API application helper context callback
        def contextCallback():
            ctx = Struct()
            ctx.odbc = self._pyodbc
            return ctx

        # Create the API application helper application
        self._config = self.loadConfig(configPath)
        self._api = Application(isDebug = self._config.isDebug if self._config.isDebug is not None else False,
                                contextCallback = contextCallback,
                                docCssUri = self._config.docCssUri)
        for specPath in self._config.specPaths:
            self._api.loadSpecs(specPath)
        for modulePath in self._config.modulePaths:
            self._api.loadModules(modulePath)

        # Create pyodbc connections
        self._pyodbc = {}
        if self._config.odbcConnections:
            import pyodbc
            for odbcConnection in self._config.odbcConnections:
                self._pyodbc[odbcConnection.name] = pyodbc.connect(odbcConnection.connectionString)

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Delegate to API application helper
        return self._api(environ, start_response)

    # Configuration file specification
    configSpec = """\
# pyodbc connections
struct ODBCConnection

    # Connection name
    string name

    # pyodbc connection string - see http://code.google.com/p/pyodbc/wiki/ConnectionStrings
    string connectionString

# The chisel application configuration file model
struct ChiselConfig

    # Specification directories (top-level only)
    string[] specPaths

    # Module directories (top-level only)
    string[] modulePaths

    # General application configuration (default is false)
    [optional] bool isDebug

    # External CSS for generated documenation HTML
    [optional] string docCssUri

    # pyodbc connections
    [optional] ODBCConnection[] odbcConnections
"""

    # Load the configuration file
    @staticmethod
    def loadConfig(configPath):

        # Create the configuration file model
        configParser = SpecParser()
        configParser.parse(ChiselApplication.configSpec)
        configParser.finalize()
        configModel = configParser.model.types["ChiselConfig"]

        # Load the config file
        with open(configPath, "rb") as fh:
            return configModel.validate(Struct(json.load(fh)))

    # Run as stand-alone server
    @staticmethod
    def serve():

        import optparse
        from wsgiref.util import setup_testing_defaults
        from wsgiref.simple_server import make_server

        # Command line options
        optParser = optparse.OptionParser()
        optParser.add_option("-c", dest = "configPath", metavar = "PATH",
                             help = "Path to configuration file")
        optParser.add_option("-p", dest = "port", type = "int", default = 8080,
                             help = "Server port (default is 8080)")
        optParser.add_option("--config-spec", dest = "configSpec", action = "store_true",
                             help = "Dump configuration file specification")
        (opts, args) = optParser.parse_args()

        # Dump configuration specification
        if opts.configSpec:
            print ChiselApplication.configSpec
            return

        # Stand-alone server WSGI entry point
        application = ChiselApplication(opts.configPath)
        def application_simple_server(environ, start_response):
            setup_testing_defaults(environ)
            return application(environ, start_response)

        # Start the stand-alone server
        print "Serving on port %d..." % (opts.port)
        httpd = make_server('', opts.port, application_simple_server)
        httpd.serve_forever()
