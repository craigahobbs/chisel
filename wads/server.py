#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct
from .url import decodeQueryString

import imp
import json
import logging
import os
import uuid


# Module action class
class ModuleAction:
    def __init__(self, callback):
        self.name = callback.func_name
        self.callback = callback


# RequestException class
class RequestException(Exception):
    def __init__(self, error, message):
        Exception.__init__(self, message)
        self.error = error
        self.message = message


# Helper function to serialize structs as JSON
def serializeJSON(o, pretty = False):

    # Unwrap struct objects during JSON serialization
    def default(o):
        if isinstance(o, Struct):
            return o()
        return o

    # Serialize to a JSON string
    return json.dumps(o,
                      sort_keys = True,
                      indent = 0 if pretty else None,
                      separators = (', ', ': ') if pretty else (',', ':'),
                      default = default)


# API server response handler
class RequestHandler:

    # JSONP callback reserved member name
    jsonpMember = "jsonp"

    # Class initializer
    def __init__(self):

        self._moduleActions = {}

    # Logger accessor
    def getLogger(self):

        return logging.getLogger()

    # Helper method to load a single module
    def _loadModule(self, modulePath):

        # Load the module
        try:
            moduleName = str(uuid.uuid1())
            with open(modulePath, 'rb') as fModule:
                module = imp.load_source(moduleName, modulePath, fModule)

            # Get the module's actions
            try:
                for actionCallback in module.actions():
                    self.addModuleAction(actionCallback)
            except Exception, e:
                self.getLogger().info("Error iterating module actions '%s': %s" % (modulePath, str(e)))

        except Exception, e:
            self.getLogger().info("Error loading module '%s': %s" % (modulePath, str(e)))

    # Add a single module action
    def addModuleAction(self, actionCallback):

        moduleAction = ModuleAction(actionCallback)
        if moduleAction.name not in self._moduleActions:
            self._moduleActions[moduleAction.name] = moduleAction
        else:
            self.getLogger().info("Action '%s' already defined" % (moduleAction.name))

    # Load modules
    def loadModules(self, modulePath):

        # Recursively load all modules
        if os.path.isdir(modulePath):
            for dirpath, dirnames, filenames in os.walk(modulePath):
                for filename in filenames:
                    (base, ext) = os.path.splitext(filename)
                    if ext == '.py':
                        modulePath = os.path.join(dirpath, filename)
                        self._loadModule(modulePath)
        else:
            self.getLogger().info("Module path does not exist '%s'" % (modulePath))

    # Request exception helper method
    def requestException(self, error, message):

        self.getLogger().warn(message)
        raise RequestException(error, message)

    # Request handling helper method
    def handleRequest(self, environ, start_response):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")
        envQueryString = environ.get("QUERY_STRING")
        envContentLength = environ.get("CONTENT_LENGTH")
        envWsgiInput = environ["wsgi.input"]

        # Match an action
        moduleAction = None
        actionName = envPathInfo.split("/")[-1]
        moduleAction = self._moduleActions.get(actionName)
        if not moduleAction or not moduleAction.name:
            raise RequestException("UnknownAction",
                                   "Request for unknown action '%s'" % (actionName))

        # Get the request
        jsonpFunction = None
        if envRequestMethod == "GET":

            # Parse the query string
            if not envQueryString:
                request = {}
            else:
                request = decodeQueryString(envQueryString)

                # JSONP?
                if RequestHandler.jsonpMember in request:
                    jsonpFunction = str(request[RequestHandler.jsonpMember])
                    del request[RequestHandler.jsonpMember]

        elif envRequestMethod != "POST":

            raise RequestException("UnknownRequestMethod",
                                   "Unknown request method '%s'" % (envRequestMethod))

        else: # POST

            # Parse content length
            try:
                contentLength = int(envContentLength)
            except:
                raise RequestException("InvalidContentLength",
                                       "Invalid content length '%s'" % (envContentLength))

            # De-serialize the JSON request
            try:
                requestBody = envWsgiInput.read(contentLength)
                request = json.loads(requestBody)
            except Exception, e:
                raise RequestException("InvalidInput",
                                       "Invalid request JSON: %s" % (str(e)))

        # Call the action callback
        try:
            return moduleAction.callback(None, Struct(request)), jsonpFunction
        except Exception, e:
            raise RequestException("UnexpectedError", str(e))

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Handle the request
        jsonpFunction = None
        try:
            response, jsonpFunction = self.handleRequest(environ, start_response)
        except RequestException, e:
            response = { "error": e.error, "message": e.message }
        except Exception, e:
            response = { "error": "UnexpectedError", "message": str(e) }

        # Serialize the response
        if jsonpFunction:
            responseBody = [jsonpFunction, "(", serializeJSON(response), ")"]
        else:
            responseBody = [serializeJSON(response)]

        # Send the response
        responseHeaders = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(sum([len(s) for s in responseBody])))
            ]
        start_response("200 OK", responseHeaders)

        return responseBody
