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

from .compat import basestring_, StringIO, wsgistr_, wsgistr_new, wsgistr_str
from .doc import DocAction
from .model import jsonDefault, Struct
from .request import Request
from .spec import SpecParser

from collections import namedtuple
import imp
import json
import logging
import os
import re
import sys
import threading
import traceback


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


# Application configuration file specification
ConfigSpec = """\
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

ConfigComment = re.compile("^\s*#.*$", flags = re.MULTILINE)

# Application configuration file model
ConfigParser = SpecParser()
ConfigParser.parseString(ConfigSpec)
ConfigModel = ConfigParser.types["ApplicationConfig"]


# Top-level WSGI application class
class Application(object):

    ThreadState = namedtuple("ThreadState", "environ, start_response, log")

    def __init__(self, configPath, wrapApplication = None, resourceTypes = None, logStream = sys.stderr):

        self._relPathBase = os.path.dirname(sys.modules[self.__module__].__file__)
        if isinstance(configPath, basestring_):
            self._configPath = configPath if os.path.isabs(configPath) else os.path.join(self._relPathBase, configPath)
            self._configString = None
        else:
            self._configPath = None
            self._configString = configPath.read()
        self._wrapApplication = wrapApplication
        self._resourceTypes = resourceTypes
        self._logStream = logStream
        self._threadStates = {}
        self._init()
        self._initLock = threading.Lock()

    def _init(self):

        # Read config file
        if self._configPath:
            with open(self._configPath, "r") as fConfig:
                self._configString = fConfig.read()
        self._config = Struct(ConfigModel.validate(json.loads(ConfigComment.sub("", self._configString))))

        # Load specs
        self._specParser = SpecParser()
        for specPath in self._config.specPaths:
            if not os.path.isabs(specPath):
                specPath = os.path.join(self._relPathBase, specPath)
            self.loadSpecs(specPath)

        # Load modules
        self._requests = {}
        self._requestUrls = {}
        for modulePath in self._config.modulePaths:
            if not os.path.isabs(modulePath):
                modulePath = os.path.join(self._relPathBase, modulePath)
            self.loadModules(modulePath)

        # Add the doc request
        if not self._config.disableDocs:
            self.addRequest(DocAction())

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

        # Default thread state
        self._threadStateDefault = self.ThreadState(None, None, self._createLogger(self._logStream))

    # Recursively load all specs in a directory
    def loadSpecs(self, specPath, specExt = ".chsl", finalize = True):

        # Does the path exist?
        if not os.path.isdir(specPath):
            raise IOError("%r not found or is not a directory" % (specPath,))

        # Resursively find spec files
        for dirpath, dirnames, filenames in os.walk(specPath):
            for filename in filenames:
                (base, ext) = os.path.splitext(filename)
                if ext == specExt:
                    self._specParser.parse(os.path.join(dirpath, filename), finalize = False)
        if finalize:
            self._specParser.finalize()

    # Load a spec string
    def loadSpecString(self, spec, fileName = "", finalize = True):
        self._specParser.parseString(spec, fileName = fileName, finalize = finalize)

    # Add a request handler (Request-wrapped WSGI application)
    def addRequest(self, request):

        # Wrap bare functions in a request decorator
        if not isinstance(request, Request):
            request = Request(request)

        # Duplicate request name?
        if request.name in self._requests:
            raise Exception("Redefinition of request '%s'" % (request.name,))
        self._requests[request.name] = request

        # Add the request URLs
        for url in request.urls:
            if url in self._requestUrls:
                raise Exception("Redefinition of request URL '%s'" % (url,))
            self._requestUrls[url] = request

        # Make the request app-aware at load-time
        request.onload(self)

    # Recursively load all modules in a directory
    def loadModules(self, moduleDir, moduleExt = ".py"):

        # Does the path exist?
        if not os.path.isdir(moduleDir):
            raise IOError("%r not found or is not a directory" % (moduleDir,))

        # Recursively find module files
        moduleDirNorm = os.path.normpath(moduleDir)
        modulePathParent = os.path.dirname(moduleDirNorm)
        modulePathBase = os.path.join(modulePathParent, "") if modulePathParent else modulePathParent
        for dirpath, dirnames, filenames in os.walk(moduleDirNorm):
            for filename in filenames:
                (base, ext) = os.path.splitext(filename)
                if ext == moduleExt:

                    # Load the module
                    module = None
                    moduleParts = []
                    for modulePart in os.path.join(dirpath, base)[len(modulePathBase):].split(os.sep):
                        moduleParts.append(modulePart)
                        moduleFp, modulePath, moduleDesc = \
                            imp.find_module(modulePart, module.__path__ if module else [modulePathParent])
                        try:
                            module = imp.load_module(".".join(moduleParts), moduleFp, modulePath, moduleDesc)
                        finally:
                            if moduleFp:
                                moduleFp.close()

                    # Add the module's requests
                    for moduleAttr in dir(module):
                        request = getattr(module, moduleAttr)
                        if isinstance(request, Request):
                            self.addRequest(request)

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Add the thread state
        threadKey = threading.current_thread().ident
        threadState = self.ThreadState(environ, start_response, self._createLogger(environ["wsgi.errors"]))
        self._threadStates[threadKey] = threadState

        # Handle the request
        try:
            # Reload, if requested
            if self._config.alwaysReload:
                with self._initLock:
                    self.log.info("Reloading application config...")
                    self._init()
                    return self.call(environ, start_response)
            else:
                return self.call(environ, start_response)
        finally:
            # Remove the thread state
            del self._threadStates[threadKey]

    # Overridable WSGI entry point
    def call(self, environ, start_response):

        # Find the matching request app and call it
        request = self._requestUrls.get(environ["PATH_INFO"])
        if request is not None:
            return request(environ, start_response)
        else:
            return self.response("404 Not Found", "text/plain", "Not Found")

    # Create a request logger
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

    # Retreive the WSGI thread state
    def _getThreadState(self):
        threadKey = threading.current_thread().ident
        return self._threadStates.get(threadKey, self._threadStateDefault)

    # Send an HTTP response
    def response(self, status, contentType, *content):

        # Ensure proper WSGI response data type
        content = [(wsgistr_new(s) if not isinstance(s, wsgistr_) else s) for s in content]

        # Build the headers array
        responseHeaders = [
            ("Content-Type", contentType),
            ("Content-Length", str(sum([len(s) for s in content])))
            ]

        # Return the response
        self._getThreadState().start_response(status, responseHeaders)
        return content

    # Serialize an object to JSON
    def serializeJSON(self, o):
        return json.dumps(o, sort_keys = True, default = jsonDefault,
                          indent = 2 if self._config.prettyOutput else None,
                          separators = (", ", ": ") if self._config.prettyOutput else (",", ":"))

    # Helper to create an error message from an exception
    def exceptionErrorMessage(self, e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        exc_path, exc_line = traceback.extract_tb(exc_tb)[-1][:2]
        return "%s:%d: %s" % (os.path.split(exc_path)[-1], exc_line, str(e))

    # Spec parser
    @property
    def specs(self):
        return self._specParser

    # Requests
    @property
    def requests(self):
        return self._requests

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

    # WSGI request start_response
    @property
    def start_response(self):
        return Struct(self._getThreadState().start_response)

    # Logger object
    @property
    def log(self):
        return self._getThreadState().log

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
            if "CONTENT_LENGTH" not in _environ:
                _environ["CONTENT_LENGTH"] = str(len(wsgiInput)) if wsgiInput else "0"
        if "wsgi.errors" not in _environ:
            _environ["wsgi.errors"] = StringIO()

        # Make the request
        startResponseArgs = {}
        def startResponse(status, responseHeaders):
            startResponseArgs["status"] = status
            startResponseArgs["responseHeaders"] = responseHeaders
        responseParts = self(_environ, startResponse)
        responseString = wsgistr_str(wsgistr_new("").join(responseParts))

        return (startResponseArgs["status"],
                startResponseArgs["responseHeaders"],
                responseString)

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
        if not application:
            if not opts.configPath:
                optParser.error("Configuration file path required")
            application = cls(os.path.abspath(opts.configPath))
        elif opts.configPath:
            application._configPath = opts.configPath
            application._configString = None
            application._init()

        # Stand-alone server WSGI entry point
        def application_simple_server(environ, start_response):
            wsgiref.util.setup_testing_defaults(environ)
            return application(environ, start_response)

        # Start the stand-alone server
        print("Serving on port %d..." % (opts.port,))
        httpd = wsgiref.simple_server.make_server("", opts.port, application_simple_server)
        httpd.serve_forever()
