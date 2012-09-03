#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .model import ValidationError, TypeStruct, Member, TypeEnum, TypeString
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

    # Class initializer
    def __init__(self):

        self._actionCallbacks = {}
        self._actionModels = {}

        # File extensions
        self.specFileExtension = ".chsl"
        self.moduleFileExtension = ".py"

        # JSONP callback reserved member name
        self.jsonpMember = "jsonp"

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

    # Helper to form an error response
    def _errorResponse(self, error, message):

        response = Struct()
        response.error = error
        response.message = message
        return response

    # Helper to create an error response type instance
    def _errorResponseTypeInst(self, errorTypeInst = None):

        errorResponseTypeInst = TypeStruct()
        if errorTypeInst is None:
            errorTypeInst = TypeEnum(("InvalidContentLength",
                                      "InvalidInput",
                                      "InvalidOutput",
                                      "IOError",
                                      "UnexpectedError",
                                      "UnknownAction",
                                      "UnknownRequestMethod"))
        errorResponseTypeInst.members.append(Member("error", errorTypeInst))
        errorResponseTypeInst.members.append(Member("message", TypeString(), isOptional = True))
        return errorResponseTypeInst

    # Request handling helper method
    def _handleRequest(self, environ, start_response):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")
        envQueryString = environ.get("QUERY_STRING")
        envContentLength = environ.get("CONTENT_LENGTH")
        envWsgiInput = environ["wsgi.input"]

        # Server error return helper
        jsonpFunction = None
        def serverError(error, message):
            return self._errorResponseTypeInst(), self._errorResponse(error, message), jsonpFunction

        # Get the request content
        isGetRequest = (envRequestMethod == "GET")
        if isGetRequest:

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

            return serverError("UnknownRequestMethod", "Unknown request method '%s'" % (envRequestMethod))

        else: # POST

            # Parse content length
            try:
                contentLength = int(envContentLength)
            except:
                return serverError("InvalidContentLength", "Invalid content length '%s'" % (envContentLength))

            # Read the request content
            try:
                requestBody = envWsgiInput.read(contentLength)
            except:
                return serverError("IOError", "Error reading request content")

            # De-serialize the JSON request
            try:
                request = json.loads(requestBody)
            except Exception, e:
                return serverError("InvalidInput", "Invalid request JSON: %s" % (str(e)))

        # Match an action
        actionName = envPathInfo.split("/")[-1]
        actionCallback = self._actionCallbacks.get(actionName)
        actionModel = self._actionModels.get(actionName)
        if actionCallback is None or actionModel is None:
            return serverError("UnknownAction", "Request for unknown action '%s'" % (actionName))

        # Validate the request
        try:
            request = actionModel.inputType.validate(request, acceptString = isGetRequest)
        except ValidationError, e:
            return serverError("InvalidInput", str(e))

        # Call the action callback
        response = actionCallback.callback(None, Struct(request))

        # Error response?
        if "error" in response:
            responseTypeInst = self._errorResponseTypeInst(actionModel.errorType)
        else:
            responseTypeInst = actionModel.outputType

        return responseTypeInst, response, jsonpFunction

    # WSGI entry point
    def __call__(self, environ, start_response):

        # Handle the request and validate the response
        jsonpFunction = None
        try:
            responseTypeInst, response, jsonpFunction = self._handleRequest(environ, start_response)
            response = responseTypeInst.validate(response)
        except ValidationError, e:
            response = self._errorResponse("InvalidOutput", str(e))
            assert self._errorResponseTypeInst().validate(response)
        except Exception, e:
            response = self._errorResponse("UnexpectedError", str(e))
            assert self._errorResponseTypeInst().validate(response)

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
