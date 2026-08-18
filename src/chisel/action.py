# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

"""
Chisel action class
"""

from functools import partial
from http import HTTPStatus
from json import loads as json_loads
import re

from bare_script.include import SchemaValidationError, url_decode_query_string, schema_get_referenced_types, schema_parse, schema_validate

from .app import Context
from .request import Request


# Regex for parsing the Content-Type header
RE_CONTENT_TYPE_HEADER = re.compile(r'(?:^|[;\s])charset\s*=\s*"?(?P<charset>[^";\s]+)', re.IGNORECASE)


def action(action_callback=None, **kwargs):
    """
    Decorator for creating an :class:`~chisel.Action` object that wraps an action callback function. For example:

    >>> @chisel.action(spec='''
    ... # Sum a list of numbers
    ... action sum_numbers
    ...     urls
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
    ('200 OK', [('Content-Type', 'application/json')], b'{"sum":6.0}')

    Chisel actions schema-validate their input before calling the callback function. For example:

    >>> status, _, response = application.request('GET', '/sum_numbers', query_string='numbers=1')
    >>> status
    '400 Bad Request'

    >>> import json
    >>> from pprint import pprint
    >>> pprint(json.loads(response.decode('utf-8')))
    {'error': 'InvalidInput',
     'member': 'numbers',
     'message': 'Invalid value "1" (type "string") for member "numbers", expected '
                'type "array" (query string)'}

    When :attr:`~chisel.Application.validate_output` is True, the response dictionary is also validated against the
    output schema.

    :param ~collections.abc.Callable action_callback: The action callback function
    """

    if action_callback is None:
        return partial(action, **kwargs)
    return Action(action_callback, **kwargs)


class ActionError(Exception):
    """
    An action error exception. Raise this exception within an action callback function to respond with an error.

    >>> @chisel.action(spec='''
    ... action my_action
    ...     urls
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

    The first argument, "ctx", is the :class:`~chisel.Context` object. The second argument is the request object which
    contains the schema-validated, combined path parameters, query string parameters, and JSON request content
    parameters.

    :param ~collections.abc.Callable action_callback: The action callback function
    :param str name: The action request name
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path. If the action's
        specification contains a "urls" section, the specification's URLs take precedence.
    :param dict types: Optional dictionary of user type models
    :param str spec: Optional action `Schema Markdown <https://craigahobbs.github.io/schema-markdown-js/language/>`__ specification.
        If a specification isn't provided it can be provided through the "types" argument.
    :param bool wsgi_response: If True, the callback function's response is a WSGI application function
        response. Default is False.
    """

    __slots__ = (
        'action_callback',
        'types',
        'wsgi_response',
        '_input_type',
        '_query_type',
        '_path_type',
        '_output_type',
        '_error_type'
    )

    def __init__(self, action_callback, name=None, urls=(('POST', None),), types=None, spec=None, wsgi_response=False):

        # Use the action callback name if no name is provided
        if name is None:
            name = action_callback.__name__

        # Spec provided?
        if types is None:
            types = {}
        if spec is not None:
            schema_parse(spec, types)

        # Assert that the action model exists
        model_type = types.get(name)
        model = model_type.get('action') if model_type is not None else None
        assert model is not None, f'Unknown action "{name}"'

        # Get the model's URLs, if any
        if 'urls' in model:
            urls = [(url.get('method'), url.get('path')) for url in model['urls']]

        # Initialize Request
        super().__init__(name=name, urls=urls, doc=model.get('doc'), doc_group=model.get('docGroup'))

        #: The action callback function
        self.action_callback = action_callback

        #: The user type model dictionary that contains the action model and all referenced user types
        self.types = types

        #: If True, the callback function's response is a WSGI application function response.
        self.wsgi_response = wsgi_response

        # Pre-compute the section types and the error response type
        self._input_type = self._get_section_type('input')
        self._query_type = self._get_section_type('query')
        self._path_type = self._get_section_type('path')
        self._output_type = self._get_section_type('output')
        self._error_type = self._get_error_type()

    @property
    def model(self):
        """Get the action model"""
        return self.types[self.name]['action']

    def _get_section_type(self, section):
        model = self.model
        if section in model:
            section_type_name = model[section]
            section_types = self.types
        else:
            # No section type - create an empty struct type
            section_type_name = f'{model["name"]}_{section}'
            section_types = {
                section_type_name: {
                    'struct': {
                        'name': section_type_name
                    }
                }
            }
        return section_types, section_type_name

    def _get_error_type(self):
        model = self.model
        output_type_name = f'{model["name"]}_output_error'
        if 'errors' in model:
            error_type_name = model['errors']
            output_types = schema_get_referenced_types(self.types, error_type_name)
        else:
            error_type_name = f'{model["name"]}_errors'
            output_types = {error_type_name: {'enum': {'name': error_type_name}}}

        output_types[output_type_name] = {
            'struct': {
                'name': output_type_name,
                'members': [
                    {'name': 'error', 'type': {'user': error_type_name}},
                    {'name': 'message', 'type': {'builtin': 'string'}, 'optional': True}
                ]
            }
        }

        return output_types, output_type_name

    def __call__(self, environ, unused_start_response):
        ctx = environ[Context.ENVIRON_CTX]

        # Handle the action
        is_get = (environ['REQUEST_METHOD'] == 'GET')
        app_validate_output = ctx.app.validate_output
        validate_output = True
        try:
            # Read the request content
            try:
                content = None if is_get else environ['wsgi.input'].read()
            except Exception:
                raise _ActionErrorInternal(HTTPStatus.REQUEST_TIMEOUT, 'IOError', message='Error reading request content')

            # De-serialize the JSON content
            try:
                if content:
                    content_type = environ.get('CONTENT_TYPE')
                    match_charset = None if content_type is None else RE_CONTENT_TYPE_HEADER.search(content_type)
                    content_charset = 'utf-8' if match_charset is None else match_charset.group('charset')
                    content_json = content.decode(content_charset)
                    request = json_loads(content_json)
                else:
                    request = {}
            except Exception as exc:
                ctx.log.warning('Error decoding JSON content for action "%s"', self.name)
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message=f'Invalid request JSON: {exc}')

            # Validate the content
            input_types, input_type = self._input_type
            try:
                request = schema_validate(input_types, input_type, request)
            except SchemaValidationError as exc:
                ctx.log.warning('Invalid content for action "%s": %s', self.name, f'{exc}')
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message=f'{exc} (content)',
                    member=exc.member_fqn
                )

            # Decode the query string
            query_string = environ.get('QUERY_STRING', '')
            request_query = url_decode_query_string(query_string)
            if request_query is None:
                ctx.log.warning('Error decoding query string for action "%s": %.1000r', self.name, query_string)
                raise _ActionErrorInternal(HTTPStatus.BAD_REQUEST, 'InvalidInput', message='Invalid query string')

            # Validate the query string
            query_types, query_type = self._query_type
            try:
                request_query = schema_validate(query_types, query_type, request_query)
            except SchemaValidationError as exc:
                ctx.log.warning('Invalid query string for action "%s": %s', self.name, f'{exc}')
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message=f'{exc} (query string)',
                    member=exc.member_fqn
                )

            # Validate the path args
            path_types, path_type = self._path_type
            request_path = ctx.url_args if ctx.url_args is not None else {}
            try:
                request_path = schema_validate(path_types, path_type, request_path)
            except SchemaValidationError as exc:
                ctx.log.warning('Invalid path for action "%s": %s', self.name, f'{exc}')
                raise _ActionErrorInternal(
                    HTTPStatus.BAD_REQUEST,
                    'InvalidInput',
                    message=f'{exc} (path)',
                    member=exc.member_fqn
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
                output_types, output_type = self._output_type
            except ActionError as exc:
                status = exc.status or HTTPStatus.BAD_REQUEST
                response = {'error': exc.error}
                if exc.message is not None:
                    response['message'] = exc.message
                if app_validate_output:
                    if exc.error == 'UnexpectedError':
                        validate_output = False
                    else:
                        output_types, output_type = self._error_type
            except Exception:
                ctx.log.exception('Unexpected error in action "%s"', self.name)
                raise _ActionErrorInternal(HTTPStatus.INTERNAL_SERVER_ERROR, 'UnexpectedError')

            # Validate the response
            if not self.wsgi_response and validate_output and app_validate_output:
                try:
                    schema_validate(output_types, output_type, response)
                except SchemaValidationError as exc:
                    ctx.log.error('Invalid output returned from action "%s": %s', self.name, f'{exc}')
                    raise _ActionErrorInternal(HTTPStatus.INTERNAL_SERVER_ERROR, 'InvalidOutput', message=f'{exc}', member=exc.member_fqn)

        except _ActionErrorInternal as exc:
            status = exc.status
            response = {'error': exc.error}
            if exc.message is not None:
                response['message'] = exc.message
            if exc.member is not None:
                response['member'] = exc.member

        # Serialize the response as JSON
        return ctx.response_json(status, response)
