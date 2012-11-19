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

    # Helper to send an HTTP response
    def _httpResponse(self, start_response, actionContext, status, contentType, *responseBody):

        # Build the headers array
        responseHeaders = [
            ("Content-Type", contentType),
            ("Content-Length", str(sum([len(s) for s in responseBody])))
            ]
        if self._headersCallback and actionContext is not None:
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

    # Helper to send an HTTP 411 Length Required
    def _http411LengthRequired(self, start_response):
        return self._httpResponse(start_response, None, "411 Length Required", "text/plain", "Length Required")

    # Helper to form an error response
    def _errorResponse(self, error, message, member = None):

        response = Struct()
        response.error = error
        response.message = message
        if member:
            response.member = member
        return response

    # Helper to create an error response type instance
    def _errorResponseTypeInst(self, errorTypeInst):

        errorResponseTypeInst = TypeStruct()
        errorResponseTypeInst.members.append(TypeStruct.Member("error", errorTypeInst))
        errorResponseTypeInst.members.append(TypeStruct.Member("message", TypeString(), isOptional = True))
        errorResponseTypeInst.members.append(TypeStruct.Member("member", TypeString(), isOptional = True))
        return errorResponseTypeInst

    # Error response exception helper class
    class _ErrorResponseException(Exception):
        def __init__(self, response):
            Exception.__init__(self, "Error response")
            self.response = response

    # Helper serialize JSON content
    def _serializeJSON(self, response):

        return json.dumps(response, sort_keys = True, default = jsonDefault,
                          indent = 2 if self._isPretty else None,
                          separators = (", ", ": ") if self._isPretty else (",", ":"))

    # Request handling helper method
    def _actionResponse(self, environ, start_response, actionName, request, errorResponse = None,
                        acceptString = False, jsonpFunction = None):

        isErrorResponse = True
        actionContext = None
        try:
            # Server error response provided?
            if errorResponse is not None:
                raise self._ErrorResponseException(errorResponse)

            # Validate the request
            try:
                actionModel = self._actionModels[actionName]
                request = actionModel.inputType.validate(request, acceptString = acceptString)
            except ValidationError, e:
                raise self._ErrorResponseException(self._errorResponse("InvalidInput", str(e), e.member))

            try:
                # Create the action callback
                actionContext = self._contextCallback(environ) if self._contextCallback is not None else None

                # Call the action callback
                actionCallback = self._actionCallbacks[actionName]
                response = actionCallback(actionContext, Struct(request))

            except Exception, e:
                raise self._ErrorResponseException(self._errorResponse("UnexpectedError", str(e)))

            # Error response?
            isErrorResponse = ("error" in response)
            if isErrorResponse:
                responseTypeInst = self._errorResponseTypeInst(actionModel.errorType)
            else:
                responseTypeInst = actionModel.outputType

            # Validate the response
            try:
                response = responseTypeInst.validate(response)
            except ValidationError, e:
                raise self._ErrorResponseException(self._errorResponse("InvalidOutput", str(e), e.member))

        except self._ErrorResponseException, e:
            response = e.response

        # Serialize the response as JSON
        try:
            jsonContent = self._serializeJSON(response)
        except Exception, e:
            response = self._errorResponse("InvalidOutput", str(e))
            jsonContent = self._serializeJSON(response)

        # Determine the HTTP status
        if isErrorResponse and jsonpFunction is None:
            status = "500 Internal Server Error"
        else:
            status = "200 OK"

        # Send the response
        if jsonpFunction is not None:
            return self._httpResponse(start_response, actionContext, status, "application/json",
                                      jsonpFunction, "(", jsonContent, ");")
        else:
            return self._httpResponse(start_response, actionContext, status, "application/json",
                                      jsonContent)

    # WSGI entry point
    def __call__(self, environ, start_response):

        envRequestMethod = environ.get("REQUEST_METHOD")
        envPathInfo = environ.get("PATH_INFO")
        envQueryString = environ.get("QUERY_STRING")
        try:
            envContentLength = int(environ.get("CONTENT_LENGTH"))
        except:
            envContentLength = None
        envWsgiInput = environ.get("wsgi.input")

        # Split the request URL
        pathParts = envPathInfo.strip("/").split("/")

        # Doc index page resource?
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

        # Action doc page resource?
        elif len(pathParts) == 2 and pathParts[0] == self._docUriDir and pathParts[1] in self._actionCallbacks:

            actionName = pathParts[1]

            if envRequestMethod == "GET":

                # Generate the action doc HTML
                docRootUrl = joinUrl(application_uri(environ), urllib.quote(self._docUriDir))
                actionModel = self._actionModels[actionName]
                responseBody = createActionHtml(docRootUrl, actionModel, docCssUri = self._docCssUri)
                return self._httpResponse(start_response, None, "200 OK", "text/html", responseBody)

            else:
                return self._http405MethodNotAllowed(start_response)

        # Action request?
        elif len(pathParts) == 1 and pathParts[0] in self._actionCallbacks:

            actionName = pathParts[0]

            if envRequestMethod == "GET":

                request = None
                jsonpFunction = None
                errorResponse = None
                try:
                    # Parse the query string
                    if envQueryString:
                        request = decodeQueryString(envQueryString)

                        # JSONP?
                        jsonpFunction = request.get(self._jsonpMemberName)
                        if jsonpFunction is not None:
                            del request[self._jsonpMemberName]
                    else:
                        request = {}

                except Exception, e:
                    errorResponse = self._errorResponse("InvalidInput", str(e))

                # Call the action callback
                return self._actionResponse(environ, start_response, actionName, request, errorResponse = errorResponse,
                                            acceptString = True, jsonpFunction = jsonpFunction)

            elif envRequestMethod == "POST":

                if envContentLength is None:
                    return self._http411LengthRequired(start_response)

                request = None
                errorResponse = None
                try:
                    # Read the request content
                    requestContent = envWsgiInput.read(envContentLength)

                    # De-serialize the JSON request
                    try:
                        request = json.loads(requestContent)
                    except Exception, e:
                        errorResponse = self._errorResponse("InvalidInput", "Invalid request JSON: %s" % (str(e)))

                except:
                    errorResponse = self._errorResponse("IOError", "Error reading request content")

                # Call the action callback
                return self._actionResponse(environ, start_response, actionName, request, errorResponse = errorResponse)

            else:
                return self._http405MethodNotAllowed(start_response)

        # Resource not found
        return self._http404NotFound(start_response)
