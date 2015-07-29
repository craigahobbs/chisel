#
# Copyright (C) 2012-2015 Craig Hobbs
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

from .compat import basestring_, iteritems, string_isidentifier, urllib_parse_unquote, xrange_
from .doc import DocAction
from .request import Request
from .spec import SpecParser

from collections import namedtuple
from io import BytesIO
import itertools
import json
import logging
import os
import re
import sys
import threading


# Null stream object for supressing logs in request
class NullStream(object):
    __slots__ = ()

    def write(self, s):
        pass

NULL_STREAM = NullStream()


# Top-level WSGI application class
class Application(object):

    __slots__ = (
        '__logStream',
        '__logLevel',
        '__logFormat',
        '__defaultLogger',
        'prettyOutput',
        'validateOutput',
        '__threadStates',
        '__specParser',
        '__requests',
        '__requestUrls',
        '__requestUrlRegex',
        )

    ENVIRON_APP = 'chisel.app'
    ENVIRON_JSONP = 'chisel.jsonp'
    ENVIRON_HEADERS = 'chisel.headers'
    ENVIRON_URL_ARGS = 'chisel.urlArgs'

    ThreadState = namedtuple('ThreadState', ('environ', 'start_response', 'log'))

    def __init__(self, logStream=sys.stderr):

        self.__logStream = logStream
        self.__logLevel = logging.WARNING
        self.__logFormat = '%(levelname)s [%(process)s / %(thread)s] %(message)s'
        self.__defaultLogger = self.__createLogger(logStream)
        self.prettyOutput = False
        self.validateOutput = True
        self.__threadStates = {}
        self.__specParser = SpecParser()
        self.__requests = {}
        self.__requestUrls = {}
        self.__requestUrlRegex = []

    # Overridable WSGI entry point
    def call(self, environ, start_response):

        # Match the request by exact URL
        pathInfo = environ['PATH_INFO']
        request = self.__requestUrls.get(pathInfo)

        # If no request was matched, match by url regular expression
        if not request:
            for reUrl, requestRegex in self.__requestUrlRegex:
                mUrl = reUrl.match(pathInfo)
                if mUrl:
                    request = requestRegex
                    environ[self.ENVIRON_URL_ARGS] = dict((urllib_parse_unquote(urlArg), urllib_parse_unquote(urlValue))
                                                          for urlArg, urlValue in iteritems(mUrl.groupdict()))
                    break

        # Handle the request
        if request is not None:
            try:
                return request(environ, start_response)
            except: # pylint: disable=bare-except
                self.log.exception('Exception raised by WSGI request "%s"', request.name)
                return self.responseText('500 Internal Server Error', 'Unexpected Error')
        else:
            return self.responseText('404 Not Found', 'Not Found')

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Set the app environment item
        environ[self.ENVIRON_APP] = self

        # Wrap start_response
        def _start_response(status, headers):
            _headers = self.getHeaders()
            if _headers:
                headers = list(itertools.chain(headers, _headers)) if headers else _headers
            return start_response(status, headers)

        # Call the overridable WSGI entry point
        self.__pushThreadState(environ, _start_response)
        try:
            return self.call(environ, _start_response)
        finally:
            self.__popThreadState()

    # Push a thread state
    def __pushThreadState(self, environ, start_response):
        threadKey = threading.current_thread().ident
        threadState = self.ThreadState(environ, start_response, self.__createLogger(environ['wsgi.errors']))
        if threadKey in self.__threadStates:
            self.__threadStates[threadKey].append(threadState)
        else:
            self.__threadStates[threadKey] = [threadState]

    # Pop a thread state
    def __popThreadState(self):
        threadKey = threading.current_thread().ident
        threadStateStack = self.__threadStates[threadKey]
        threadState = threadStateStack.pop()
        if len(threadStateStack) == 0:
            del self.__threadStates[threadKey]

        # Cleanup a logger to avoid memory leaks
        for handler in threadState.log.handlers:
            handler.flush()
            handler.close()

    # Get the active thread state
    def __topThreadState(self):
        threadKey = threading.current_thread().ident
        threadStateStack = self.__threadStates.get(threadKey)
        if threadStateStack is not None and len(threadStateStack) > 0:
            return self.__threadStates[threadKey][-1]
        return None

    # Create a request logger
    def __createLogger(self, logStream):
        logger = logging.getLoggerClass()('')
        logger.setLevel(self.logLevel)
        if logStream is not None:
            handler = logging.StreamHandler(logStream)
            handler.setFormatter(self.__logFormatter())
            logger.addHandler(handler)
        return logger

    # Logging level
    @property
    def logLevel(self):
        return self.__logLevel

    @logLevel.setter
    def logLevel(self, value):
        self.__logLevel = value
        if self.__defaultLogger:
            self.__defaultLogger.setLevel(self.logLevel)

    # Logging format
    @property
    def logFormat(self):
        return self.__logFormat

    def __logFormatter(self):
        return logging.Formatter(self.__logFormat) if not hasattr(self.__logFormat, '__call__') else self.__logFormat(self)

    @logFormat.setter
    def logFormat(self, value):
        self.__logFormat = value
        if self.__defaultLogger:
            for handler in self.__defaultLogger.handlers:
                handler.setFormatter(self.__logFormatter())

    # Spec parser
    @property
    def specs(self):
        return self.__specParser

    # Requests
    @property
    def requests(self):
        return self.__requests

    # WSGI request environ
    @property
    def environ(self):
        threadState = self.__topThreadState()
        return threadState.environ if threadState else None

    # WSGI request start_response
    @property
    def start_response(self):
        threadState = self.__topThreadState()
        return threadState.start_response if threadState else None

    # Logger object
    @property
    def log(self):
        threadState = self.__topThreadState()
        return threadState.log if threadState else self.__defaultLogger

    # Send an HTTP response
    def response(self, status, contentType, content, headers=None):
        assert not isinstance(content, basestring_) and not isinstance(content, bytes), \
            'Response of type str, unicode, or bytes received'

        # Build the headers array
        _headers = [] if headers is None else list(headers)
        if not any(header[0] == 'Content-Type' for header in _headers):
            _headers.append(('Content-Type', contentType))
        if hasattr(content, '__len__'):
            _headers.append(('Content-Length', str(sum(len(s) for s in content))))

        # Return the response
        self.start_response(status, _headers)
        return content

    # Send a plain-text response
    def responseText(self, status, text, headers=None, contentType='text/plain', encoding='utf-8'):
        return self.response(status, contentType, [text.encode(encoding)], headers=headers)

    # Will responseJSON serialize using JSONP (by default)?
    def isJSONP(self):
        return self.environ.get(self.ENVIRON_JSONP) is not None

    # Set the current request's JSONP function for use in responseJSON (by default)
    def setJSONP(self, jsonpFunction):
        self.environ[self.ENVIRON_JSONP] = jsonpFunction

    # Serialize an object to JSON
    def serializeJSON(self, o):
        return json.dumps(o, sort_keys=True,
                          indent=2 if self.prettyOutput else None,
                          separators=(', ', ': ') if self.prettyOutput else (',', ':'))

    # Send a JSON response
    def responseJSON(self, response, status=None, isError=False, headers=None):
        if status is None:
            status = '200 OK' if not isError or self.isJSONP() else '500 Internal Server Error'
        content = self.serializeJSON(response)
        jsonpFunction = self.environ.get(self.ENVIRON_JSONP)
        if jsonpFunction:
            content = [jsonpFunction.encode('utf-8'), b'(', content.encode('utf-8'), b');']
        else:
            content = [content.encode('utf-8')]

        return self.response(status, 'application/json', content, headers=headers)

    # Add a request header
    def addHeader(self, key, value):
        headers = self.environ.get(self.ENVIRON_HEADERS)
        if headers is None:
            headers = self.environ[self.ENVIRON_HEADERS] = []
        headers.append((key, value))

    # Get the request's headers
    def getHeaders(self):
        return self.environ.get(self.ENVIRON_HEADERS)

    # Recursively load all specs in a directory
    def loadSpecs(self, specPath, specExt='.chsl', finalize=True):

        # Does the path exist?
        if not os.path.isdir(specPath):
            raise IOError('%r not found or is not a directory' % (specPath,))

        # Resursively find spec files
        for dirpath, dummy_dirnames, filenames in os.walk(specPath):
            for filename in filenames:
                (dummy_base, ext) = os.path.splitext(filename)
                if ext == specExt:
                    with open(os.path.join(dirpath, filename), 'r') as specStream:
                        self.__specParser.parse(specStream, finalize=False)
        if finalize:
            self.__specParser.finalize()

    # Load a spec string
    def loadSpecString(self, spec, fileName='', finalize=True):
        self.__specParser.parseString(spec, fileName=fileName, finalize=finalize)

    # Regular expression for matching URL arguments
    __reUrlArg = re.compile(r'/\{([A-Za-z]\w*)\}')
    __reUrlArgEsc = re.compile(r'/\\{([A-Za-z]\w*)\\}')

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

            # URL with arguments?
            if self.__reUrlArg.search(url):
                urlRegex = '^' + self.__reUrlArgEsc.sub('/(?P<\\1>[^/]+)', re.escape(url)) + '$'
                self.__requestUrlRegex.append((re.compile(urlRegex), request))
            else:
                if url in self.__requestUrls:
                    raise Exception("Redefinition of request URL '%s'" % (url,))
                self.__requestUrls[url] = request

        # Make the request app-aware at load-time
        request.onload(self)

    # Add the built-in documentation request
    def addDocRequest(self):
        self.addRequest(DocAction())

    # Generator to recursively load all modules
    @classmethod
    def loadModules(cls, moduleDir, moduleExt='.py', excludedSubmodules=None):

        # Does the path exist?
        if not os.path.isdir(moduleDir):
            raise IOError('%r not found or is not a directory' % (moduleDir,))

        # Where is this module on the system path?
        moduleDirParts = moduleDir.split(os.sep)

        def findModuleNameIndex():
            for sysPath in sys.path:
                for iModulePart in xrange_(len(moduleDirParts) - 1, 0, -1):
                    moduleNameParts = moduleDirParts[iModulePart:]
                    if not any(not string_isidentifier(part) for part in moduleNameParts):
                        sysModulePath = os.path.join(sysPath, *moduleNameParts)
                        if os.path.isdir(sysModulePath) and os.path.samefile(moduleDir, sysModulePath):
                            # Make sure the module package is import-able
                            moduleName = '.'.join(moduleNameParts)
                            try:
                                __import__(moduleName)
                            except ImportError:
                                pass
                            else:
                                return len(moduleDirParts) - len(moduleNameParts)
            raise ImportError('%r not found on system path' % (moduleDir,))
        ixModuleName = findModuleNameIndex()

        # Recursively find module files
        excludedSubmodulesDot = None if excludedSubmodules is None else [x + '.' for x in excludedSubmodules]
        for dirpath, dummy_dirnames, filenames in os.walk(moduleDir):

            # Skip Python 3.x cache directories
            if os.path.basename(dirpath) == '__pycache__':
                continue

            # Is the sub-package excluded?
            subpkgParts = dirpath.split(os.sep)
            subpkgName = '.'.join(itertools.islice(subpkgParts, ixModuleName, None))
            if excludedSubmodules is not None and \
               (subpkgName in excludedSubmodules or any(subpkgName.startswith(x) for x in excludedSubmodulesDot)):
                continue

            # Load each sub-module file in the directory
            for filename in filenames:

                # Skip non-module files
                (basename, ext) = os.path.splitext(filename)
                if ext != moduleExt:
                    continue

                # Skip package __init__ files
                if basename == '__init__':
                    continue

                # Is the sub-module excluded?
                submoduleName = subpkgName + '.' + basename
                if excludedSubmodules is not None and \
                   (submoduleName in excludedSubmodules or any(submoduleName.startswith(x) for x in excludedSubmodules)):
                    continue

                # Load the sub-module
                yield __import__(submoduleName, globals(), locals(), ['.'])

    # Recursively load all requests in a directory
    def loadRequests(self, moduleDir, moduleExt='.py'):

        for module in self.loadModules(moduleDir, moduleExt=moduleExt):
            for moduleAttr in dir(module):
                request = getattr(module, moduleAttr)
                if isinstance(request, Request):
                    self.addRequest(request)

    # Make an HTTP request on this application
    def request(self, requestMethod, pathInfo, queryString=None, wsgiInput=None, environ=None, suppressLogging=True):

        # WSGI environment - used passed-in environ if its complete
        _environ = dict(environ) if environ else {}
        _environ['REQUEST_METHOD'] = requestMethod
        _environ['PATH_INFO'] = pathInfo
        if 'SCRIPT_NAME' not in _environ:
            _environ['SCRIPT_NAME'] = ''
        if 'QUERY_STRING' not in _environ:
            _environ['QUERY_STRING'] = queryString if queryString else ''
        if 'wsgi.input' not in _environ:
            _environ['wsgi.input'] = BytesIO(wsgiInput if wsgiInput else b'')
            if 'CONTENT_LENGTH' not in _environ:
                _environ['CONTENT_LENGTH'] = str(len(wsgiInput)) if wsgiInput else '0'
        if 'wsgi.errors' not in _environ:
            environOuter = self.environ
            _environ['wsgi.errors'] = (NULL_STREAM if suppressLogging else
                                       environOuter.get('wsgi.errors', self.__logStream) if environOuter else
                                       self.__logStream)

        # Capture the response status and headers
        startResponseArgs = {}

        def startResponse(status, responseHeaders):
            startResponseArgs['status'] = status
            startResponseArgs['responseHeaders'] = responseHeaders

        # Make the request
        response = self(_environ, startResponse)

        return (startResponseArgs['status'],
                startResponseArgs['responseHeaders'],
                b''.join(response))
