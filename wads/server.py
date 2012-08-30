#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .spec import SpecParser
from .struct import Struct
from .url import decodeQueryString

import imp
import json
import logging
import os
import uuid


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
                      separators = (", ", ": ") if pretty else (",", ":"),
                      default = default)


# API server response handler
class Application:

    # File extensions
    specFileExtension = ".chsl"
    moduleFileExtension = ".py"

    # JSONP callback reserved member name
    jsonpMember = "jsonp"

    # Class initializer
    def __init__(self):

        self._actionCallbacks = {}
        self._actionModels = {}

    # Logger accessor
    def getLogger(self):

        return logging.getLogger()

    # Action callback helper class
    class _ActionCallback:
        def __init__(self, actionCallback, actionName = None):
            self.name = actionName or actionCallback.func_name
            self.callback = actionCallback

    # Add a single action callback
    def addActionCallback(self, actionCallback):

        actionCallback = self._ActionCallback(actionCallback)
        if actionCallback.name not in self._actionCallbacks:
            self._actionCallbacks[actionCallback.name] = actionCallback
        else:
            raise Exception("Redefinition of action callback '%s'" % (actionCallback.name))

    # Recursively load all modules in a directory
    def loadModules(self, modulePath):

        # Directory (presumably containing modules)
        if os.path.isdir(modulePath):

            # Search for module files
            for dirpath, dirnames, filenames in os.walk(modulePath):
                for filename in filenames:
                    (base, ext) = os.path.splitext(filename)
                    if ext == self.moduleFileExtension:
                        self.loadModules(os.path.join(dirpath, filename))

        else:

            # Load the module file
            try:
                moduleName = str(uuid.uuid1())
                with open(modulePath, "rb") as fModule:
                    module = imp.load_source(moduleName, modulePath, fModule)

                # Get the module's actions
                for actionCallback in module.actions():
                    self.addActionCallback(actionCallback)

            except Exception, e:
                self.getLogger().error("Error loading module '%s': %s" % (modulePath, str(e)))
                raise e

    # Add a single action model
    def addActionModel(self, actionModel):

        if actionModel.name not in self._actionModels:
            self._actionModels[actionModel.name] = actionModel
        else:
            raise Exception("Redefinition of action model '%s'" % (actionModel.name))

    # Load spec(s) from a directory path, file path, or stream
    def loadSpecs(self, spec, parser = None):

        parser = parser or SpecParser()

        # Is spec a path string?
        if isinstance(spec, basestring):

            # Is spec a directory path?
            if os.path.isdir(spec):

                # Recursively parse spec files
                for dirpath, dirnames, filenames in os.walk(spec):
                    for filename in filenames:
                        (base, ext) = os.path.splitext(filename)
                        if ext == self.specFileExtension:
                            self.loadSpec(os.path.join(dirpath, filename), parser = parser)

            # Assume file path...
            else:
                with open(spec, "rb") as fhSpec:
                    self.loadSpec(fhSpec, parser = parser)

        # Assume stream...
        else:
            parser.parse(spec)

        # Finalize parsing
        parser.finalize()
        if parser.errors:
            raise Exception("\n".join(parser.errors))

        # Add action models
        for actionModel in parser.model.actions.itervalues():
            self.addActionModel(actionModel)

    # Request exception helper class
    class _RequestException(Exception):
        def __init__(self, error, message):
            Exception.__init__(self, message)
            self.error = error

    # Request exception helper method
    def _requestException(self, error, message):

        self.getLogger().info(message)
        raise self._RequestException(error, message)

    # Request handling helper method
    def _handleRequest(self, environ, start_response):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")
        envQueryString = environ.get("QUERY_STRING")
        envContentLength = environ.get("CONTENT_LENGTH")
        envWsgiInput = environ["wsgi.input"]

        # Match an action
        actionName = envPathInfo.split("/")[-1]
        actionCallback = self._actionCallbacks.get(actionName)
        actionModel = self._actionModels.get(actionName)
        if actionCallback is None or actionModel is None:
            self._requestException("UnknownAction", "Request for unknown action '%s'" % (actionName))

        # Get the request
        jsonpFunction = None
        if envRequestMethod == "GET":

            # Parse the query string
            if not envQueryString:
                request = {}
            else:
                request = decodeQueryString(envQueryString)

                # JSONP?
                if self.jsonpMember in request:
                    jsonpFunction = str(request[self.jsonpMember])
                    del request[self.jsonpMember]

        elif envRequestMethod != "POST":

            self._requestException("UnknownRequestMethod", "Unknown request method '%s'" % (envRequestMethod))

        else: # POST

            # Parse content length
            try:
                contentLength = int(envContentLength)
            except:
                self._requestException("InvalidContentLength", "Invalid content length '%s'" % (envContentLength))

            # Read the request content
            try:
                requestBody = envWsgiInput.read(contentLength)
            except:
                self._requestException("InvalidInput", "Error reading request content")

            # De-serialize and validate the JSON request
            try:
                request = actionModel.inputType.validate(json.loads(requestBody))
            except Exception, e:
                self._requestException("InvalidInput", "Invalid request JSON: %s" % (str(e)))

        # Call the action callback and validate the response
        try:
            response = actionModel.outputType.validate(actionCallback.callback(None, Struct(request)))
        except ValidationException, e:
            self._requestException("InvalidOutput", str(e))
        except Exception, e:
            self._requestException("UnexpectedError", str(e))

        return response, jsonpFunction

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Handle the request
        jsonpFunction = None
        try:
            response, jsonpFunction = self._handleRequest(environ, start_response)
        except self._RequestException, e:
            response = { "error": e.error, "message": str(e) }
        except Exception, e:
            response = { "error": "UnexpectedError", "message": str(e) }

        # Serialize the response
        if jsonpFunction:
            responseBody = [jsonpFunction, "(", serializeJSON(response), ");"]
        else:
            responseBody = [serializeJSON(response)]

        # Send the response
        responseHeaders = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(sum([len(s) for s in responseBody])))
            ]
        start_response("200 OK", responseHeaders)

        return responseBody
