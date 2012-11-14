#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import json
import logging
import os
import re

import api
from .model import Struct
from .spec import SpecParser


# Chisel application resource type
class ResourceType:

    def __init__(self, typeName, openFn, closeFn):

        self.typeName = typeName
        self.openFn = openFn
        self.closeFn = closeFn


# The chisel WSGI application
class Application:

    def __init__(self, configPath = None, resourceTypes = None):

        # Load the config file
        if configPath is None:
            configPath = os.environ["CHISEL_CONFIG"]
        config = self.loadConfig(configPath)
        self._logLevel = self._getLogLevel(config)

        # Create the API application helper application
        self._api = api.Application(isPretty = config.prettyOutput,
                                    contextCallback = self._contextCallback,
                                    docCssUri = config.docCssUri)
        for specPath in config.specPaths:
            self._api.loadSpecs(specPath)
        for modulePath in config.modulePaths:
            self._api.loadModules(modulePath)

        # Create resource factories
        self._resources = {}
        if config.resources:
            for resource in config.resources:

                # Find the resource type
                if resourceTypes:
                    resourceType = [resourceType for resourceType in resourceTypes if resourceType.typeName == resource.type]
                else:
                    resourceType = []
                if not resourceType:
                    raise Exception("Unknown resource type '%s'" % (resource.type))

                # Add the resource factory
                self._resources[resource.name] = self._ResourceFactory(resource.name, resourceType[0], resource.resourceString)

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Delegate to API application helper
        return self._api(environ, start_response)

    # API application helper context callback
    def _contextCallback(self, environ):

        # Create the logger
        logger = logging.getLoggerClass()("")
        logger.addHandler(logging.StreamHandler(environ.get("wsgi.errors")))
        logger.setLevel(self._logLevel)

        # Create the action context
        ctx = Struct()
        ctx.resources = self._resources
        ctx.environ = environ
        ctx.log = logger
        return ctx

    # Configuration file specification
    configSpec = """\
# Log level
enum LogLevel
    Debug
    Info
    Warning
    Error

# Resource description
struct Resource

    # Resource name
    string name

    # Resource type
    string type

    # Resource string (e.g. connection string)
    string resourceString

# The chisel application configuration file
struct ChiselConfig

    # Specification directories (top-level only)
    string[] specPaths

    # Module directories (top-level only)
    string[] modulePaths

    # Pretty JSON output (default is False)
    [optional] bool prettyOutput

    # Logger output level (default is Warning)
    [optional] LogLevel logLevel

    # External CSS for generated documenation HTML
    [optional] string docCssUri

    # Resources
    [optional] Resource[] resources
"""

    # Load the configuration file
    @classmethod
    def loadConfig(cls, configPath):

        # Create the configuration file model
        configParser = SpecParser()
        configParser.parse(cls.configSpec)
        configParser.finalize()
        configModel = configParser.model.types["ChiselConfig"]

        # Read the config file and strip comments
        with open(configPath, "rb") as fh:
            config = fh.read()
        config = re.sub("^\s*#.*$", "", config, flags = re.MULTILINE)

        # Load the config file
        return configModel.validate(Struct(json.loads(config)))

    # Get the Python logging level
    def _getLogLevel(self, configSpec):

        if configSpec.logLevel == "Debug":
            return logging.DEBUG
        elif configSpec.logLevel == "Info":
            return logging.INFO
        elif configSpec.logLevel == "Error":
            return logging.ERROR
        else:
            return logging.WARNING

    # Resource factory - create a resource context manager
    class _ResourceFactory:

        def __init__(self, name, resourceType, resourceString):

            self._name = name
            self._resourceType = resourceType
            self._resourceString = resourceString

        def __call__(self):

            return self.ResourceContext(self._resourceType.openFn(self._resourceString), self._resourceType)

        # Resource context manager
        class ResourceContext:

            def __init__(self, resource, resourceType):

                self._resource = resource
                self._resourceType = resourceType

            def __enter__(self):

                return self._resource

            def __exit__(self, exc_type, exc_value, traceback):

                self._resourceType.closeFn(self._resource)

    # Run as stand-alone server
    @classmethod
    def serve(cls, resourceTypes = None):

        import optparse
        import wsgiref.util
        import wsgiref.simple_server

        # Command line options
        optParser = optparse.OptionParser()
        optParser.add_option("-c", dest = "configPath", metavar = "PATH",
                             help = "Path to configuration file")
        optParser.add_option("-p", dest = "port", type = "int", default = 8080,
                             help = "Server port (default is 8080)")
        optParser.add_option("--config-spec", dest = "configSpec", action = "store_true",
                             help = "Dump configuration file specification")
        (opts, args) = optParser.parse_args()
        if not opts.configPath:
            optParser.error("Configuration file path required")

        # Dump configuration specification
        if opts.configSpec:
            print cls.configSpec
            return

        # Stand-alone server WSGI entry point
        application = cls(configPath = opts.configPath, resourceTypes = resourceTypes)
        def application_simple_server(environ, start_response):
            wsgiref.util.setup_testing_defaults(environ)
            return application(environ, start_response)

        # Start the stand-alone server
        print "Serving on port %d..." % (opts.port)
        httpd = wsgiref.simple_server.make_server('', opts.port, application_simple_server)
        httpd.serve_forever()
