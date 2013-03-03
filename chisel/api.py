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

from .doc import joinUrl, createIndexHtml, createActionHtml
from .compat import func_name, itervalues, urllib
from .model import jsonDefault, ValidationError, TypeStruct, TypeEnum, TypeString
from .spec import SpecParser
from .struct import Struct
from .url import decodeQueryString

from collections import namedtuple
import imp
import json
import os
import sys
import traceback
from wsgiref.util import application_uri


# Action path helper class
class ActionPath(namedtuple("ActionPath", "method path")):
    def __new__(cls, method, path):
        return super(cls, cls).__new__(cls, method.upper(), path)


# API callback decorator - used to identify action callback functions during module loading
class Action(object):

    def __init__(self, _fn = None, name = None, path = None,
                 responseCallback = None, validateResponse = True):

        self.fn = _fn
        self.name = name
        self.path = path if path is None else [ActionPath(*p) for p in path]
        self._setDefaults()
        self.responseCallback = responseCallback
        self.validateResponse = validateResponse
        self.model = None

    def _setDefaults(self):

        # Set the name - default is the function name
        if self.name is None and self.fn is not None:
            self.name = func_name(self.fn)

        # Set the path - default is name at root
        if self.path is None and self.name is not None:
            defaultPath = "/" + self.name
            self.path = [ActionPath("GET", defaultPath),
                         ActionPath("POST", defaultPath)]

    def __call__(self, *args):

        # If not constructed as function decorator, first call must be function decorator...
        if self.fn is None:
            self.fn = args[0]
            self._setDefaults()
            return self
        else:
            return self.fn(*args)


# Action error response exception
class ActionError(Exception):

    def __init__(self, error, message = None):

        Exception.__init__(self, error)
        self.error = error
        self.message = message


# Internal action error response exception
class ActionErrorInternal(Exception):

    def __init__(self, error, message = None, member = None):

        Exception.__init__(self, error)
        self.error = error
        self.message = message
        self.member = member


# API server response handler
class Application(object):

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
        self._actionPaths = {}
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
    def addActionCallback(self, actionCallback):

        # Wrap functions in action decorator
        if not isinstance(actionCallback, Action):
            actionCallback = Action(actionCallback)

        # Duplicate action name?
        if actionCallback.name in self._actionCallbacks:
            raise Exception("Redefinition of action callback '%s'" % (actionCallback.name,))
        self._actionCallbacks[actionCallback.name] = actionCallback

        # Match an action spec
        if actionCallback.name not in self._specParser.actions:
            raise Exception("No model defined for action callback '%s'" % (actionCallback.name,))
        actionCallback.model = self._specParser.actions[actionCallback.name]

        # Add the action paths
        for actionPath in actionCallback.path:
            self._actionPaths[actionPath] = actionCallback

    # Recursively load all modules files in a directory
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

                    # Add the module's actions
                    for moduleAttr in dir(module):
                        actionCallback = getattr(module, moduleAttr)
                        if isinstance(actionCallback, Action):
                            self.addActionCallback(actionCallback)

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

    # Helper to create an error message from an exception
    def _exceptionErrorMessage(self, e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        exc_path, exc_line = traceback.extract_tb(exc_tb)[-1][:2]
        return "%s:%d: %s" % (os.path.split(exc_path)[-1], exc_line, str(e))

    # Helper serialize JSON content
    def _serializeJSON(self, response):
        return json.dumps(response, sort_keys = True, default = jsonDefault,
                          indent = 2 if self._isPretty else None,
                          separators = (", ", ": ") if self._isPretty else (",", ":"))

    # Request handling helper method
    def _actionResponse(self, environ, start_response, actionCallback, request, actionError = None,
                        acceptString = False, jsonpFunction = None):

        # Create the action callback
        actionContext = self._contextCallback(environ) if self._contextCallback is not None else None

        try:
            # Server error provided?
            if actionError is not None:
                raise actionError

            # Validate the request
            try:
                if actionCallback.model is not None:
                    request = actionCallback.model.inputType.validate(request, acceptString = acceptString)
            except ValidationError as e:
                raise ActionErrorInternal("InvalidInput", str(e), e.member)

            # Call the action callback
            try:
                response = actionCallback(actionContext, Struct(request))
            except ActionError as e:
                response = { "error": e.error }
                if e.message is not None:
                    response["message"] = e.message
            except Exception as e:
                raise ActionErrorInternal("UnexpectedError", self._exceptionErrorMessage(e))

            # Validate the response
            if actionCallback.model is not None and actionCallback.validateResponse:
                try:
                    if "error" in response:
                        responseTypeInst = self._errorResponseTypeInst(actionCallback.model.errorType)
                    else:
                        responseTypeInst = actionCallback.model.outputType
                    response = responseTypeInst.validate(response)
                except ValidationError as e:
                    raise ActionErrorInternal("InvalidOutput", str(e), e.member)

            # Custom response serialization?
            if actionCallback.responseCallback is not None:
                try:
                    # Response callbacks respect the headersCallback
                    def _start_response(status, responseHeaders):
                        if self._headersCallback:
                            responseHeaders = list(responseHeaders)
                            responseHeaders.extend(self._headersCallback(actionContext))
                        return start_response(status, responseHeaders)

                    # Response callbacks must respond as WSGI app (call start_response and return content)
                    return actionCallback.responseCallback(environ, _start_response, actionContext, Struct(request), Struct(response))
                except Exception as e:
                    raise ActionErrorInternal("UnexpectedError", self._exceptionErrorMessage(e))

        except ActionErrorInternal as e:

            response = { "error": e.error }
            if e.message is not None:
                response["message"] = e.message
            if e.member is not None:
                response["member"] = e.member

        # Serialize the response as JSON
        jsonContent = self._serializeJSON(response)

        # Determine the HTTP status
        if "error" in response  and jsonpFunction is None:
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

        actionPath = ActionPath(environ["REQUEST_METHOD"], environ["PATH_INFO"])
        actionCallback = self._actionPaths.get(actionPath)
        envQueryString = environ.get("QUERY_STRING")
        try:
            envContentLength = int(environ.get("CONTENT_LENGTH"))
        except:
            envContentLength = None
        envWsgiInput = environ.get("wsgi.input")

        # Split the request URL
        pathParts = actionPath.path.strip("/").split("/")

        # Doc index page resource?
        if len(pathParts) == 1 and pathParts[0] == self._docUriDir:

            if actionPath.method == "GET":

                # Generate the doc index HTML
                docRootUrl = self._docUriDir
                actionModels = [actionModel for actionModel in itervalues(self._specParser.actions) \
                                    if actionModel.name in self._actionCallbacks]
                responseBody = createIndexHtml(docRootUrl, actionModels, docCssUri = self._docCssUri)
                return self._httpResponse(start_response, None, "200 OK", "text/html", responseBody)

            else:
                return self._http405MethodNotAllowed(start_response)

        # Action doc page resource?
        elif len(pathParts) == 2 and pathParts[0] == self._docUriDir and pathParts[1] in self._actionCallbacks:

            actionName = pathParts[1]

            if actionPath.method == "GET":

                # Generate the action doc HTML
                docRootUrl = self._docUriDir
                actionModel = self._specParser.actions[actionName]
                responseBody = createActionHtml(docRootUrl, actionModel, docCssUri = self._docCssUri)
                return self._httpResponse(start_response, None, "200 OK", "text/html", responseBody)

            else:
                return self._http405MethodNotAllowed(start_response)

        # Action request?
        elif actionCallback is not None:

            if actionPath.method == "GET":

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
                return self._actionResponse(environ, start_response, actionCallback, request, actionError = actionError,
                                            acceptString = True, jsonpFunction = jsonpFunction)

            elif actionPath.method == "POST":

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
                return self._actionResponse(environ, start_response, actionCallback, request, actionError = actionError)

            else:
                return self._http405MethodNotAllowed(start_response)

        # Resource not found
        return self._http404NotFound(environ, start_response)
