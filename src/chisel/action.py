# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from cgi import parse_header
from functools import partial
from http import HTTPStatus
from json import loads as json_loads

from .app import Context
from .model import ValidationError, ValidationMode, TypeStruct, TYPE_STRING
from .request import Request
from .spec import SpecParser
from .util import decode_query_string


def action(action_callback=None, **kwargs):
    """
    TODO
    """

    if action_callback is None:
        return partial(action, **kwargs)
    return Action(action_callback, **kwargs).decorate_module(action_callback)


class ActionError(Exception):
    """
    TODO
    """

    __slots__ = ('error', 'message', 'status')

    def __init__(self, error, message=None, status=None):
        super().__init__(error)

        #: TODO
        self.error = error

        #: TODO
        self.message = message

        #: TODO
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
    TODO
    """

    __slots__ = ('action_callback', 'model', 'wsgi_response', 'jsonp')

    def __init__(self, action_callback, name=None, urls=(('POST', None),), doc=None, doc_group=None,
                 spec_parser=None, spec=None, wsgi_response=False, jsonp=None):

        # Use the action model name, if available
        if name is None:
            name = action_callback.__name__

        # Spec provided?
        if spec_parser is None:
            spec_parser = SpecParser(spec=spec)
        elif spec is not None:
            spec_parser.parse_string(spec)
        model = spec_parser.actions.get(name)
        assert model is not None, f'Unknown action "{name}"'

        super().__init__(
            name=name,
            urls=model.urls or urls,
            doc=doc if doc is not None else model.doc,
            doc_group=doc_group if doc_group is not None else model.doc_group
        )

        #: TODO
        self.action_callback = action_callback

        #: TODO
        self.model = model

        #: TODO
        self.wsgi_response = wsgi_response

        #: TODO
        self.jsonp = jsonp

    def __call__(self, environ, unused_start_response):
        """
        TODO
        """

        ctx = environ[Context.ENVIRON_CTX]

        # Handle the action
        is_get = (environ['REQUEST_METHOD'] == 'GET')
        jsonp = None
        validate_output = True
        try:
            # Read the request content
            try:
                content = None if is_get else environ['wsgi.input'].read()
            except:
                raise _ActionErrorInternal(HTTPStatus.REQUEST_TIMEOUT, 'IOError', message='Error reading request content')

            # De-serialize the JSON content
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
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message=f'Invalid request JSON: {exc}')

            # Validate the content
            try:
                request = self.model.input_type.validate(request, ValidationMode.JSON_INPUT)
            except ValidationError as exc:
                ctx.log.warning("Invalid content for action '%s': %s", self.name, str(exc))
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message=f'{exc} (content)',
                    member=exc.member
                )

            # Decode the query string
            query_string = environ.get('QUERY_STRING', '')
            try:
                request_query = decode_query_string(query_string)
            except Exception as exc:
                ctx.log.warning("Error decoding query string for action '%s': %.1000r", self.name, query_string)
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message=str(exc))

            # JSONP?
            if is_get and self.jsonp and self.jsonp in request_query:
                jsonp = str(request_query[self.jsonp])
                del request_query[self.jsonp]

            # Validate the query string
            try:
                request_query = self.model.query_type.validate(request_query, ValidationMode.QUERY_STRING)
            except ValidationError as exc:
                ctx.log.warning("Invalid query string for action '%s': %s", self.name, str(exc))
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message=f'{exc} (query string)',
                    member=exc.member
                )

            # Validate the path args
            request_path = ctx.url_args if ctx.url_args is not None else {}
            try:
                request_path = self.model.path_type.validate(request_path, ValidationMode.QUERY_STRING)
            except ValidationError as exc:
                ctx.log.warning("Invalid path for action '%s': %s", self.name, str(exc))
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message=f'{exc} (path)',
                    member=exc.member
                )

            # Copy top-level path keys and query string keys
            for request_key, request_value in request_path.items():
                request[request_key] = request_value
            for request_key, request_value in request_query.items():
                request[request_key] = request_value

            # Call the action callback
            try:
                status = HTTPStatus.OK
                response = self.action_callback(ctx, request)
                if self.wsgi_response:
                    return response
                if response is None:
                    response = {}
                response_type = self.model.output_type
            except ActionError as exc:
                status = exc.status or HTTPStatus.BAD_REQUEST
                response = {'error': exc.error}
                if exc.message is not None:
                    response['message'] = exc.message
                if ctx.app.validate_output:
                    if exc.error in ('UnexpectedError',):
                        validate_output = False
                    else:
                        response_type = TypeStruct()
                        response_type.add_member('error', self.model.error_type)
                        response_type.add_member('message', TYPE_STRING, optional=True)
            except Exception as exc:
                ctx.log.exception("Unexpected error in action '%s'", self.name)
                raise _ActionErrorInternal(HTTPStatus.INTERNAL_SERVER_ERROR, 'UnexpectedError')

            # Validate the response
            if validate_output and ctx.app.validate_output:
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
