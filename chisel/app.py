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

    def __init__(self, resourceTypeName, resourceOpen, resourceClose):

        self._resourceTypeName = resourceTypeName
        self._resourceOpen = resourceOpen
        self._resourceClose = resourceClose

    @property
    def name(self):

        return self._resourceTypeName

    def open(self, resourceString):

        return self._resourceOpen(resourceString)

    def close(self, resource):

        return self._resourceClose(resource)


# Resource factory - create a resource context manager
class ResourceFactory:

    def __init__(self, name, resourceString, resourceType):

        self._name = name
        self._resourceString = resourceString
        self._resourceType = resourceType

    def __call__(self):

        return ResourceContext(self)

    def _open(self):

        return self._resourceType.open(self._resourceString)

    def _close(self, resource):

        return self._resourceType.close(resource)


# Resource context manager
class ResourceContext:

    def __init__(self, resourceFactory):

        self._resourceFactory = resourceFactory

    def __enter__(self):

        self._resource = self._resourceFactory._open()
        return self._resource

    def __exit__(self, exc_type, exc_value, traceback):

        self._resourceFactory._close(self._resource)


# Cache factory - create a cache context manager
class CacheFactory:

    def __init__(self):

        self._cache = {}
        self._cacheLock = threading.Lock()

    def __call__(self, name):

        # Get the cache - create if necessary
        with self._cacheLock:
            cache = self._cache.get(name)
            if cache is None:
                cache = CacheContext()
                self._cache[name] = cache
        return cache


# Cache context manager
class CacheContext:

    def __init__(self):

        self._cache = Struct()
        self._cacheLock = threading.Lock()

    def __enter__(self):

        self._cacheLock.acquire()
        return self._cache

    def __exit__(self, exc_type, exc_value, traceback):

        self._cacheLock.release()


# Top-level WSGI application class
class Application:

    # Environment variables
    ENV_CONFIG = "chisel.config"

    def __init__(self, resourceTypes = None, configString = None, configPath = None):

        self._resourceTypes = resourceTypes
        self._configString = configString
        self._configPath = configPath
        self._config = None
        self._api = None
        self._initLock = threading.Lock()
        self._cache = CacheFactory()

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Initialize, if necessary
        self._init(environ)

        # Delegate to API application helper
        return self._api(environ, start_response)

    def _init(self, environ):

        with self._initLock:

            # Already initialized?
            if self._api is not None and not self._config.alwaysReload:
                return

            # Load the config file
            if self._configString:
                self._config = self.loadConfigString(self._configString)
            else:
                configPath = self._configPath if self._configPath else environ[self.ENV_CONFIG]
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
                        resourceType = [resourceType for resourceType in self._resourceTypes if resourceType.name == resource.type]
                    else:
                        resourceType = []
                    if not resourceType:
                        raise Exception("Unknown resource type '%s'" % (resource.type))

                    # Add the resource factory
                    self._resources[resource.name] = \
                        ResourceFactory(resource.name, resource.resourceString, resourceType[0])

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
    _configParser = SpecParser()
    _configParser.parseString(configSpec)
    _configModel = _configParser.types["ApplicationConfig"]
    _reComment = re.compile("^\s*#.*$", flags = re.MULTILINE)

    # Load the configuration file
    @classmethod
    def loadConfig(cls, configPath):

        with open(configPath, "rb") as fh:
            return cls.loadConfigString(fh.read())

    # Load the configuration string
    @classmethod
    def loadConfigString(cls, configString):

        # Strip comments
        configString = cls._reComment.sub("", configString)

        # Parse and validate the config string
        return Struct(cls._configModel.validate(json.loads(configString)))

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
