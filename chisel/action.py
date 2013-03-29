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

from .compat import itervalues
from .model import ValidationError, TypeStruct, TypeString
from .request import Request
from .spec import SpecParser
from .struct import Struct
from .url import decodeQueryString

import json


# Action error response exception
class ActionError(Exception):
    def __init__(self, error, message = None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message


# Internal action error response exception
class _ActionErrorInternal(Exception):
    def __init__(self, error, message = None, member = None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message
        self.member = member


# Action callback decorator
class Action(Request):

    JSONP = "jsonp"

    def __init__(self, _fn = None, name = None, urls = None, spec = None, response = None):

        # Spec provided?
        self.model = None
        if spec is not None:
            specParser = SpecParser()
            specParser.parseString(spec)
            if name is not None:
                self.model = specParser.actions[name]
            else:
                assert len(specParser.actions) == 1, "Action specification must contain exactly one action definition"
                for self.model in itervalues(specParser.actions):
                    break

        # Use the action model name, if available
        if name is None and self.model is not None:
            name = self.model.name

        self.response = response
        Request.__init__(self, _fn = _fn, name = name, urls = urls)

    def onload(self, app):

        # Get the action model, if necessary
        if self.model is None:
            self.model = app.specs.actions.get(self.name)
            if self.model is None:
                raise Exception("No model defined for action callback '%s'" % (self.name,))

        Request.onload(self, app)

    def call(self, environ, start_response):

        # Check the method
        isGet = (environ["REQUEST_METHOD"] == "GET")
        if not isGet and environ["REQUEST_METHOD"] != "POST":
            return self.app.response("405 Method Not Allowed", "text/plain", "Method Not Allowed")

        # Handle the action
        jsonpFunction = None
        try:
            # Get the input struct
            if environ["REQUEST_METHOD"] == "GET":

                # Decode the query string
                try:
                    request = decodeQueryString(environ.get("QUERY_STRING", ""))
                except Exception as e:
                    raise _ActionErrorInternal("InvalidInput", str(e))

            elif environ["REQUEST_METHOD"] == "POST":

                # Get the content length
                try:
                    contentLength = int(environ["CONTENT_LENGTH"])
                except:
                    return self.app.response("411 Length Required", "text/plain", "Length Required")

                # Read the request content
                try:
                    requestContent = environ["wsgi.input"].read(contentLength)
                except:
                    raise _ActionErrorInternal("IOError", "Error reading request content")

                # De-serialize the JSON request
                try:
                    request = json.loads(requestContent)
                except Exception as e:
                    raise _ActionErrorInternal("InvalidInput", "Invalid request JSON: %s" % (str(e)))

            # JSONP?
            if isGet and self.JSONP in request:
                jsonpFunction = str(request[self.JSONP])
                del request[self.JSONP]

            # Validate the request
            try:
                request = self.model.inputType.validate(request, acceptString = isGet)
            except ValidationError as e:
                raise _ActionErrorInternal("InvalidInput", str(e), e.member)

            # Call the action callback
            try:
                response = self.fn(self.app, Struct(request))
            except ActionError as e:
                response = { "error": e.error }
                if e.message is not None:
                    response["message"] = e.message
            except Exception as e:
                raise _ActionErrorInternal("UnexpectedError", self.app.exceptionErrorMessage(e))

            # Validate the response
            try:
                if isinstance(response, (dict, Struct)) and "error" in response:
                    responseTypeInst = TypeStruct()
                    responseTypeInst.members.append(TypeStruct.Member("error", self.model.errorType))
                    responseTypeInst.members.append(TypeStruct.Member("message", TypeString(), isOptional = True))
                else:
                    responseTypeInst = self.model.outputType
                response = responseTypeInst.validate(response)
            except ValidationError as e:
                raise _ActionErrorInternal("InvalidOutput", str(e), e.member)

            # Custom response serialization?
            if self.response is not None:
                try:
                    return self.response(self.app, Struct(request), Struct(response))
                except Exception as e:
                    raise _ActionErrorInternal("UnexpectedError", self.app.exceptionErrorMessage(e))

        except _ActionErrorInternal as e:
            response = { "error": e.error }
            if e.message is not None:
                response["message"] = e.message
            if e.member is not None:
                response["member"] = e.member

        # Serialize the response as JSON
        try:
            jsonContent = self.app.serializeJSON(response)
        except Exception as e:
            response = { "error": "InvalidOutput", "message": self.app.exceptionErrorMessage(e) }
            jsonContent = self.app.serializeJSON(response)

        # Determine the HTTP status
        if "error" in response  and jsonpFunction is None:
            status = "500 Internal Server Error"
        else:
            status = "200 OK"

        # Send the response
        if jsonpFunction:
            return self.app.response(status, "application/json", jsonpFunction, "(", jsonContent, ");")
        else:
            return self.app.response(status, "application/json", jsonContent)
