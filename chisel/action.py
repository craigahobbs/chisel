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

from .app import Application
from .compat import func_name, iteritems, itervalues
from .model import VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT, VALIDATE_JSON_OUTPUT, ValidationError, TypeStruct, TypeString
from .request import Request
from .spec import SpecParser
from .url import decodeQueryString

import cgi
import json


def action(_action_callback=None, name=None, urls=None, spec=None, wsgiResponse=False):
    """
    Chisel action request decorator
    """

    if _action_callback is None:
        return lambda fn: Action(fn, name=name, urls=urls, spec=spec, wsgiResponse=wsgiResponse)
    return Action(_action_callback, name=name, urls=urls, spec=spec, wsgiResponse=wsgiResponse)


class ActionError(Exception):
    """
    Action error response exception
    """

    __slots__ = ('error', 'message')

    def __init__(self, error, message=None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message


class _ActionErrorInternal(Exception):
    __slots__ = ('error', 'message', 'member')

    def __init__(self, error, message=None, member=None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message
        self.member = member


class Action(Request):
    """
    Chisel action request
    """

    __slots__ = ('action_callback', 'model', 'wsgiResponse')

    JSONP = 'jsonp'

    def __init__(self, action_callback, name=None, urls=None, spec=None, wsgiResponse=False):

        # Spec provided?
        model = None
        if spec is not None:
            specParser = SpecParser()
            specParser.parseString(spec)
            if name is not None:
                model = specParser.actions[name]
            else:
                assert len(specParser.actions) == 1, 'Action spec must contain exactly one action definition'
                model = next(itervalues(specParser.actions))

        # Use the action model name, if available
        if name is None:
            name = model.name if model is not None else func_name(action_callback)

        Request.__init__(self, self._wsgi_callback, name=name, urls=urls)
        self.action_callback = action_callback
        self.model = model
        self.wsgiResponse = wsgiResponse

    def onload(self, app):
        Request.onload(self, app)

        # Get the action model, if necessary
        if self.model is None:
            self.model = app.specs.actions.get(self.name)
            assert self.model is not None, "No spec defined for action '%s'" % (self.name,)

    def _wsgi_callback(self, environ, dummy_start_response):
        ctx = environ[Application.ENVIRON_APP]
        urlArgs = environ.get(Application.ENVIRON_URL_ARGS)

        # Check the method
        isGet = (environ['REQUEST_METHOD'] == 'GET')
        if not isGet and environ['REQUEST_METHOD'] != 'POST':
            return ctx.responseText('405 Method Not Allowed', 'Method Not Allowed')

        # Handle the action
        try:
            # Get the input dict
            if isGet:

                # Decode the query string
                validateMode = VALIDATE_QUERY_STRING
                try:
                    request = decodeQueryString(environ.get('QUERY_STRING', ''))
                except Exception as e:
                    ctx.log.warning("Error decoding query string for action '%s': %s", self.name, environ.get('QUERY_STRING', ''))
                    raise _ActionErrorInternal('InvalidInput', str(e))

            else:

                # Get the content length
                try:
                    contentLength = int(environ['CONTENT_LENGTH'])
                except ValueError:
                    ctx.log.warning("Invalid content length for action '%s': %s", self.name, environ.get('CONTENT_LENGTH', ''))
                    return ctx.responseText('411 Length Required', 'Length Required')

                # Read the request content
                try:
                    requestContent = environ['wsgi.input'].read(contentLength)
                except:
                    ctx.log.warning("I/O error reading input for action '%s'", self.name)
                    raise _ActionErrorInternal('IOError', 'Error reading request content')

                # De-serialize the JSON request
                validateMode = VALIDATE_JSON_INPUT
                try:
                    contentTypeHeader = environ.get('CONTENT_TYPE')
                    contentCharset = ('utf-8' if contentTypeHeader is None else
                                      cgi.parse_header(contentTypeHeader)[1].get('charset', 'utf-8'))
                    request = json.loads(requestContent.decode(contentCharset))
                except Exception as e:
                    ctx.log.warning("Error decoding JSON content for action '%s': %s", self.name, requestContent)
                    raise _ActionErrorInternal('InvalidInput', 'Invalid request JSON: ' + str(e))

            # JSONP?
            if isGet and self.JSONP in request:
                ctx.setJSONP(str(request[self.JSONP]))
                del request[self.JSONP]

            # Add url arguments
            if urlArgs is not None:
                validateMode = VALIDATE_QUERY_STRING
                for urlArg, urlValue in iteritems(urlArgs):
                    if urlArg in request or urlArg == self.JSONP:
                        ctx.log.warning("Duplicate URL argument member '%s' for action '%s'", urlArg, self.name)
                        raise _ActionErrorInternal('InvalidInput', "Duplicate URL argument member '%s'" % (urlArg,))
                    request[urlArg] = urlValue

            # Validate the request
            try:
                request = self.model.inputType.validate(request, validateMode)
            except ValidationError as e:
                ctx.log.warning("Invalid input for action '%s': %s", self.name, str(e))
                raise _ActionErrorInternal('InvalidInput', str(e), e.member)

            # Call the action callback
            try:
                response = self.action_callback(ctx, request)
                if self.wsgiResponse:
                    return response
                elif response is None:
                    response = {}
            except ActionError as e:
                response = {'error': e.error}
                if e.message is not None:
                    response['message'] = e.message
            except Exception as e:
                ctx.log.exception("Unexpected error in action '%s'", self.name)
                raise _ActionErrorInternal('UnexpectedError')

            # Validate the response
            if ctx.validateOutput:
                if hasattr(response, '__contains__') and 'error' in response:
                    responseType = TypeStruct()
                    responseType.addMember('error', self.model.errorType)
                    responseType.addMember('message', TypeString(), isOptional=True)
                else:
                    responseType = self.model.outputType

                try:
                    responseType.validate(response, mode=VALIDATE_JSON_OUTPUT)
                except ValidationError as e:
                    ctx.log.error("Invalid output returned from action '%s': %s", self.name, str(e))
                    raise _ActionErrorInternal('InvalidOutput', str(e), e.member)

        except _ActionErrorInternal as e:
            response = {'error': e.error}
            if e.message is not None:
                response['message'] = e.message
            if e.member is not None:
                response['member'] = e.member

        # Serialize the response as JSON
        return ctx.responseJSON(response, isError='error' in response)
