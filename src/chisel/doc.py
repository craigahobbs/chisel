# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from collections import defaultdict

from .action import Action, ActionError
from .model import Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict, get_referenced_types
from .request import RedirectRequest, StaticRequest


def get_doc_requests(root_path='/doc', request_api=True, request_names=None, static=True, static_css=True, cache=True):
    """
    TODO

    :param str root_path: TODO
    :param bool request_api: TODO
    :param list[str] request_names: TODO
    :param bool static: TODO
    :param bool static_css: TODO
    """

    if request_api and request_names is None:
        yield DocIndex(urls=(('GET', root_path + '/doc_index'),))
    if request_api:
        yield DocRequest(urls=(('GET', root_path + '/doc_request'),), request_names=request_names)
    if static:
        yield RedirectRequest((('GET', root_path),), root_path + '/')
        yield StaticRequest('chisel', 'static/chisel.js', urls=(('GET', root_path + '/chisel.js'),), cache=cache)
        yield StaticRequest('chisel', 'static/doc.js', urls=(('GET', root_path + '/doc.js'),), cache=cache)
        yield StaticRequest('chisel', 'static/doc.html', urls=(('GET', root_path + '/'), ('GET', root_path + '/index.html')), cache=cache)
        if static_css:
            yield StaticRequest('chisel', 'static/doc.css', urls=(('GET', root_path + '/doc.css'),), cache=cache)


class DocIndex(Action):
    """
    TODO
    """

    __slots__ = ()

    def __init__(self, urls=(('GET', '/doc_index'),)):
        super().__init__(
            self._doc_index,
            name='chisel_doc_index',
            urls=urls,
            spec='''\
group "Documentation"

# TODO
typedef string[len > 0] StringArray

# TODO
action chisel_doc_index

    output

        # TODO
        StringArray{} groups
''')

    @staticmethod
    def _doc_index(ctx, unused_req):
        groups = defaultdict(list)
        for request in ctx.app.requests.values():
            groups[request.doc_group or 'Uncategorized'].append(request.name)
        return {
            'groups': {group: sorted(names) for group, names in groups.items()}
        }


class DocRequest(Action):
    """
    TODO
    """

    __slots__ = ('_request_names',)

    def __init__(self, urls=(('GET', '/doc_request'),), request_names=None):
        super().__init__(
            self._doc_request,
            name='chisel_doc_request',
            urls=urls,
            spec='''\
group "Documentation"

# TODO
typedef string[len > 0] StringArray

# TODO
typedef string(len > 0) StructName

# TODO
typedef string(len > 0) EnumName

# TODO
typedef string(len > 0) TypedefName

# TODO
union Type

    # TODO
    BuiltinType builtin

    # TODO
    Array array

    # TODO
    Dict dict

    # TODO
    EnumName enum

    # TODO
    StructName struct

    # TODO
    TypedefName typedef

# TODO
enum BuiltinType

    # TODO
    string

    # TODO
    int

    # TODO
    float

    # TODO
    bool

    # TODO
    date

    # TODO
    datetime

    # TODO
    uuid

    # TODO
    object

# TODO
struct Array

    # TODO
    Type type

    # TODO
    optional Attr attr

# TODO
struct Dict

    # TODO
    Type type

    # TODO
    optional Attr attr

    # TODO
    Type key_type

    # TODO
    optional Attr key_attr

# TODO
struct Enum

    # TODO
    optional StringArray doc

    # TODO
    EnumName name

    # TODO
    EnumValue[] values

# TODO
struct EnumValue

    # TODO
    optional StringArray doc

    # TODO
    string value

# TODO
struct Struct

    # TODO
    optional StringArray doc

    # TODO
    StructName name

    # TODO
    optional bool union

    # TODO
    Member[] members

# TODO
struct Member

    # TODO
    optional StringArray doc

    # TODO
    string name

    # TODO
    optional bool optional

    # TODO
    optional bool nullable

    # TODO
    optional Attr attr

    # TODO
    Type type

# TODO
struct Attr

    # TODO
    optional float eq

    # TODO
    optional float lt

    # TODO
    optional float lte

    # TODO
    optional float gt

    # TODO
    optional float gte

    # TODO
    optional int len_eq

    # TODO
    optional int len_lt

    # TODO
    optional int len_lte

    # TODO
    optional int len_gt

    # TODO
    optional int len_gte

# TODO
struct Typedef

    # TODO
    optional StringArray doc

    # TODO
    TypedefName name

    # TODO
    optional Attr attr

    # TODO
    Type type

# TODO
struct Action

    # TODO
    string name

    # TODO
    Struct path

    # TODO
    Struct query

    # TODO
    Struct input

    # TODO
    optional Struct output

    # TODO
    Enum errors

# TODO
struct RequestUrl

    # TODO
    optional string method

    # TODO
    string url

# TODO
action chisel_doc_request

    query

        # TODO
        string name

    output

        # TODO
        optional StringArray doc

        # TODO
        string name

        # TODO
        RequestUrl[] urls

        # TODO
        optional Action action

        # TODO
        optional Struct[] structs

        # TODO
        optional Enum[] enums

        # TODO
        optional Typedef[] typedefs

        # If True, hide documentation navigation. Only present when True.
        optional bool hide_nav

    errors

        # TODO
        UnknownName
''')
        self._request_names = request_names

    def _doc_request(self, ctx, req):
        request = ctx.app.requests.get(req['name'])
        if request is None:
            raise ActionError('UnknownName')
        if self._request_names is not None and req['name'] not in self._request_names:
            raise ActionError('UnknownName')

        response = {
            'name': request.name,
            'urls': [self._url_dict(method, url) for method, url in request.urls],
        }
        if request.doc:
            response['doc'] = [request.doc] if isinstance(request.doc, str) else request.doc
        if self._request_names is not None:
            response['hide_nav'] = True

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
        if struct_type.doc:
            struct_dict['doc'] = [struct_type.doc] if isinstance(struct_type.doc, str) else struct_type.doc
        if struct_type.union:
            struct_dict['union'] = True
        return struct_dict

    @classmethod
    def _member_dict(cls, member):
        member_dict = {
            'name': member.name,
            'type': cls._type_dict(member.type),
        }
        if member.doc:
            member_dict['doc'] = member.doc if isinstance(member.doc, str) else member.doc
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
        if enum_type.doc:
            enum_dict['doc'] = enum_type.doc if isinstance(enum_type.doc, str) else enum_type.doc
        return enum_dict

    @classmethod
    def _enum_value_dict(cls, enum_value):
        enum_value_dict = {
            'value': enum_value.value,
        }
        if enum_value.doc:
            enum_value_dict['doc'] = enum_value.doc if isinstance(enum_value.doc, str) else enum_value.doc
        return enum_value_dict

    @classmethod
    def _typedef_dict(cls, typedef_type):
        typedef_dict = {
            'name': typedef_type.type_name,
            'type': cls._type_dict(typedef_type.type),
        }
        if typedef_type.doc:
            typedef_dict['doc'] = typedef_type.doc if isinstance(typedef_type.doc, str) else typedef_type.doc
        if typedef_type.attr is not None:
            typedef_dict['attr'] = cls._attr_dict(typedef_type.attr)
        return typedef_dict
