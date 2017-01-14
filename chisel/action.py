#
# Copyright (C) 2012-2016 Craig Hobbs
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

from cgi import parse_header
from json import loads as json_loads

from .app_defs import ENVIRON_CTX, STATUS_200_OK, STATUS_400_BAD_REQUEST, STATUS_500_INTERNAL_SERVER_ERROR
from .model import VALIDATE_DEFAULT, VALIDATE_QUERY_STRING, VALIDATE_JSON_INPUT, ValidationError, TypeStruct, TYPE_STRING
from .request import Request
from .spec import SpecParser
from .url import decode_query_string


def action(_action_callback=None, **kwargs):
    """
    Chisel action request decorator
    """
    return Action(_action_callback, **kwargs).decorate_module(_action_callback) if _action_callback else lambda fn: action(fn, **kwargs)


class ActionError(Exception):
    """
    Action error response exception
    """

    __slots__ = ('error', 'message', 'status')

    def __init__(self, error, message=None, status=None):
        Exception.__init__(self, error)
        self.error = error
        self.message = message
        self.status = status


class _ActionErrorInternal(Exception):
    __slots__ = ('status', 'error', 'message', 'member')

    def __init__(self, status, error, message=None, member=None):
        Exception.__init__(self, error)
        self.status = status
        self.error = error
        self.message = message
        self.member = member


class Action(Request):
    """
    Chisel action request
    """

    __slots__ = ('action_callback', 'model', 'wsgi_response', 'jsonp')

    def __init__(self, action_callback, name=None, method=('GET', 'POST'), urls=None, doc=None, doc_group=None,
                 spec=None, wsgi_response=False, jsonp=None):

        # Use the action model name, if available
        if name is None:
            name = action_callback.__name__

        # Spec provided?
        model = None
        doc = doc
        doc_group = doc_group
        if spec is not None:
            parser = spec if isinstance(spec, SpecParser) else SpecParser(spec=spec)
            assert name in parser.actions, 'Unknown action "{0}"'.format(name)
            model = parser.actions[name]
            if doc is None:
                doc = model.doc
            if doc_group is None:
                doc_group = model.doc_group

        Request.__init__(self, name=name, method=method, urls=urls, doc=doc, doc_group=doc_group)
        self.action_callback = action_callback
        self.model = model
        self.wsgi_response = wsgi_response
        self.jsonp = jsonp

    def onload(self, app):
        Request.onload(self, app)

        # Get the action model, if necessary
        if self.model is None:
            self.model = app.specs.actions.get(self.name)
            assert self.model is not None, "No spec defined for action '{0}'".format(self.name)
            if self.doc is None:
                self.doc = self.model.doc
            if self.doc_group is None:
                self.doc_group = self.model.doc_group

    def __call__(self, environ, dummy_start_response):
        ctx = environ[ENVIRON_CTX]

        # Handle the action
        is_get = (environ['REQUEST_METHOD'] == 'GET')
        jsonp = None
        try:
            # Read the request content
            try:
                content = None if is_get else environ['wsgi.input'].read()
            except:
                ctx.log.warning("I/O error reading input for action '%s'", self.name)
                raise _ActionErrorInternal(STATUS_400_BAD_REQUEST, 'IOError', message='Error reading request content')

            # De-serialize the JSON content
            validate_mode = VALIDATE_JSON_INPUT
            try:
                if content:
                    content_type = environ.get('CONTENT_TYPE')
                    content_charset = ('utf-8' if content_type is None else parse_header(content_type)[1].get('charset', 'utf-8'))
                    request = json_loads(content.decode(content_charset))
                else:
                    request = {}
            except Exception as exc:
                ctx.log.warning("Error decoding JSON content for action '%s'", self.name)
                raise _ActionErrorInternal(STATUS_400_BAD_REQUEST, 'InvalidInput', message='Invalid request JSON: ' + str(exc))

            # Decode the query string
            query_string = environ.get('QUERY_STRING')
            if query_string:
                validate_mode = VALIDATE_QUERY_STRING
                try:
                    request_query_string = decode_query_string(query_string)
                except Exception as exc:
                    ctx.log.warning("Error decoding query string for action '%s': %s", self.name, environ.get('QUERY_STRING', ''))
                    raise _ActionErrorInternal(STATUS_400_BAD_REQUEST, 'InvalidInput', message=str(exc))

                for request_key, request_value in request_query_string.items():
                    if request_key in request:
                        ctx.log.warning("Duplicate query string argument member '%s' for action '%s'", request_key, self.name)
                        raise _ActionErrorInternal(
                            STATUS_400_BAD_REQUEST,
                            'InvalidInput',
                            message="Duplicate query string argument member '{0}'".format(request_key)
                        )
                    request[request_key] = request_value

            # Add url arguments
            if ctx.url_args is not None:
                validate_mode = VALIDATE_QUERY_STRING
                for url_arg, url_value in ctx.url_args.items():
                    if url_arg in request:
                        ctx.log.warning("Duplicate URL argument member '%s' for action '%s'", url_arg, self.name)
                        raise _ActionErrorInternal(
                            STATUS_400_BAD_REQUEST,
                            'InvalidInput',
                            message="Duplicate URL argument member '{0}'".format(url_arg)
                        )
                    request[url_arg] = url_value

            # JSONP?
            if is_get and self.jsonp and self.jsonp in request:
                jsonp = str(request[self.jsonp])
                del request[self.jsonp]

            # Validate the request
            try:
                request = self.model.input_type.validate(request, validate_mode)
            except ValidationError as exc:
                ctx.log.warning("Invalid input for action '%s': %s", self.name, str(exc))
                raise _ActionErrorInternal(STATUS_400_BAD_REQUEST, 'InvalidInput', message=str(exc), member=exc.member)

            # Call the action callback
            try:
                status = STATUS_200_OK
                response = self.action_callback(ctx, request)
                if self.wsgi_response:
                    return response
                elif response is None:
                    response = {}
                response_type = self.model.output_type
            except ActionError as exc:
                status = exc.status or STATUS_400_BAD_REQUEST
                response = {'error': exc.error}
                if exc.message is not None:
                    response['message'] = exc.message
                if ctx.app.validate_output:
                    response_type = TypeStruct()
                    response_type.add_member('error', self.model.error_type)
                    response_type.add_member('message', TYPE_STRING, optional=True)
            except Exception as exc:
                ctx.log.exception("Unexpected error in action '%s'", self.name)
                raise _ActionErrorInternal(STATUS_500_INTERNAL_SERVER_ERROR, 'UnexpectedError')

            # Validate the response
            if ctx.app.validate_output:
                try:
                    response_type.validate(response, mode=VALIDATE_DEFAULT)
                except ValidationError as exc:
                    ctx.log.error("Invalid output returned from action '%s': %s", self.name, str(exc))
                    raise _ActionErrorInternal(STATUS_500_INTERNAL_SERVER_ERROR, 'InvalidOutput', message=str(exc), member=exc.member)

        except _ActionErrorInternal as exc:
            status = exc.status
            response = {'error': exc.error}
            if exc.message is not None:
                response['message'] = exc.message
            if exc.member is not None:
                response['member'] = exc.member

        # Serialize the response as JSON
        return ctx.response_json(status, response, jsonp=jsonp)
