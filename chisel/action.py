# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from cgi import parse_header
from http import HTTPStatus
from json import loads as json_loads

from .app_defs import Environ
from .model import ValidationError, ValidationMode, TypeStruct, TYPE_STRING
from .request import Request
from .spec import SpecParser
from .url import decode_query_string


def action(_action_callback=None, **kwargs):
    """
    Chisel action request decorator
    """
    if _action_callback is None:
        return lambda fn: action(fn, **kwargs)
    else:
        return Action(_action_callback, **kwargs).decorate_module(_action_callback)


class ActionError(Exception):
    """
    Action error response exception
    """

    __slots__ = ('error', 'message', 'status')

    def __init__(self, error, message=None, status=None):
        super().__init__(error)
        self.error = error
        self.message = message
        self.status = status


class _ActionErrorInternal(Exception):
    __slots__ = ('status', 'error', 'message', 'member')

    def __init__(self, status, error, message=None, member=None):
        super().__init__(error)
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
        parser = spec if isinstance(spec, SpecParser) else SpecParser(spec=spec)
        model = parser.actions.get(name)
        assert model is not None, 'Unknown action "{0}"'.format(name)

        super().__init__(name=name, method=method, urls=urls,
                         doc=doc if doc is not None else model.doc,
                         doc_group=doc_group if doc_group is not None else model.doc_group)
        self.action_callback = action_callback
        self.model = model
        self.wsgi_response = wsgi_response
        self.jsonp = jsonp

    def __call__(self, environ, unused_start_response):
        ctx = environ[Environ.CTX]

        # Handle the action
        is_get = (environ['REQUEST_METHOD'] == 'GET')
        jsonp = None
        try:
            # Read the request content
            try:
                content = None if is_get else environ['wsgi.input'].read()
            except:
                ctx.log.warning("I/O error reading input for action '%s'", self.name)
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'IOError', message='Error reading request content')

            # De-serialize the JSON content
            validation_mode = ValidationMode.JSON_INPUT
            try:
                if content:
                    content_type = environ.get('CONTENT_TYPE')
                    content_charset = ('utf-8' if content_type is None else parse_header(content_type)[1].get('charset', 'utf-8'))
                    content_json = content.decode(content_charset)
                    request = json_loads(content_json)
                else:
                    request = {}
            except Exception as exc:
                ctx.log.warning("Error decoding JSON content for action '%s'", self.name)
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message='Invalid request JSON: ' + str(exc))

            # Fail non-dictionary requests
            if not isinstance(request, dict):
                ctx.log.warning("Invalid top-level JSON object of type '%s': %.1000r", type(request).__name__, content_json)
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message="Invalid top-level JSON object of type '{0}'".format(type(request).__name__)
                )

            # Decode the query string
            query_string = environ.get('QUERY_STRING')
            if query_string:
                validation_mode = ValidationMode.QUERY_STRING
                try:
                    request_query_string = decode_query_string(query_string)
                except Exception as exc:
                    ctx.log.warning("Error decoding query string for action '%s': %.1000r", self.name, environ.get('QUERY_STRING', ''))
                    raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message=str(exc))

                for request_key, request_value in request_query_string.items():
                    if request_key in request:
                        ctx.log.warning("Duplicate query string argument member %.100r for action '%s'", request_key, self.name)
                        raise _ActionErrorInternal(
                            HTTPStatus.BAD_REQUEST,
                            'InvalidInput',
                            message="Duplicate query string argument member {0!r:.100s}".format(request_key)
                        )
                    request[request_key] = request_value

            # Add url arguments
            if ctx.url_args is not None:
                validation_mode = ValidationMode.QUERY_STRING
                for url_arg, url_value in ctx.url_args.items():
                    if url_arg in request:
                        ctx.log.warning("Duplicate URL argument member %r for action '%s'", url_arg, self.name)
                        raise _ActionErrorInternal(
                            HTTPStatus.BAD_REQUEST,
                            'InvalidInput',
                            message="Duplicate URL argument member {0!r}".format(url_arg)
                        )
                    request[url_arg] = url_value

            # JSONP?
            if is_get and self.jsonp and self.jsonp in request:
                jsonp = str(request[self.jsonp])
                del request[self.jsonp]

            # Validate the request
            try:
                request = self.model.input_type.validate(request, validation_mode)
            except ValidationError as exc:
                ctx.log.warning("Invalid input for action '%s': %s", self.name, str(exc))
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message=str(exc), member=exc.member)

            # Call the action callback
            try:
                status = HTTPStatus.OK
                response = self.action_callback(ctx, request)
                if self.wsgi_response:
                    return response
                elif response is None:
                    response = {}
                response_type = self.model.output_type
            except ActionError as exc:
                status = exc.status or HTTPStatus.BAD_REQUEST
                response = {'error': exc.error}
                if exc.message is not None:
                    response['message'] = exc.message
                if ctx.app.validate_output:
                    response_type = TypeStruct()
                    response_type.add_member('error', self.model.error_type)
                    response_type.add_member('message', TYPE_STRING, optional=True)
            except Exception as exc:
                ctx.log.exception("Unexpected error in action '%s'", self.name)
                raise _ActionErrorInternal(HTTPStatus.INTERNAL_SERVER_ERROR, 'UnexpectedError')

            # Validate the response
            if ctx.app.validate_output:
                try:
                    response_type.validate(response)
                except ValidationError as exc:
                    ctx.log.error("Invalid output returned from action '%s': %s", self.name, str(exc))
                    raise _ActionErrorInternal(HTTPStatus.INTERNAL_SERVER_ERROR, 'InvalidOutput', message=str(exc), member=exc.member)

        except _ActionErrorInternal as exc:
            status = exc.status
            response = {'error': exc.error}
            if exc.message is not None:
                response['message'] = exc.message
            if exc.member is not None:
                response['member'] = exc.member

        # Serialize the response as JSON
        return ctx.response_json(status, response, jsonp=jsonp)
