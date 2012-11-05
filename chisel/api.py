#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .doc import joinUrl, createIndexHtml, createActionHtml
from .model import jsonDefault, ValidationError, TypeStruct, TypeEnum, TypeString
from .spec import SpecParser
from .struct import Struct
from .url import decodeQueryString

import imp
import json
import os
import urllib
import uuid
from wsgiref.util import application_uri


# API server response handler
class Application:

    # Class initializer
    def __init__(self,
                 isPretty = False,
                 contextCallback = None,
                 headersCallback = None,
                 docCssUri = None,
                 docUriDir = "doc",
                 jsonpMemberName = "jsonp",
                 specFileExtension = ".chsl",
                 moduleFileExtension = ".py"):

        self._actionModels = {}
        self._actionCallbacks = {}
        self._isPretty = isPretty

        # Action handler context creation callback function
        self._contextCallback = contextCallback

        # Additional HTTP headers callback function
        self._headersCallback = headersCallback

        # CSS URL for generated documentation pages
        self._docCssUri = docCssUri

        # The generated spec documentation URL directory name
        self._docUriDir = docUriDir

        # JSONP callback reserved member name
        self._jsonpMemberName = jsonpMemberName

        # File extensions
        self._specFileExtension = specFileExtension
        self._moduleFileExtension = moduleFileExtension

    # Add a single action callback
    def addActionCallback(self, actionCallback, actionName = None):

        actionName = actionCallback.func_name if actionName is None else actionName
        if actionName not in self._actionModels:
            raise Exception("No model defined for action callback '%s'" % (actionName))
        elif actionName in self._actionCallbacks:
            raise Exception("Redefinition of action callback '%s'" % (actionName))
        else:
            self._actionCallbacks[actionName] = actionCallback

    # Recursively load all modules in a directory
    def loadModules(self, modulePath):

        # Directory (presumably containing modules)
        if os.path.isdir(modulePath):

            # Search for module files
            for dirpath, dirnames, filenames in os.walk(modulePath):
                for filename in filenames:
                    (base, ext) = os.path.splitext(filename)
                    if ext == self._moduleFileExtension:
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
                raise e

    # Add a single action model
    def addActionModel(self, actionModel):

        if actionModel.name in self._actionModels:
            raise Exception("Redefinition of action model '%s'" % (actionModel.name))
        else:
            self._actionModels[actionModel.name] = actionModel

    # Load spec(s) from a directory path, file path, or stream
    def loadSpecs(self, spec, parser = None, specFileName = None):

        isFinal = parser is None
        parser = parser or SpecParser()

        # Is spec a path string?
        if isinstance(spec, basestring):

            # Is spec a directory path?
            if os.path.isdir(spec):

                # Recursively parse spec files
                for dirpath, dirnames, filenames in os.walk(spec):
                    for filename in filenames:
                        (base, ext) = os.path.splitext(filename)
                        if ext == self._specFileExtension:
                            self.loadSpecs(os.path.join(dirpath, filename), parser = parser, specFileName = filename)

            # Assume file path...
            else:
                with open(spec, "rb") as fhSpec:
                    self.loadSpecs(fhSpec, parser = parser, specFileName = spec)

        # Assume stream...
        else:
            parser.parse(spec, fileName = specFileName)

        # Finalize parsing
        if isFinal:
            parser.finalize()
            if parser.errors:
                raise Exception("\n".join(parser.errors))

            # Add action models
            for actionModel in parser.model.actions.itervalues():
                self.addActionModel(actionModel)

    # Is a response an error response?
    @staticmethod
    def isErrorResponse(response):

        return "error" in response

    # Helper to form an error response
    def _errorResponse(self, error, message, member = None):

        response = Struct()
        response.error = error
        response.message = message
        if member:
            response.member = member
        return response

    # Helper to create an error response type instance
    def _errorResponseTypeInst(self, errorTypeInst = None):

        errorResponseTypeInst = TypeStruct()
        if errorTypeInst is None:
            errorTypeInst = TypeEnum()
            errorTypeInst.values.append(TypeEnum.Value("InvalidContentLength"))
            errorTypeInst.values.append(TypeEnum.Value("InvalidInput"))
            errorTypeInst.values.append(TypeEnum.Value("InvalidOutput"))
            errorTypeInst.values.append(TypeEnum.Value("IOError"))
            errorTypeInst.values.append(TypeEnum.Value("UnexpectedError"))
            errorTypeInst.values.append(TypeEnum.Value("UnknownAction"))
            errorTypeInst.values.append(TypeEnum.Value("UnknownRequestMethod"))
        errorResponseTypeInst.members.append(TypeStruct.Member("error", errorTypeInst))
        errorResponseTypeInst.members.append(TypeStruct.Member("message", TypeString(), isOptional = True))
        errorResponseTypeInst.members.append(TypeStruct.Member("member", TypeString(), isOptional = True))
        return errorResponseTypeInst

    # Request handling helper method
    def _handleRequest(self, environ):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")
        envQueryString = environ.get("QUERY_STRING")
        envContentLength = environ.get("CONTENT_LENGTH")
        envWsgiInput = environ["wsgi.input"]

        # Server error return helper
        jsonpFunction = None
        actionContext = None
        def serverError(error, message, member = None):
            response = self._errorResponse(error, message, member)
            assert self._errorResponseTypeInst().validate(response)
            return jsonpFunction, actionContext, response

        # Match an action
        actionName = envPathInfo.split("/")[-1]
        actionCallback = self._actionCallbacks.get(actionName)
        if actionCallback is None:
            return serverError("UnknownAction", "Request for unknown action '%s'" % (actionName))
        actionModel = self._actionModels[actionName]

        # Get the request content
        isGetRequest = (envRequestMethod == "GET")
        if isGetRequest:

            # Parse the query string
            if not envQueryString:
                request = {}
            else:
                request = decodeQueryString(envQueryString)

                # JSONP?
                if self._jsonpMemberName in request:
                    jsonpFunction = str(request[self._jsonpMemberName])
                    del request[self._jsonpMemberName]

        elif envRequestMethod == "POST":

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

        else:
            return serverError("UnknownRequestMethod", "Unknown request method '%s'" % (envRequestMethod))

        # Validate the request
        try:
            request = actionModel.inputType.validate(request, acceptString = isGetRequest)
        except ValidationError, e:
            return serverError("InvalidInput", str(e), e.member)

        # Call the action callback
        actionContext = self._contextCallback and self._contextCallback(environ)
        try:
            response = actionCallback(actionContext, Struct(request))
        except Exception, e:
            return serverError("UnexpectedError", str(e))

        # Error response?
        if self.isErrorResponse(response):
            responseTypeInst = self._errorResponseTypeInst(actionModel.errorType)
        else:
            responseTypeInst = actionModel.outputType

        # Validate the response
        try:
            response = responseTypeInst.validate(response)
        except ValidationError, e:
            return serverError("InvalidOutput", str(e), e.member)

        return jsonpFunction, actionContext, response

    # WSGI entry point
    def __call__(self, environ, start_response):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")

        # Doc request?
        pathParts = envPathInfo.strip("/").split("/")
        if envRequestMethod == "GET" and pathParts[-1] == self._docUriDir:

            status = "200 OK"
            contentType = "text/html"
            responseBody = createIndexHtml(joinUrl(application_uri(environ), urllib.quote(self._docUriDir)),
                                           [actionModel for actionModel in self._actionModels.itervalues() \
                                                if actionModel.name in self._actionCallbacks],
                                           docCssUri = self._docCssUri)

        # Action doc request?
        elif envRequestMethod == "GET" and len(pathParts) >= 2 and pathParts[-2] == self._docUriDir:

            actionModel = self._actionModels.get(pathParts[-1])
            if actionModel is None:

                status = "404 Not Found"
                contentType = "text/plain"
                responseBody = "Not Found"

            else:

                status = "200 OK"
                contentType = "text/html"
                responseBody = createActionHtml(joinUrl(application_uri(environ), self._docUriDir), actionModel,
                                                docCssUri = self._docCssUri)

        else:

            # Handle the request
            jsonpFunction, actionContext, response = self._handleRequest(environ)

            # Helper function to serialize structs as JSON
            def serializeJSON(o, isPretty = False):
                return json.dumps(o, sort_keys = True, default = jsonDefault,
                                  indent = 2 if isPretty else None,
                                  separators = (", ", ": ") if isPretty else (",", ":"))

            # Serialize the response
            contentType = "application/json"
            if jsonpFunction:
                responseBody = [jsonpFunction, "(", serializeJSON(response, isPretty = self._isPretty), ");"]
            else:
                responseBody = [serializeJSON(response, isPretty = self._isPretty)]

            # Determine the HTTP status
            if self.isErrorResponse(response) and jsonpFunction is None:
                if response["error"] == "UnknownAction":
                    status = "404 Not Found"
                else:
                    status = "500 Internal Server Error"
            else:
                status = "200 OK"

        # Send the response
        responseHeaders = [
            ("Content-Type", contentType),
            ("Content-Length", str(sum([len(s) for s in responseBody])))
            ]
        if self._headersCallback:
            responseHeaders.extend(self._headersCallback(actionContext))
        start_response(status, responseHeaders)

        return responseBody
