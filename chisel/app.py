#
# Copyright (C) 2012-2013 Craig Hobbs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from . import api
from .compat import StringIO
from .model import Struct
from .spec import SpecParser

import json
import logging
import os
import re
import sys
import threading


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

        if self._resourceClose is not None:
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


# Top-level WSGI application class
class Application:

    # Environment variables
    ENV_CONFIG = "chisel.config"

    def __init__(self, wrapApplication = None, resourceTypes = None, configPath = None, scriptFilename = None):

        self._wrapApplication = wrapApplication
        self._resourceTypes = resourceTypes
        self._configPath = configPath
        self._scriptFilename = scriptFilename
        self._config = None
        self._api = None
        self._initLock = threading.Lock()

        # Initialize now if possible
        if configPath and scriptFilename:
            self._init(None)

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Initialize, if necessary
        self._init(environ)

        # Delegate to API application helper
        return self._api(environ, start_response)

    # Create the action context object
    def createContext(self, environ):

        # Initialize, if necessary
        self._init(environ)

        # Do the work...
        return self._createContext(environ)

    def _createContext(self, environ):

        # Create the logger
        logger = logging.getLoggerClass()("")
        logger.addHandler(logging.StreamHandler(environ.get("wsgi.errors")))
        logger.setLevel(self._getLogLevel(self._config))

        # Create the action context
        ctx = Struct()
        ctx.resources = self._resources
        ctx.config = self._config.config
        ctx.environ = environ
        ctx.log = logger
        return ctx

    def _init(self, environ):

        with self._initLock:

            # Already initialized?
            if self._api is not None and not self._config.alwaysReload:
                return

            # Base path for relative paths
            pathBaseFile = self._scriptFilename if self._scriptFilename else environ.get("SCRIPT_FILENAME")
            pathBase = os.path.dirname(pathBaseFile) if pathBaseFile else ""

            # Load the config file
            configPath = self._configPath if self._configPath else environ.get(self.ENV_CONFIG)
            if not os.path.isabs(configPath):
                configPath = os.path.join(pathBase, configPath)
            self._config = self.loadConfig(configPath)

            # Create the API application helper application
            self._api = api.Application(wrapApplication = self._wrapApplication,
                                        isPretty = self._config.prettyOutput,
                                        contextCallback = self._createContext,
                                        docCssUri = self._config.docCssUri)

            # Load specs and modules
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
                        raise Exception("Unknown resource type '%s'" % (resource.type,))

                    # Add the resource factory
                    self._resources[resource.name] = \
                        ResourceFactory(resource.name, resource.resourceString, resourceType[0])

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

    # Configuration key/value string pairs
    [optional] string{} config

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

        with open(configPath, "r") as fh:

            # Strip comments
            configString = cls._reComment.sub("", fh.read())

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
    def serve(cls, application):

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
            print(cls.configSpec)
            return

        # Stand-alone server WSGI entry point
        def application_simple_server(environ, start_response):
            wsgiref.util.setup_testing_defaults(environ)
            environ[cls.ENV_CONFIG] = os.path.abspath(opts.configPath)
            return application(environ, start_response)

        # Start the stand-alone server
        print("Serving on port %d..." % (opts.port,))
        httpd = wsgiref.simple_server.make_server('', opts.port, application_simple_server)
        httpd.serve_forever()

    # Call an action on this application
    def callAction(self, actionName, request, environ = None):

        # Serialize the request
        requestJson = json.dumps(request)

        # Call the action
        status, responseHeaders, responseString, wsgi_errors = \
            self.callRaw("POST", "/" + actionName, requestJson, environ = environ)

        # Deserialize the response
        try:
            response = json.loads(responseString)
        except:
            response = responseString

        return (status,
                responseHeaders,
                response,
                wsgi_errors)

    # Make an HTTP request on this application
    def callRaw(self, method, url, data = None, environ = None):

        # WSGI environment - used passed-in environ if its complete
        if (environ is not None and
            "REQUEST_METHOD" in environ and
            "PATH_INFO" in environ and
            "wsgi.input" in environ and
            "wsgi.errors" in environ):

            _environ = environ

        else:

            _environ = dict(environ) if environ else {}
            if "REQUEST_METHOD" not in _environ:
                _environ["REQUEST_METHOD"] = method
            if "PATH_INFO" not in _environ:
                _environ["PATH_INFO"] = url
            if "CONTENT_LENGTH" not in _environ and data is not None:
                _environ["CONTENT_LENGTH"] = str(len(data))
            if "wsgi.input" not in _environ:
                _environ["wsgi.input"] = StringIO(data if data is not None else "")
            if "wsgi.errors" not in _environ:
                _environ["wsgi.errors"] = StringIO()

        # Call the action
        startResponseArgs = {}
        def startResponse(status, responseHeaders):
            startResponseArgs["status"] = status
            startResponseArgs["responseHeaders"] = responseHeaders
        responseParts = self(_environ, startResponse)
        responseString = "".join(responseParts)

        return (startResponseArgs["status"],
                startResponseArgs["responseHeaders"],
                responseString,
                _environ["wsgi.errors"].getvalue())
