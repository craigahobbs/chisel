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
            moduleName = str(uuid.uuid1())
            with open(modulePath, "rb") as fModule:
                module = imp.load_source(moduleName, modulePath, fModule)

            # Get the module's actions
            for actionCallback in module.actions():
                self.addActionCallback(actionCallback)

    # Add a single action model
    def addActionModel(self, actionModel):

        if actionModel.name in self._actionModels:
            raise Exception("Redefinition of action model '%s'" % (actionModel.name))
        else:
            self._actionModels[actionModel.name] = actionModel

    # Load spec(s) from a directory path, file path, or stream
    def loadSpecs(self, spec, parser = None, specFileName = ""):

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
            errorTypeInst.values.append(TypeEnum.Value("UnknownRequestMethod"))
        errorResponseTypeInst.members.append(TypeStruct.Member("error", errorTypeInst))
        errorResponseTypeInst.members.append(TypeStruct.Member("message", TypeString(), isOptional = True))
        errorResponseTypeInst.members.append(TypeStruct.Member("member", TypeString(), isOptional = True))
        return errorResponseTypeInst

    # Helper to send an HTTP response
    def _httpResponse(self, start_response, actionContext, status, contentType, *responseBody):

        # Build the headers array
        responseHeaders = [
            ("Content-Type", contentType),
            ("Content-Length", str(sum([len(s) for s in responseBody])))
            ]
        if self._headersCallback:
            responseHeaders.extend(self._headersCallback(actionContext))

        # Return the response
        start_response(status, responseHeaders)
        return responseBody

    # Helper to send an HTTP 404 Not Found
    def _http404NotFound(self, start_response):

        return self._httpResponse(start_response, None, "404 Not Found", "text/plain", "Not Found")

    # Helper to send an HTTP 405 Method Not Allowed
    def _http405MethodNotAllowed(self, start_response):

        return self._httpResponse(start_response, None, "405 Method Not Allowed", "text/plain", "Method Not Allowed")

    # Request handling helper method
    def _handleRequest(self, environ):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")
        envQueryString = environ.get("QUERY_STRING")
        envContentLength = environ.get("CONTENT_LENGTH")
        envWsgiInput = environ.get("wsgi.input")

        # Server error return helper
        jsonpFunction = None
        actionContext = None
        def serverError(error, message, member = None):
            response = self._errorResponse(error, message, member)
            assert self._errorResponseTypeInst().validate(response)
            return jsonpFunction, actionContext, response

        # Match an action
        actionName = envPathInfo.split("/")[-1]
        actionCallback = self._actionCallbacks[actionName]
        actionModel = self._actionModels[actionName]

        # Get the request content
        isGetRequest = (envRequestMethod == "GET")
        if isGetRequest:

            # Parse the query string
            if not envQueryString:
                request = {}
            else:
                try:
                    request = decodeQueryString(envQueryString)
                except Exception, e:
                    return serverError("InvalidInput", str(e))

                # JSONP?
                if self._jsonpMemberName in request:
                    jsonpFunction = request[self._jsonpMemberName]
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

        # Match the resource
        pathParts = envPathInfo.strip("/").split("/")
        if len(pathParts) == 1 and pathParts[0] == self._docUriDir:

            if envRequestMethod == "GET":

                # Generate the doc index HTML
                docRootUrl = joinUrl(application_uri(environ), urllib.quote(self._docUriDir))
                actionModels = [actionModel for actionModel in self._actionModels.itervalues() \
                                    if actionModel.name in self._actionCallbacks]
                responseBody = createIndexHtml(docRootUrl, actionModels, docCssUri = self._docCssUri)
                return self._httpResponse(start_response, None, "200 OK", "text/html", responseBody)

            else:

                return self._http405MethodNotAllowed(start_response)

        elif len(pathParts) == 2 and pathParts[0] == self._docUriDir and pathParts[1] in self._actionCallbacks:

            if envRequestMethod == "GET":

                # Generate the action doc HTML
                docRootUrl = joinUrl(application_uri(environ), urllib.quote(self._docUriDir))
                actionModel = self._actionModels[pathParts[1]]
                responseBody = createActionHtml(docRootUrl, actionModel, docCssUri = self._docCssUri)
                return self._httpResponse(start_response, None, "200 OK", "text/html", responseBody)

            else:

                return self._http405MethodNotAllowed(start_response)

        elif len(pathParts) == 1 and pathParts[0] in self._actionCallbacks:

            if envRequestMethod in ("GET", "POST"):

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
                    status = "500 Internal Server Error"
                else:
                    status = "200 OK"

                # Send the response
                return self._httpResponse(start_response, actionContext, status, contentType, *responseBody)

            else:

                return self._http405MethodNotAllowed(start_response)

        # Resource not found
        return self._http404NotFound(start_response)
