# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel action class
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
    Decorator for creating an :class:`~chisel.Action` object that wraps an action callback function. For example:

    >>> import chisel
    ...
    >>> @chisel.action(spec='''
    ... # Sum a list of numbers
    ... action sum_numbers
    ...     url
    ...         GET
    ...     query
    ...         # The list of numbers to sum
    ...         int[len > 0] numbers
    ...     output
    ...         # The sum of the numbers
    ...         int sum
    ... ''')
    ... def sum_numbers(ctx, req):
    ...    return {'sum': sum(req['numbers'])}
    ...
    >>> application = chisel.Application()
    >>> application.add_request(sum_numbers)
    >>> application.request('GET', '/sum_numbers', query_string='numbers.0=1&numbers.1=2&numbers.2=3')
    ('200 OK', [('Content-Type', 'application/json')], b'{"sum":6}')

    Chisel actions schema-validate their input before calling the callback function. For example:

    >>> status, _, response = application.request('GET', '/sum_numbers', query_string='numbers=1')
    >>> status
    '400 Bad Request'

    >>> import json
    >>> from pprint import pprint
    >>> pprint(json.loads(response.decode('utf-8')))
    {'error': 'InvalidInput',
     'member': 'numbers',
     'message': "Invalid value '1' (type 'str') for member 'numbers', expected "
                "type 'array' (query string)"}

    When :attr:`~chisel.Application.validate_output` the response dictionary is also validated to the output schema.

    :param ~collections.abc.Callable action_callback: The action callback function
    """

    if action_callback is None:
        return partial(action, **kwargs)
    return Action(action_callback, **kwargs).decorate_module(action_callback)


class ActionError(Exception):
    """
    An action error exception. Raise this exception within an action callback function to respond with an error.

    >>> import chisel
    ...
    >>> @chisel.action(spec='''
    ... action my_action
    ...     url
    ...         GET
    ...     errors
    ...         AlwaysError
    ... ''')
    ... def my_action(ctx, req):
    ...    raise chisel.ActionError('AlwaysError')
    ...
    >>> application = chisel.Application()
    >>> application.add_request(my_action)
    >>> application.request('GET', '/my_action')
    ('400 Bad Request', [('Content-Type', 'application/json')], b'{"error":"AlwaysError"}')

    :param str error: The error code
    :param str message: Optional error message
    :param status: The HTTP response status
    :type status: ~http.HTTPStatus or str
    """

    __slots__ = ('error', 'message', 'status')

    def __init__(self, error, message=None, status=None):
        super().__init__(error)

        #: The error code
        self.error = error

        #: The error message or None
        self.message = message

        #: The HTTP response status
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
    A schema-validated, JSON API request. An Action wraps a callback function that it calls when a request occurs. Here's
    an example of an action callback function:

    >>> def my_action(ctx, req):
    ...    return {}

    The first arugument, "ctx", is the :class:`~chisel.Context` object. The second argument is the request object which
    contiains the schema-validated, combined path parameters, query string parameters, and JSON request content
    parameters.

    :param ~collections.abc.Callable action_callback: The action callback function
    :param str name: The action request name
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    :param str doc: The documentation markdown text
    :param str doc_group: The documentation group
    :param ~chisel.SpecParser spec_parser: Optional specification parser to use for specification parsing
    :param str spec: Optional action specification (see :ref:`spec`). If a specification isn't provided it can be
        provided through the "spec_parser" argument.
    :param bool wsgi_response: If True, the callback function's response is a WSGI application function
        response. Default is False.
    :param str jsonp: Optional JSONP key
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

        #: The action callback function
        self.action_callback = action_callback

        #: The action's :class:`~chisel.ActionModel` object. This is retrieved from the spec/spec_parser
        #: attr:`~chisel.SpecParser.actions` collection.
        self.model = model

        #: If True, the callback function's response is a WSGI application function response.
        self.wsgi_response = wsgi_response

        #: JSONP key or None
        self.jsonp = jsonp

    def __call__(self, environ, unused_start_response):
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
