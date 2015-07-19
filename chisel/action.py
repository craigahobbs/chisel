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

from .compat import iteritems, itervalues
from .model import VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT, VALIDATE_JSON_OUTPUT, ValidationError, TypeStruct, TypeString
from .request import Request
from .spec import SpecParser
from .url import decodeQueryString

import cgi
import json


# Action error response exception
class ActionError(Exception):
    __slots__ = ('error', 'message')

    def __init__(self, error, message=None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message


# Internal action error response exception
class _ActionErrorInternal(Exception):
    __slots__ = ('error', 'message', 'member')

    def __init__(self, error, message=None, member=None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message
        self.member = member


# Action callback decorator
class Action(Request):
    __slots__ = ('model', 'wsgiResponse', 'strictValidation')

    JSONP = 'jsonp'

    def __init__(self, _fn=None, name=None, urls=None, spec=None, wsgiResponse=False,
                 strictValidation=True):

        # Spec provided?
        self.model = None
        if spec is not None:
            specParser = SpecParser()
            specParser.parseString(spec)
            if name is not None:
                self.model = specParser.actions[name]
            else:
                assert len(specParser.actions) == 1, 'Action spec must contain exactly one action definition'
                self.model = next(itervalues(specParser.actions))

        # Use the action model name, if available
        if name is None and self.model is not None:
            name = self.model.name

        self.wsgiResponse = wsgiResponse
        self.strictValidation = strictValidation
        Request.__init__(self, _fn=_fn, name=name, urls=urls)

    def onload(self, app):

        # Get the action model, if necessary
        if self.model is None:
            self.model = app.specs.actions.get(self.name)
            assert self.model is not None, "No spec defined for action '%s'" % (self.name,)

        Request.onload(self, app)

    def call(self, environ, start_response):

        # Check the method
        isGet = (environ['REQUEST_METHOD'] == 'GET')
        if not isGet and environ['REQUEST_METHOD'] != 'POST':
            return self.app.responseText('405 Method Not Allowed', 'Method Not Allowed')

        # Handle the action
        try:
            # Get the input dict
            if isGet:

                # Decode the query string
                validateMode = VALIDATE_QUERY_STRING
                try:
                    request = decodeQueryString(environ.get('QUERY_STRING', ''))
                except Exception as e:
                    self.app.log.warning("Error decoding query string for action '%s': %s", self.name, environ.get('QUERY_STRING', ''))
                    raise _ActionErrorInternal('InvalidInput', str(e))

            else:

                # Get the content length
                try:
                    contentLength = int(environ['CONTENT_LENGTH'])
                except ValueError:
                    self.app.log.warning("Invalid content length for action '%s': %s", self.name, environ.get('CONTENT_LENGTH', ''))
                    return self.app.responseText('411 Length Required', 'Length Required')

                # Read the request content
                try:
                    requestContent = environ['wsgi.input'].read(contentLength)
                except:
                    self.app.log.warning("I/O error reading input for action '%s'", self.name)
                    raise _ActionErrorInternal('IOError', 'Error reading request content')

                # De-serialize the JSON request
                validateMode = VALIDATE_JSON_INPUT if self.strictValidation else VALIDATE_QUERY_STRING
                try:
                    contentTypeHeader = environ.get('CONTENT_TYPE')
                    contentCharset = ('utf-8' if contentTypeHeader is None else
                                      cgi.parse_header(contentTypeHeader)[1].get('charset', 'utf-8'))
                    request = json.loads(requestContent.decode(contentCharset))
                except Exception as e:
                    self.app.log.warning("Error decoding JSON content for action '%s': %s", self.name, requestContent)
                    raise _ActionErrorInternal('InvalidInput', 'Invalid request JSON: ' + str(e))

            # JSONP?
            if isGet and self.JSONP in request:
                self.app.setJSONP(str(request[self.JSONP]))
                del request[self.JSONP]

            # Add url arguments
            urlArgs = environ.get(self.app.ENVIRON_URL_ARGS)
            if urlArgs:
                validateMode = VALIDATE_QUERY_STRING
                for urlArg, urlValue in iteritems(urlArgs):
                    if urlArg in request or urlArg == self.JSONP:
                        self.app.log.warning("Duplicate URL argument member '%s' for action '%s'", urlArg, self.name)
                        raise _ActionErrorInternal('InvalidInput', "Duplicate URL argument member '%s'" % (urlArg,))
                    request[urlArg] = urlValue

            # Validate the request
            try:
                request = self.model.inputType.validate(request, validateMode)
            except ValidationError as e:
                self.app.log.warning("Invalid input for action '%s': %s", self.name, str(e))
                raise _ActionErrorInternal('InvalidInput', str(e), e.member)

            # Call the action callback
            try:
                response = self.fn(self.app, request)
                if self.wsgiResponse:
                    return response
                elif response is None:
                    response = {}
            except ActionError as e:
                response = {'error': e.error}
                if e.message is not None:
                    response['message'] = e.message
            except Exception as e:
                self.app.log.exception("Unexpected error in action '%s'", self.name)
                raise _ActionErrorInternal('UnexpectedError')

            # Validate the response
            if self.app.validateOutput:
                if hasattr(response, '__contains__') and 'error' in response:
                    responseType = TypeStruct()
                    responseType.addMember('error', self.model.errorType)
                    responseType.addMember('message', TypeString(), isOptional=True)
                else:
                    responseType = self.model.outputType

                try:
                    responseType.validate(response, mode=VALIDATE_JSON_OUTPUT)
                except ValidationError as e:
                    self.app.log.error("Invalid output returned from action '%s': %s", self.name, str(e))
                    raise _ActionErrorInternal('InvalidOutput', str(e), e.member)

        except _ActionErrorInternal as e:
            response = {'error': e.error}
            if e.message is not None:
                response['message'] = e.message
            if e.member is not None:
                response['member'] = e.member

        # Serialize the response as JSON
        return self.app.responseJSON(response, isError='error' in response)
