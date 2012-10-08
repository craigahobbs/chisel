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


# Chisel application resource type
class ResourceType:

    def __init__(self, typeName, openFn, closeFn):

        self.typeName = typeName
        self.openFn = openFn
        self.closeFn = closeFn


# The chisel WSGI application
class ChiselApplication:

    def __init__(self, configPath = None, resourceTypes = None):

        # Config path
        if configPath is None:
            configPath = os.environ["CHISEL_CONFIG"]

        # API application helper context callback
        def contextCallback():
            ctx = Struct()
            ctx.resources = self._resources
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

        # Create resource factories
        self._resources = {}
        if self._config.resources:
            for resource in self._config.resources:

                # Find the resource type
                if resourceTypes:
                    resourceType = [resourceType for resourceType in resourceTypes if resourceType.typeName == resource.type]
                else:
                    resourceType = []
                if not resourceType:
                    raise Exception("Resource type '%s' not found" % (resource.type))

                # Add the resource factory
                self._resources[resource.name] = self._ResourceFactory(resource.name, resourceType[0], resource.resourceString)

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Delegate to API application helper
        return self._api(environ, start_response)

    # Configuration file specification
    configSpec = """\
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

    # General application configuration (default is false)
    [optional] bool isDebug

    # External CSS for generated documenation HTML
    [optional] string docCssUri

    # Resources
    [optional] Resource[] resources
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
    @staticmethod
    def serve(resourceTypes = None):

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
        application = ChiselApplication(configPath = opts.configPath, resourceTypes = resourceTypes)
        def application_simple_server(environ, start_response):
            setup_testing_defaults(environ)
            return application(environ, start_response)

        # Start the stand-alone server
        print "Serving on port %d..." % (opts.port)
        httpd = make_server('', opts.port, application_simple_server)
        httpd.serve_forever()
