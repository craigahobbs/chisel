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

from .compat import json, StringIO, wsgistr_, wsgistr_new, wsgistr_str
from .doc import DocAction
from .request import Request
from .resource.base import ResourceCollection
from .spec import SpecParser

from collections import namedtuple
import imp
import logging
import os
import sys
import threading


# Top-level WSGI application class
class Application(object):

    ENVIRON_APP = "chisel.app"

    ThreadState = namedtuple("ThreadState", ("environ", "start_response", "log"))

    def __init__(self, logStream = sys.stderr):

        self.logLevel = logging.WARNING
        self.prettyOutput = False
        self.alwaysReload = False
        self.__logStream = logStream
        self.__threadStates = {}
        self.__threadStateDefault = self.ThreadState(None, None, self.__createLogger(self.__logStream))
        self.__initLock = threading.Lock()
        self.__init()

    def __init(self):

        self.__specParser = SpecParser()
        self.__requests = {}
        self.__requestUrls = {}
        self.__resources = ResourceCollection()
        self.__threadStateDefault = self.ThreadState(None, None, self.__createLogger(self.__logStream))
        self.init()

    # Overridable initialization function
    def init(self):

        pass

    # Overridable WSGI entry point
    def call(self, environ, start_response):

        request = self.__requestUrls.get(environ["PATH_INFO"])
        if request is not None:
            return request(environ, start_response)
        else:
            return self.response("404 Not Found", "text/plain", "Not Found")

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Set the app environment item
        environ[self.ENVIRON_APP] = self

        # Add the thread state
        threadKey = threading.current_thread().ident
        threadState = self.ThreadState(environ, start_response, self.__createLogger(environ["wsgi.errors"]))
        self.__threadStates[threadKey] = threadState

        # Handle the request - re-initialize if necessary
        try:
            if self.alwaysReload:
                with self.__initLock:
                    self.__init()
                    return self.call(environ, start_response)
            else:
                return self.call(environ, start_response)
        finally:
            # Remove the thread state
            del self.__threadStates[threadKey]

    # Create a request logger
    def __createLogger(self, logStream):
        logger = logging.getLoggerClass()("")
        logger.setLevel(self.logLevel)
        if logStream:
            logger.addHandler(logging.StreamHandler(logStream))
        return logger

    # Spec parser
    @property
    def specs(self):
        return self.__specParser

    # Requests
    @property
    def requests(self):
        return self.__requests

    # Resources collection
    @property
    def resources(self):
        return self.__resources

    # WSGI request environ
    @property
    def environ(self):
        threadKey = threading.current_thread().ident
        threadState = self.__threadStates.get(threadKey, self.__threadStateDefault)
        return threadState.environ

    # WSGI request start_response
    @property
    def start_response(self):
        threadKey = threading.current_thread().ident
        threadState = self.__threadStates.get(threadKey, self.__threadStateDefault)
        return threadState.start_response

    # Logger object
    @property
    def log(self):
        threadKey = threading.current_thread().ident
        threadState = self.__threadStates.get(threadKey, self.__threadStateDefault)
        return threadState.log

    # Send an HTTP response
    def response(self, status, contentType, content, headers = None):

        # Ensure proper WSGI response data type
        if not isinstance(content, (list, tuple)):
            content = [content]
        content = [(wsgistr_new(s) if not isinstance(s, wsgistr_) else s) for s in content]

        # Build the headers array
        _headers = list(headers or [])
        if not any(header[0] == "Content-Type" for header in _headers):
            _headers.append(("Content-Type", contentType))
        _headers.append(("Content-Length", str(sum(len(s) for s in content))))

        # Return the response
        self.start_response(status, _headers)
        return content

    # Serialize an object to JSON
    def serializeJSON(self, o):
        return json.dumps(o, sort_keys = True,
                          indent = 2 if self.prettyOutput else None,
                          separators = (", ", ": ") if self.prettyOutput else (",", ":"))

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
                    self.__specParser.parse(os.path.join(dirpath, filename), finalize = False)
        if finalize:
            self.__specParser.finalize()

    # Load a spec string
    def loadSpecString(self, spec, fileName = "", finalize = True):
        self.__specParser.parseString(spec, fileName = fileName, finalize = finalize)

    # Add a request handler (Request-wrapped WSGI application)
    def addRequest(self, request):

        # Wrap bare functions in a request decorator
        if not isinstance(request, Request):
            request = Request(request)

        # Duplicate request name?
        if request.name in self.__requests:
            raise Exception("Redefinition of request '%s'" % (request.name,))
        self.__requests[request.name] = request

        # Add the request URLs
        for url in request.urls:
            if url in self.__requestUrls:
                raise Exception("Redefinition of request URL '%s'" % (url,))
            self.__requestUrls[url] = request

        # Make the request app-aware at load-time
        request.onload(self)

    # Add the built-in documentation request
    def addDocRequest(self):
        self.addRequest(DocAction())

    # Recursively load all requests in a directory
    def loadRequests(self, moduleDir, moduleExt = ".py"):

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

    # Add a resource
    def addResource(self, resourceName, resourceOpen, resourceClose, resourceString):
        self.__resources.add(resourceName, resourceOpen, resourceClose, resourceString)

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
    def serve(cls, application):

        import optparse
        import wsgiref.util
        import wsgiref.simple_server

        # Command line options
        optParser = optparse.OptionParser()
        optParser.add_option("-p", dest = "port", type = "int", default = 8080,
                             help = "Server port (default is 8080)")
        (opts, args) = optParser.parse_args()

        # Stand-alone server WSGI entry point
        def application_simple_server(environ, start_response):
            wsgiref.util.setup_testing_defaults(environ)
            return application(environ, start_response)

        # Start the stand-alone server
        print("Serving on port %d..." % (opts.port,))
        httpd = wsgiref.simple_server.make_server("", opts.port, application_simple_server)
        httpd.serve_forever()
