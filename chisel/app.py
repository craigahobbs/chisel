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
from .compat import StringIO, wsgistr_, wsgistr_new, wsgistr_str
from .model import Struct
from .spec import SpecParser

from collections import namedtuple
import json
import logging
import os
import re
import sys
import threading


# Application resource type
class ResourceType(object):

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
class ResourceFactory(object):

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
class ResourceContext(object):

    def __init__(self, resourceFactory):
        self._resourceFactory = resourceFactory

    def __enter__(self):
        self._resource = self._resourceFactory._open()
        return self._resource

    def __exit__(self, exc_type, exc_value, traceback):
        self._resourceFactory._close(self._resource)


# Top-level WSGI application class
class Application(object):

    _singleton = None
    _logger = logging.getLoggerClass()("")
    _logger.addHandler(logging.StreamHandler(sys.stderr))
    _logger.setLevel(logging.WARNING)

    @classmethod
    def getApp(cls):
        return cls._singleton

    @classmethod
    def getLogger(cls):
        return cls._singleton.log if cls._singleton else cls._logger

    ThreadState = namedtuple("ThreadState", "environ, log")

    def __init__(self, configPath, wrapApplication = None, resourceTypes = None, logStream = sys.stderr):

        self._wrapApplication = wrapApplication
        self._resourceTypes = resourceTypes

        # Base path for relative paths
        pathBaseFile = sys.modules[self.__module__].__file__
        pathBase = os.path.dirname(pathBaseFile) if pathBaseFile else ""

        # Load the config file
        if not os.path.isabs(configPath):
            configPath = os.path.join(pathBase, configPath)
        self._config = self.loadConfig(configPath)

        # Environment collection
        self._threadStates = {}
        self._threadStateDefault = self.ThreadState(None, self._createLogger(logStream))

        # Create the API application helper application
        self._api = api.Application(wrapApplication = self._wrapApplication,
                                    isPretty = self._config.prettyOutput,
                                    contextCallback = lambda environ: self,
                                    docUriDir = None if self._config.disableDocs else "doc",
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

        # Set the application singleton
        Application._singleton = self

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Add the thread state
        threadKey = threading.current_thread().ident
        self._threadStates[threadKey] = self.ThreadState(environ, self._createLogger(environ["wsgi.errors"]))

        # Handle the request
        try:
            return self.call(environ, start_response)
        finally:
            # Remove the thread state
            del self._threadStates[threadKey]

    # Overridable WSGI entry point
    def call(self, environ, start_response):
        return self._api(environ, start_response)

    # Serialize a JSON object
    def serializeJSON(self, o):
        return self._api.serializeJSON(o)

    def _createLogger(self, logStream):
        logger = logging.getLoggerClass()("")
        if logStream:
            logger.addHandler(logging.StreamHandler(logStream))
        if self._config.logLevel == "Debug":
            logger.setLevel(logging.DEBUG)
        elif self._config.logLevel == "Info":
            logger.setLevel(logging.INFO)
        elif self._config.logLevel == "Error":
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.WARNING)
        return logger

    def _getThreadState(self):
        threadKey = threading.current_thread().ident
        return self._threadStates.get(threadKey, self._threadStateDefault)

    # Resources collection
    @property
    def resources(self):
        return Struct(self._resources)

    # Application-specific configuration values
    @property
    def config(self):
        return self._config.config

    # WSGI request environ
    @property
    def environ(self):
        return Struct(self._getThreadState().environ)

    # Logger object
    @property
    def log(self):
        return self._getThreadState().log

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

    # Pretty JSON output (default is false)
    [optional] bool prettyOutput

    # Re-load specs and scripts on every requests (default is false)
    [optional] bool alwaysReload

    # Disable documentation (default is false)
    [optional] bool disableDocs

    # External CSS for generated documenation HTML (default is None)
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

    # Make an HTTP request on this application
    def request(self, requestMethod, pathInfo, queryString = None, wsgiInput = None, environ = None):

        # WSGI environment - used passed-in environ if its complete
        _environ = dict(environ) if environ else {}
        _environ["REQUEST_METHOD"] = requestMethod
        _environ["PATH_INFO"] = pathInfo
        if "SCRIPT_NAME" not in _environ:
            _environ["SCRIPT_NAME"] = ""
        if "QUERY_STRING" not in _environ:
            _environ["QUERY_STRING"] = queryString if queryString else ""
        if "wsgi.input" not in _environ:
            _environ["wsgi.input"] = StringIO(wsgiInput if wsgiInput else "")
            _environ["CONTENT_LENGTH"] = str(len(wsgiInput)) if wsgiInput else "0"
        if "wsgi.errors" not in _environ:
            _environ["wsgi.errors"] = StringIO()

        # Call the action
        startResponseArgs = {}
        def startResponse(status, responseHeaders):
            startResponseArgs["status"] = status
            startResponseArgs["responseHeaders"] = responseHeaders
        responseParts = self(_environ, startResponse)
        responseString = wsgistr_str(wsgistr_new("").join(responseParts))

        return (startResponseArgs["status"],
                startResponseArgs["responseHeaders"],
                responseString,
                _environ["wsgi.errors"].getvalue())

    # Run as stand-alone server
    @classmethod
    def serve(cls, application = None, configPath = None):

        import optparse
        import wsgiref.util
        import wsgiref.simple_server

        # Command line options
        optParser = optparse.OptionParser()
        optParser.add_option("-c", dest = "configPath", metavar = "PATH", default = configPath,
                             help = "Path to configuration file")
        optParser.add_option("-p", dest = "port", type = "int", default = 8080,
                             help = "Server port (default is 8080)")
        optParser.add_option("--config-spec", dest = "configSpec", action = "store_true",
                             help = "Dump configuration file specification")
        (opts, args) = optParser.parse_args()

        # Dump configuration specification
        if opts.configSpec:
            print(cls.configSpec)
            return

        # Create the application instance
        if application is None:
            if not opts.configPath:
                optParser.error("Configuration file path required")
            application = cls(opts.configPath)

        # Stand-alone server WSGI entry point
        def application_simple_server(environ, start_response):
            wsgiref.util.setup_testing_defaults(environ)
            return application(environ, start_response)

        # Start the stand-alone server
        print("Serving on port %d..." % (opts.port,))
        httpd = wsgiref.simple_server.make_server("", opts.port, application_simple_server)
        httpd.serve_forever()
