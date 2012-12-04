#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import json
import logging
import os
import re
import threading

import api
from .model import Struct
from .spec import SpecParser


# Application resource type
class ResourceType:

    def __init__(self, typeName, openFn, closeFn):

        self.typeName = typeName
        self.openFn = openFn
        self.closeFn = closeFn


# Resource factory - create a resource context manager
class ResourceFactory:

    def __init__(self, name, resourceType, resourceString):

        self._name = name
        self._resourceType = resourceType
        self._resourceString = resourceString

    def __call__(self):

        return ResourceContext(self._resourceType.openFn(self._resourceString), self._resourceType)


# Resource context manager
class ResourceContext:

    def __init__(self, resource, resourceType):

        self._resource = resource
        self._resourceType = resourceType

    def __enter__(self):

        return self._resource

    def __exit__(self, exc_type, exc_value, traceback):

        self._resourceType.closeFn(self._resource)


# Cache context manager
class Cache:

    def __init__(self):

        self._cache = Struct()
        self._cacheLock = threading.Lock()

    def __call__(self):

        return self

    def __enter__(self):

        self._cacheLock.acquire()
        return self._cache

    def __exit__(self, exc_type, exc_value, traceback):

        self._cacheLock.release()


# Top-level WSGI application class
class Application:

    # Environment variables
    ENV_CONFIG = "chisel.config"

    def __init__(self, resourceTypes = None):

        self._resourceTypes = resourceTypes
        self._config = None
        self._api = None
        self._initLock = threading.Lock()
        self._cache = Cache()

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Initialize, if necessary
        with self._initLock:
            self._init(environ)

        # Delegate to API application helper
        return self._api(environ, start_response)

    def _init(self, environ):

        # Already initialized?
        if self._api is not None and not self._config.alwaysReload:
            return

        # Load the config file
        configPath = environ[self.ENV_CONFIG]
        self._config = self.loadConfig(configPath)

        # Create the API application helper application
        self._api = api.Application(isPretty = self._config.prettyOutput,
                                    contextCallback = self._contextCallback,
                                    docCssUri = self._config.docCssUri)

        # Load specs and modules
        pathBase = os.path.dirname(environ["SCRIPT_FILENAME"])
        for specPath in self._config.specPaths:
            if not os.path.isabs(specPath):
                specPath = os.path.join(pathBase, specPath)
            self._api.loadSpecs(specPath)
        for modulePath in self._config.modulePaths:
            if not os.path.isabs(modulePath):
                modulePath = os.path.join(pathBase, modulePath)
            self._api.loadModules(modulePath)

        # Create resource factories
        self._resources = {}
        if self._config.resources:
            for resource in self._config.resources:

                # Find the resource type
                if self._resourceTypes:
                    resourceType = [resourceType for resourceType in self._resourceTypes if resourceType.typeName == resource.type]
                else:
                    resourceType = []
                if not resourceType:
                    raise Exception("Unknown resource type '%s'" % (resource.type))

                # Add the resource factory
                self._resources[resource.name] = ResourceFactory(resource.name, resourceType[0], resource.resourceString)

    # API application helper context callback
    def _contextCallback(self, environ):

        # Create the logger
        logger = logging.getLoggerClass()("")
        logger.addHandler(logging.StreamHandler(environ.get("wsgi.errors")))
        logger.setLevel(self._getLogLevel(self._config))

        # Create the action context
        ctx = Struct()
        ctx.resources = self._resources
        ctx.environ = environ
        ctx.log = logger
        ctx.cache = self._cache
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

# Application configuration file
struct ApplicationConfig

    # Specification directories (top-level only)
    string[] specPaths

    # Module directories (top-level only)
    string[] modulePaths

    # Resources
    [optional] Resource[] resources

    # Logger output level (default is Warning)
    [optional] LogLevel logLevel

    # Pretty JSON output (default is False)
    [optional] bool prettyOutput

    # Re-load specs and scripts on every requests (development mode)
    [optional] bool alwaysReload

    # External CSS for generated documenation HTML
    [optional] string docCssUri
"""

    # Load the configuration file
    @classmethod
    def loadConfig(cls, configPath):

        # Create the configuration file model
        configParser = SpecParser()
        configParser.parseString(cls.configSpec)
        configModel = configParser.types["ApplicationConfig"]

        # Read the config file and strip comments
        with open(configPath, "rb") as fh:
            config = fh.read()
        reComment = re.compile("^\s*#.*$", flags = re.MULTILINE)
        config = reComment.sub("", config)

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

    # Run as stand-alone server
    @classmethod
    def serve(cls, application, scriptFilename):

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
        def application_simple_server(environ, start_response):
            wsgiref.util.setup_testing_defaults(environ)
            if "SCRIPT_FILENAME" not in environ:
                environ["SCRIPT_FILENAME"] = os.path.abspath(scriptFilename)
            environ[cls.ENV_CONFIG] = os.path.abspath(opts.configPath)
            return application(environ, start_response)

        # Start the stand-alone server
        print "Serving on port %d..." % (opts.port)
        httpd = wsgiref.simple_server.make_server('', opts.port, application_simple_server)
        httpd.serve_forever()
