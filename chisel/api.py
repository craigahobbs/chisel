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
import sys
import traceback
import urllib
from wsgiref.util import application_uri


# API callback decorator - used to identify action callback functions during module loading
class actionDecorator:

    def __init__(self, fn):

        self.fn = fn
        self.name = fn.func_name

    def __call__(self, *args):

        self.fn(*args)


# Action error response exception
class ActionError(Exception):
    def __init__(self, error, message = None):
        self.error = error
        self.message = message


# Internal action error response exception
class ActionErrorInternal(Exception):
    def __init__(self, error, message = None, member = None):
        self.error = error
        self.message = message
        self.member = member


# API server response handler
class Application:

    # Class initializer
    def __init__(self,
                 wrapApplication = None,
                 isPretty = False,
                 contextCallback = None,
                 headersCallback = None,
                 docCssUri = None,
                 docUriDir = "doc",
                 jsonpMemberName = "jsonp"):

        self._actionCallbacks = {}
        self._specParser = SpecParser()
        self._wrapApplication = wrapApplication
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

    # Add a single action callback
    def addActionCallback(self, actionCallback, actionName = None):

        actionName = actionCallback.func_name if actionName is None else actionName
        if actionName not in self._specParser.actions:
            raise Exception("No model defined for action callback '%s'" % (actionName))
        elif actionName in self._actionCallbacks:
            raise Exception("Redefinition of action callback '%s'" % (actionName))
        else:
            self._actionCallbacks[actionName] = actionCallback

    # Recursively load all modules files in a directory
    def loadModules(self, modulePath, moduleExt = ".py"):

        # Add the module path to the system load path
        if modulePath not in sys.path:
            sys.path.append(modulePath)

        # Recursively find module names
        modulePathParts = modulePath.split(os.sep)
        for dirpath, dirnames, filenames in os.walk(modulePath):
            for filename in filenames:
                (base, ext) = os.path.splitext(filename)
                if ext == moduleExt:

                    # Determine the relative module path
                    moduleFile = os.path.join(dirpath, filename)
                    moduleFileParts = moduleFile.split(os.sep)
                    moduleNames = moduleFileParts[len(modulePathParts):-1] + \
                        list(os.path.splitext(moduleFileParts[-1])[:1])

                    # Don't load __init__
                    if moduleNames[-1] == "__init__":
                        continue

                    # Load each module down the relative module path
                    curPath = modulePath
                    module = None
                    for ixModuleName, moduleName in enumerate(moduleNames):
                        moduleArgs = imp.find_module(moduleName, [curPath])
                        module = imp.load_module(".".join(moduleNames[0:ixModuleName + 1]), *moduleArgs)
                        curPath = os.path.join(curPath, moduleName)

                    # Add the module's actions
                    for moduleAttr in dir(module):
                        actionDecoratorInst = getattr(module, moduleAttr)
                        if isinstance(actionDecoratorInst, actionDecorator):
                            self.addActionCallback(actionDecoratorInst.fn, actionName = actionDecoratorInst.name)

    # Recursively load all specs in a directory
    def loadSpecs(self, specPath, specExt = ".chsl", finalize = True):

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
    def _http404NotFound(self, environ, start_response):
        if self._wrapApplication is not None:
            return self._wrapApplication(environ, start_response)
        else:
            return self._httpResponse(start_response, None, "404 Not Found", "text/plain", "Not Found")

    # Helper to send an HTTP 405 Method Not Allowed
    def _http405MethodNotAllowed(self, start_response):
        return self._httpResponse(start_response, None, "405 Method Not Allowed", "text/plain", "Method Not Allowed")

    # Helper to send an HTTP 411 Length Required
    def _http411LengthRequired(self, start_response):
        return self._httpResponse(start_response, None, "411 Length Required", "text/plain", "Length Required")

    # Helper to create an error response type instance
    def _errorResponseTypeInst(self, errorTypeInst):

        errorResponseTypeInst = TypeStruct()
        errorResponseTypeInst.members.append(TypeStruct.Member("error", errorTypeInst))
        errorResponseTypeInst.members.append(TypeStruct.Member("message", TypeString(), isOptional = True))
        return errorResponseTypeInst

    # Helper serialize JSON content
    def _serializeJSON(self, response):

        return json.dumps(response, sort_keys = True, default = jsonDefault,
                          indent = 2 if self._isPretty else None,
                          separators = (", ", ": ") if self._isPretty else (",", ":"))

    # Request handling helper method
    def _actionResponse(self, environ, start_response, actionName, request, actionError = None,
                        acceptString = False, jsonpFunction = None):

        isErrorResponse = True
        actionContext = None
        try:
            # Server error provided?
            if actionError is not None:
                raise actionError

            # Validate the request
            try:
                actionModel = self._specParser.actions[actionName]
                request = actionModel.inputType.validate(request, acceptString = acceptString)
            except ValidationError as e:
                raise ActionErrorInternal("InvalidInput", str(e), e.member)

            try:
                # Create the action callback
                actionContext = self._contextCallback(environ) if self._contextCallback is not None else None

                # Call the action callback
                actionCallback = self._actionCallbacks[actionName]
                response = actionCallback(actionContext, Struct(request))

            except ActionError as e:

                response = { "error": e.error }
                if e.message is not None:
                    response["message"] = e.message

            except Exception as e:

                exc_type, exc_obj, exc_tb = sys.exc_info()
                exc_path, exc_line = traceback.extract_tb(exc_tb)[-1][:2]
                err = "%s:%d: %s" % (os.path.split(exc_path)[-1], exc_line, str(e))
                raise ActionErrorInternal("UnexpectedError", err)

            # Error response?
            isErrorResponse = ("error" in response)
            if isErrorResponse:
                responseTypeInst = self._errorResponseTypeInst(actionModel.errorType)
            else:
                responseTypeInst = actionModel.outputType

            # Validate the response
            try:
                response = responseTypeInst.validate(response)
            except ValidationError as e:
                raise ActionErrorInternal("InvalidOutput", str(e), e.member)

        except ActionErrorInternal as e:

            response = { "error": e.error }
            if e.message is not None:
                response["message"] = e.message
            if e.member is not None:
                response["member"] = e.member

        # Serialize the response as JSON
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
                actionModels = [actionModel for actionModel in self._specParser.actions.itervalues() \
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
                actionModel = self._specParser.actions[actionName]
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
                actionError = None
                try:
                    # Parse the query string
                    if envQueryString:
                        request = decodeQueryString(envQueryString)

                        # JSONP?
                        if self._jsonpMemberName in request:
                            jsonpFunction = str(request[self._jsonpMemberName])
                            del request[self._jsonpMemberName]
                    else:
                        request = {}

                except Exception as e:
                    actionError = ActionErrorInternal("InvalidInput", str(e))

                # Call the action callback
                return self._actionResponse(environ, start_response, actionName, request, actionError = actionError,
                                            acceptString = True, jsonpFunction = jsonpFunction)

            elif envRequestMethod == "POST":

                if envContentLength is None:
                    return self._http411LengthRequired(start_response)

                request = None
                actionError = None
                try:
                    # Read the request content
                    requestContent = envWsgiInput.read(envContentLength)

                    # De-serialize the JSON request
                    try:
                        request = json.loads(requestContent)
                    except Exception as e:
                        actionError = ActionErrorInternal("InvalidInput", "Invalid request JSON: %s" % (str(e)))

                except:
                    actionError = ActionErrorInternal("IOError", "Error reading request content")

                # Call the action callback
                return self._actionResponse(environ, start_response, actionName, request, actionError = actionError)

            else:
                return self._http405MethodNotAllowed(start_response)

        # Resource not found
        return self._http404NotFound(environ, start_response)
