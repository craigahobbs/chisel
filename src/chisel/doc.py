# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
Chisel documentation application
"""

from collections import defaultdict

from .action import Action, ActionError
from .model import Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict, get_referenced_types
from .request import RedirectRequest, StaticRequest


def create_doc_requests(requests=None, root_path='/doc', api=True, app=True, css=True, cache=True):
    """
    Yield a series of requests for use with :meth:`~chisel.Application.add_requests` comprising the Chisel
    documentation application. By default, the documenation application is hosted at "/doc/".

    :param requests: A list of requests or None to use the application's requests
    :type requests: list(~chisel.Request)
    :param str root_path: The documentation application URL root path. The default is "/doc".
    :param bool api: If True, include the documentation APIs. Two documentation APIs are added,
        "/doc/doc_index" and "`/doc/doc_request <doc/doc.html#name=chisel_doc_request>`_".
    :param bool app: If True, include the documentation client application.
    :param bool css: If True, and "app" is True, include "/doc/doc.css" and "/doc/doc.svg". If you exclude CSS,
        you can add your own versions of these requests to customize the documentation styling.
    :param bool cache: If True, cache static request content.
    :returns: Generator of :class:`~chisel.Request`
    """

    if api:
        yield DocIndex(requests=requests, urls=(('GET', root_path + '/doc_index'),))
        yield DocRequest(requests=requests, urls=(('GET', root_path + '/doc_request'),))
    if app:
        yield RedirectRequest((('GET', root_path),), root_path + '/')
        yield StaticRequest('chisel', 'static/doc.html', urls=(('GET', root_path + '/'), ('GET', root_path + '/index.html')), cache=cache)
        if css:
            yield StaticRequest('chisel', 'static/doc.css', urls=(('GET', root_path + '/doc.css'),), cache=cache)
            yield StaticRequest('chisel', 'static/doc.svg', urls=(('GET', root_path + '/doc.svg'),), cache=cache)
        yield StaticRequest('chisel', 'static/chisel.js', urls=(('GET', root_path + '/chisel.js'),), cache=cache)
        yield StaticRequest('chisel', 'static/doc.js', urls=(('GET', root_path + '/doc.js'),), cache=cache)


class DocIndex(Action):
    """
    The documentation index API. This API provides all the information the documentation application needs to render the
    index page.

    :param requests: A list of requests or None to use the application's requests
    :type requests: dict(str, ~chisel.Request)
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    """

    __slots__ = ('requests',)

    SPEC = '''\
group "Documentation"

# A non-empty string array
typedef string[len > 0] StringArray

# Get the documentation index
action chisel_doc_index

    output

        # The documentation index title
        string title

        # The dictionary of documentation group titles to array of request names
        StringArray{} groups
'''

    def __init__(self, requests=None, urls=(('GET', '/doc_index'),)):
        super().__init__(self._doc_index, name='chisel_doc_index', urls=urls, spec=self.SPEC)
        if requests is not None:
            self.requests = {request.name: request for request in requests}
        else:
            self.requests = None

    def _doc_index(self, ctx, unused_req):
        requests = self.requests if self.requests is not None else ctx.app.requests
        groups = defaultdict(list)
        for request in requests.values():
            groups[request.doc_group or 'Uncategorized'].append(request.name)
        return {
            'title': ctx.environ['HTTP_HOST'],
            'groups': {group: sorted(names) for group, names in groups.items()}
        }


class DocRequest(Action):
    """
    The documentation request API. This API provides all the information the documentation applicaton needs to render
    the request documentation page. The documentation request API's documentation is `here
    <doc/doc.html#name=chisel_doc_request>`_.

    :param requests: A list of requests or None to use the application's requests
    :type requests: list(~chisel.Request)
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    """

    __slots__ = ('requests',)

    SPEC = '''
group "Documentation"

# Union representing a member type
union Type

    # A built-in type
    BuiltinType builtin

    # An array type
    Array array

    # A dictionary type
    Dict dict

    # An enumeration type
    string enum

    # A struct type
    string struct

    # A type definition
    string typedef

# A type attribute
struct Attribute

    # The value is equal
    optional float eq

    # The value is less than
    optional float lt

    # The value is less than or equal to
    optional float lte

    # The value is greater than
    optional float gt

    # The value is greater than or equal to
    optional float gte

    # The length is equal to
    optional int len_eq

    # The length is less-than
    optional int len_lt

    # The length is less than or equal to
    optional int len_lte

    # The length is greater than
    optional int len_gt

    # The length is greater than or equal to
    optional int len_gte

# The built-in type enumeration
enum BuiltinType

    # The string type
    string

    # The integer type
    int

    # The float type
    float

    # The boolean type
    bool

    # A date formatted as an ISO-8601 date string
    date

    # A date/time formatted as an ISO-8601 date/time string
    datetime

    # A UUID formatted as string
    uuid

    # An object of any type
    object

# An array type
struct Array

    # The contained type
    Type type

    # The contained type's attributes
    optional Attribute attr

# A dictionary type
struct Dict

    # The contained key type
    Type type

    # The contained key type's attributes
    optional Attribute attr

    # The contained value type
    Type key_type

    # The contained value type's attributes
    optional Attribute key_attr

# An enumeration type
struct Enum

    # The documentation markdown text
    optional string doc

    # The enum type name
    string name

    # The enumeration values
    EnumValue[] values

# An enumeration type value
struct EnumValue

    # The documentation markdown text
    optional string doc

    # The value string
    string value

# A struct type
struct Struct

    # The documentation markdown text
    optional string doc

    # The struct type name
    string name

    # The struct members
    Member[] members

    # If true, the struct is a union and exactly one of the optional members is present.
    optional bool union

# A struct type member
struct Member

    # The documentation markdown text
    optional string doc

    # The member name
    string name

    # The member type
    Type type

    # The member type attributes
    optional Attribute attr

    # If true, the member is optional and may not be present.
    optional bool optional

    # If true, the member may be null.
    optional bool nullable

# A typedef type
struct Typedef

    # The documentation markdown text
    optional string doc

    # The typedef type name
    string name

    # The typedef's type
    Type type

    # The typedef's type attributes
    optional Attribute attr

# A JSON web service API
struct Action

    # The action name
    string name

    # The path parameters struct
    Struct path

    # The query parameters struct
    Struct query

    # The content body struct
    Struct input

    # The response body struct
    optional Struct output

    # The custom error response codes
    Enum errors

# Struct representing a request's URL information
struct RequestURL

    # The request URL HTTP request method. If not present, all HTTP request methods are accepted.
    optional string method

    # The request URL path
    string url

# Get a request's documentation information
action chisel_doc_request

    query

        # The request name
        string name

    output

        # The documentation markdown text
        optional string doc

        # The request name
        string name

        # The array of URL paths where the request is hosted.
        RequestURL[] urls

        # The action definition. If this member is present then this request is an action.
        optional Action action

        # The array of struct types referenced by the action
        optional Struct[] structs

        # The array of enum types referenced by the action
        optional Enum[] enums

        # The array of typedef types referenced by the action
        optional Typedef[] typedefs

    errors

        # The request name is unknown
        UnknownName
'''

    def __init__(self, requests=None, urls=(('GET', '/doc_request'),)):
        super().__init__(self._doc_request, name='chisel_doc_request', urls=urls, spec=self.SPEC)
        if requests is not None:
            self.requests = {request.name: request for request in requests}
        else:
            self.requests = None

    def _doc_request(self, ctx, req):
        requests = self.requests if self.requests is not None else ctx.app.requests
        request = requests.get(req['name'])
        if request is None:
            raise ActionError('UnknownName')

        response = {
            'name': request.name,
            'urls': [self._url_dict(method, url) for method, url in request.urls],
        }
        if request.doc is not None:
            response['doc'] = request.doc

        if isinstance(request, Action):
            response['action'] = action_dict = {
                'name': request.model.name,
                'path': self._struct_dict(request.model.path_type),
                'query': self._struct_dict(request.model.query_type),
                'input': self._struct_dict(request.model.input_type),
                'errors': self._enum_dict(request.model.error_type),
            }
            if not request.wsgi_response:
                action_dict['output'] = self._struct_dict(request.model.output_type)

            response_structs = sorted(
                (self._struct_dict(typ) for typ in get_referenced_types(request.model) if isinstance(typ, TypeStruct)),
                key=lambda x: x['name']
            )
            if response_structs:
                response['structs'] = response_structs

            response_enums = sorted(
                (self._enum_dict(typ) for typ in get_referenced_types(request.model) if isinstance(typ, TypeEnum)),
                key=lambda x: x['name']
            )
            if response_enums:
                response['enums'] = response_enums

            response_typedefs = sorted(
                (self._typedef_dict(typ) for typ in get_referenced_types(request.model) if isinstance(typ, Typedef)),
                key=lambda x: x['name']
            )
            if response_typedefs:
                response['typedefs'] = response_typedefs

        return response

    @staticmethod
    def _url_dict(method, url):
        url_dict = {'url': url}
        if method is not None:
            url_dict['method'] = method
        return url_dict

    @classmethod
    def _type_dict(cls, type_):
        if isinstance(type_, TypeArray):
            return {'array': cls._array_dict(type_)}
        if isinstance(type_, TypeDict):
            return {'dict': cls._dict_dict(type_)}
        if isinstance(type_, TypeEnum):
            return {'enum': type_.type_name}
        if isinstance(type_, TypeStruct):
            return {'struct': type_.type_name}
        if isinstance(type_, Typedef):
            return {'typedef': type_.type_name}
        return {'builtin': type_.type_name}

    @classmethod
    def _array_dict(cls, array_type):
        array_dict = {
            'type': cls._type_dict(array_type.type),
        }
        if array_type.attr is not None:
            array_dict['attr'] = cls._attr_dict(array_type.attr)
        return array_dict

    @classmethod
    def _dict_dict(cls, dict_type):
        dict_dict = {
            'type': cls._type_dict(dict_type.type),
            'key_type': cls._type_dict(dict_type.key_type),
        }
        if dict_type.attr is not None:
            dict_dict['attr'] = cls._attr_dict(dict_type.attr)
        if dict_type.key_attr is not None:
            dict_dict['key_attr'] = cls._attr_dict(dict_type.key_attr)
        return dict_dict

    @classmethod
    def _attr_dict(cls, attr):
        attr_dict = {}
        if attr.op_eq is not None:
            attr_dict['eq'] = attr.op_eq
        if attr.op_lt is not None:
            attr_dict['lt'] = attr.op_lt
        if attr.op_lte is not None:
            attr_dict['lte'] = attr.op_lte
        if attr.op_gt is not None:
            attr_dict['gt'] = attr.op_gt
        if attr.op_gte is not None:
            attr_dict['gte'] = attr.op_gte
        if attr.op_len_eq is not None:
            attr_dict['len_eq'] = attr.op_len_eq
        if attr.op_len_lt is not None:
            attr_dict['len_lt'] = attr.op_len_lt
        if attr.op_len_lte is not None:
            attr_dict['len_lte'] = attr.op_len_lte
        if attr.op_len_gt is not None:
            attr_dict['len_gt'] = attr.op_len_gt
        if attr.op_len_gte is not None:
            attr_dict['len_gte'] = attr.op_len_gte
        return attr_dict

    @classmethod
    def _struct_dict(cls, struct_type):
        struct_dict = {
            'name': struct_type.type_name,
            'members': [cls._member_dict(member) for member in struct_type.members()],
        }
        if struct_type.doc is not None:
            struct_dict['doc'] = struct_type.doc
        if struct_type.union:
            struct_dict['union'] = True
        return struct_dict

    @classmethod
    def _member_dict(cls, member):
        member_dict = {
            'name': member.name,
            'type': cls._type_dict(member.type),
        }
        if member.doc is not None:
            member_dict['doc'] = member.doc
        if member.optional:
            member_dict['optional'] = member.optional
        if member.nullable:
            member_dict['nullable'] = member.nullable
        if member.attr is not None:
            member_dict['attr'] = cls._attr_dict(member.attr)
        return member_dict

    @classmethod
    def _enum_dict(cls, enum_type):
        enum_dict = {
            'name': enum_type.type_name,
            'values': [cls._enum_value_dict(enum_value) for enum_value in enum_type.values()],
        }
        if enum_type.doc is not None:
            enum_dict['doc'] = enum_type.doc
        return enum_dict

    @classmethod
    def _enum_value_dict(cls, enum_value):
        enum_value_dict = {
            'value': enum_value.value,
        }
        if enum_value.doc is not None:
            enum_value_dict['doc'] = enum_value.doc
        return enum_value_dict

    @classmethod
    def _typedef_dict(cls, typedef_type):
        typedef_dict = {
            'name': typedef_type.type_name,
            'type': cls._type_dict(typedef_type.type),
        }
        if typedef_type.doc is not None:
            typedef_dict['doc'] = typedef_type.doc
        if typedef_type.attr is not None:
            typedef_dict['attr'] = cls._attr_dict(typedef_type.attr)
        return typedef_dict
