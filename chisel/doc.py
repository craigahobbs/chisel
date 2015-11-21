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

from .action import Action, ActionError
from .compat import html_escape, iteritems, itervalues, urllib_parse_quote
from .model import JsonFloat, Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict
from .spec import SpecParser

from xml.sax.saxutils import quoteattr as saxutils_quoteattr


DOC_PARSER = SpecParser(spec='''\
union Type
    BuiltinType builtin
    Array array
    Dict dict
    string enum
    string struct
    Typedef typedef

enum BuiltinType
    string
    int
    float
    bool
    date
    datetime
    uuid

struct Array
    Type type
    optional Attr attr

struct Dict
    Type type
    optional Attr attr
    Type key_type
    optional Attr key_attr

struct Enum
    optional string[] doc
    string name
    EnumValue[] values

struct EnumValue
    optional string[] doc
    string value

struct Struct
    optional string[] doc
    string name
    optional bool union
    Member[] members

struct Member
    optional string[] doc
    string name
    optional bool optional
    optional Attr attr
    Type type

struct Attr
    optional float eq
    optional float lt
    optional float lte
    optional float gt
    optional float gte
    optional int len_eq
    optional int len_lt
    optional int len_lte
    optional int len_gt
    optional int len_gte

struct Typedef
    optional string[] doc
    string name
    optional Attr attr
    Type type

struct Action
    string name
    ActionInputOutput input
    optional ActionInputOutput output
    Enum errors

union ActionInputOutput
    Struct struct
    Dict dict

struct RequestUrl
    optional string method
    string url

action doc_index
    output
        string[] names

action doc_request
    input
        string name
    output
        optional string[] doc
        string name
        RequestUrl[] urls
        optional Action action
        optional Struct[] structs
        optional Enum[] enums
        optional Typedef[] typedefs
    errors
        UnknownName
''')


def _referenced_types(struct_types, enum_types, typedef_types, type_, top_level=True):
    if isinstance(type_, TypeStruct) and type_.type_name not in struct_types:
        if not top_level:
            struct_types[type_.type_name] = type_
        for member in type_.members:
            _referenced_types(struct_types, enum_types, typedef_types, member.type, top_level=False)
    elif isinstance(type_, TypeEnum) and type_.type_name not in enum_types:
        if not top_level:
            enum_types[type_.type_name] = type_
    elif isinstance(type_, Typedef) and type_.type_name not in typedef_types:
        if not top_level:
            typedef_types[type_.type_name] = type_
        _referenced_types(struct_types, enum_types, typedef_types, type_.type, top_level=False)
    elif isinstance(type_, TypeArray):
        _referenced_types(struct_types, enum_types, typedef_types, type_.type, top_level=False)
    elif isinstance(type_, TypeDict):
        _referenced_types(struct_types, enum_types, typedef_types, type_.type, top_level=False)
        _referenced_types(struct_types, enum_types, typedef_types, type_.key_type, top_level=False)


class DocIndex(Action):
    __slots__ = ()

    def __init__(self, name=None, urls=None):
        Action.__init__(self, self.doc_index, name=name, urls=urls, parser=DOC_PARSER)

    @staticmethod
    def doc_index(ctx, dummy_req):
        return {'names': sorted((request.name for request in itervalues(ctx.app.requests)), key=lambda x: x.lower())}


class DocRequest(Action):
    __slots__ = ()

    def __init__(self, name=None, urls=None):
        Action.__init__(self, self.doc_request, name=name, urls=urls, parser=DOC_PARSER)

    @staticmethod
    def doc_request(ctx, req):
        request = ctx.app.requests.get(req['name'])
        if request is None:
            raise ActionError('UnknownName')

        def url_dict(method, url):
            url_dict = {'url': url}
            if method is not None:
                url_dict['method'] = method
            return url_dict

        response = {
            'name': request.name,
            'urls': [url_dict(method, url) for method, url in request.urls],
        }
        if request.doc:
            response['doc'] = request.doc

        def type_dict(type_):
            if isinstance(type_, TypeArray):
                array_dict = {
                    'type': type_dict(type_.type),
                }
                if type_.attr is not None:
                    array_dict['attr'] = attr_dict(type_.attr)
                return {'array': array_dict}
            elif isinstance(type_, TypeDict):
                return {'dict': dict_dict(type_)}
            elif isinstance(type_, TypeEnum):
                return {'enum': type_.type_name}
            elif isinstance(type_, TypeStruct):
                return {'struct': type_.type_name}
            elif isinstance(type_, Typedef):
                return {'typedef': type_.type_name}
            else:
                return {'builtin': type_.type_name}

        def dict_dict(dict_type):
            dict_dict = {
                'type': type_dict(dict_type.type),
                'key_type': type_dict(dict_type.key_type),
            }
            if dict_type.attr is not None:
                dict_dict['attr'] = attr_dict(dict_type.attr)
            if dict_type.key_attr is not None:
                dict_dict['key_attr'] = attr_dict(dict_type.key_attr)
            return dict_dict

        def attr_dict(attr):
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

        if isinstance(request, Action):

            def struct_dict(struct_type):
                struct_dict = {
                    'name': struct_type.type_name,
                    'members': [member_dict(member) for member in struct_type.members],
                }
                if struct_type.doc:
                    struct_dict['doc'] = struct_type.doc
                if struct_type.union:
                    struct_dict['union'] = True
                return struct_dict

            def member_dict(member):
                member_dict = {
                    'name': member.name,
                    'type': type_dict(member.type),
                }
                if member.doc:
                    member_dict['doc'] = member.doc
                if member.optional:
                    member_dict['optional'] = member.optional
                if member.attr is not None:
                    member_dict['attr'] = attr_dict(member.attr)
                return member_dict

            def enum_dict(enum_type):
                enum_dict = {
                    'name': enum_type.type_name,
                    'values': [enum_value_dict(enum_value) for enum_value in enum_type.values],
                }
                if enum_type.doc:
                    enum_dict['doc'] = enum_type.doc
                return enum_dict

            def enum_value_dict(enum_value):
                enum_value_dict = {
                    'value': enum_value.value,
                }
                if enum_value.doc:
                    enum_value_dict['doc'] = enum_value.doc
                return enum_value_dict

            def action_input_output(input_output_type):
                if isinstance(input_output_type, TypeDict):
                    return {'dict': dict_dict(input_output_type)}
                return {'struct': struct_dict(input_output_type)}

            struct_types = {}
            enum_types = {}
            typedef_types = {}
            _referenced_types(struct_types, enum_types, typedef_types, request.model.input_type)
            _referenced_types(struct_types, enum_types, typedef_types, request.model.output_type)
            _referenced_types(struct_types, enum_types, typedef_types, request.model.error_type)

            response['action'] = action_dict = {
                'name': request.model.name,
                'input': action_input_output(request.model.input_type),
                'errors': enum_dict(request.model.error_type),
            }
            if not request.wsgi_response:
                action_dict['output'] = action_input_output(request.model.output_type)

            response['structs'] = struct_dicts = []
            for struct_type in sorted(itervalues(struct_types), key=lambda x: x.type_name.lower()):
                struct_dicts.append(struct_dict(struct_type))

            response['enums'] = enum_dicts = []
            for enum_type in sorted(itervalues(enum_types), key=lambda x: x.type_name.lower()):
                enum_dicts.append(enum_dict(enum_type))

            response['typedefs'] = typedef_dicts = []
            for typedef_type in sorted(itervalues(typedef_types), key=lambda x: x.type_name.lower()):
                typedef_dict = {
                    'name': typedef_type.type_name,
                    'type': type_dict(typedef_type.type_name),
                }
                if typedef_type.doc:
                    typedef_dict['doc'] = typedef_type.doc
                if typedef_type.attr is not None:
                    typedef_dict['attr'] = attr_dict(typedef_type.attr)
                typedef_dicts.append(typedef_dict)

        return response


class DocAction(Action):
    """
    Chisel documentation request
    """

    __slots__ = ()

    def __init__(self, name=None, urls=None):
        if name is None:
            name = 'doc'
        Action.__init__(self, self._action_callback, name=name, urls=urls, wsgi_response=True,
                        spec='''\
# Generate the application's documentation HTML page.
action {name}
  input
    # Generate documentation for the specified request name; generate the
    # documentation index if the request name is not specified.
    optional string name

    # Remove navigation links.
    optional bool nonav
'''.format(name=name))

    @staticmethod
    def _action_callback(ctx, req):
        request_name = req.get('name')
        if request_name is None:
            root = _index_html(ctx.environ, sorted(itervalues(ctx.app.requests), key=lambda x: x.name.lower()))
            content = root.serialize(indent='  ' if ctx.app.pretty_output else '')
            return ctx.response_text('200 OK', content, content_type='text/html')
        elif request_name in ctx.app.requests:
            root = _request_html(ctx.environ, ctx.app.requests[request_name], req.get('nonav'))
            content = root.serialize(indent='  ' if ctx.app.pretty_output else '')
            return ctx.response_text('200 OK', content, content_type='text/html')
        else:
            return ctx.response_text('500 Internal Server Error', 'Unknown Request')


class DocPage(Action):
    """
    Chisel single-request documentation request
    """

    __slots__ = ('request')

    def __init__(self, request, name=None, urls=None):
        request_desc = 'action' if isinstance(request, Action) else 'request'
        request_name = request.name
        if name is None:
            name = 'doc_' + request_desc + '_' + request_name
        if urls is None:
            urls = ('/doc/' + request_desc + '/' + request_name,)
        Action.__init__(self, self._action_callback, name=name, urls=urls, wsgi_response=True,
                        spec='''\
# Documentation page for {request_desc} {request_name}.
action {name}
'''.format(name=name, request_desc=request_desc, request_name=request_name))
        self.request = request

    def _action_callback(self, ctx, dummy_req):
        root = _request_html(ctx.environ, self.request, nonav=True)
        content = root.serialize(indent='  ' if ctx.app.pretty_output else '')
        return ctx.response_text('200 OK', content, content_type='text/html')


class Element(object):
    """
    HTML5 DOM element
    """

    __slots__ = ('name', 'text', 'text_raw', 'closed', 'indent', 'inline', 'attrs', 'children')

    def __init__(self, name, text=False, text_raw=False, closed=True, indent=True, inline=False, **attrs):
        self.name = name
        self.text = text
        self.text_raw = text_raw
        self.closed = closed
        self.indent = indent
        self.inline = inline
        self.attrs = attrs
        self.children = []

    def add_child(self, name, **kwargs):
        child = Element(name, **kwargs)
        self.children.append(child)
        return child

    def serialize_chunks(self, indent='  ', indent_index=0, inline=False):

        # HTML5
        if indent_index <= 0:
            yield '<!doctype html>\n'

        # Initial newline and indent as necessary...
        if indent is not None and not inline and indent_index > 0 and self.indent:
            yield '\n'
            if indent and not self.text and not self.text_raw:
                yield indent * indent_index

        # Text element?
        if self.text:
            yield html_escape(self.name)
            return
        elif self.text_raw:
            yield self.name
            return

        # Element open
        yield '<' + self.name
        for attr_key, attr_value in sorted(iteritems(self.attrs), key=lambda x: x[0].lstrip('_')):
            yield ' ' + attr_key.lstrip('_') + '=' + saxutils_quoteattr(attr_value)
        yield '>'
        if not self.closed and not self.children:
            return

        # Children elements
        for child in self.children:
            for chunk in child.serialize_chunks(indent=indent, indent_index=indent_index + 1, inline=inline or self.inline):
                yield chunk

        # Element close
        if indent is not None and not inline and not self.inline:
            yield '\n' + indent * indent_index
        yield '</' + self.name + '>'

    def serialize(self, indent='  '):
        return ''.join(self.serialize_chunks(indent=indent))


def _index_html(environ, requests):
    doc_root_url = environ['SCRIPT_NAME'] + environ['PATH_INFO']

    # Index page title
    if 'HTTP_HOST' in environ:
        title = environ['HTTP_HOST']
    else:
        title = environ['SERVER_NAME'] + (':' + environ['SERVER_PORT'] if environ['SERVER_NAME'] != 80 else '')

    # Index page header
    root = Element('html')
    head = root.add_child('head')
    head.add_child('meta', closed=False, charset='UTF-8')
    head.add_child('title', inline=True).add_child(title, text=True)
    _add_style(head)
    body = root.add_child('body', _class='chsl-index-body')
    body.add_child('h1', inline=True).add_child(title, text=True)

    # Action and request links
    ul_requests = body.add_child('ul', _class='chsl-request-list')
    for request in requests:
        li_request = ul_requests.add_child('li', inline=True)
        li_request.add_child('a', href=doc_root_url + '?name=' + urllib_parse_quote(request.name)) \
                  .add_child(request.name, text=True)

    return root


def _request_html(environ, request, nonav=False):
    doc_root_url = environ['SCRIPT_NAME'] + environ['PATH_INFO']

    # Request page header
    root = Element('html')
    head = root.add_child('head')
    head.add_child('meta', closed=False, charset='UTF-8')
    head.add_child('title', inline=True).add_child(request.name, text=True)
    _add_style(head)
    body = root.add_child('body', _class='chsl-request-body')
    if not nonav:
        header = body.add_child('div', _class='chsl-header')
        header.add_child('a', inline=True, href=doc_root_url) \
              .add_child('Back to documentation index', text=True)

    # Request title
    body.add_child('h1', inline=True) \
        .add_child(request.name, text=True)
    _add_doc_text(body, request.doc)

    # Note for request URLs
    notes = body.add_child('div', _class='chsl-notes')
    if request.urls:
        div_note = notes.add_child('div', _class='chsl-note')
        p_note = div_note.add_child('p')
        p_note.add_child('b', inline=True).add_child('Note: ', text=True)
        p_note.add_child('The request is exposed at the following ' + ('URLs' if len(request.urls) > 1 else 'URL') + ':', text=True)
        ul_urls = div_note.add_child('ul')
        for method, url in request.urls:
            ul_urls.add_child('li', inline=True) \
                   .add_child('a', href=url) \
                   .add_child(('' if method is None else method + ' ') + url, text=True)

    if isinstance(request, Action):
        # Note for custom response callback
        if request.wsgi_response:
            div_note_response = notes.add_child('div', _class='chsl-note')
            p_note_response = div_note_response.add_child('p')
            p_note_response.add_child('b', inline=True).add_child('Note: ', text=True)
            p_note_response.add_child('The action has a non-default response. See documentation for details.', text=True)

        # Find all user types referenced by the action
        struct_types = {}
        enum_types = {}
        typedef_types = {}
        _referenced_types(struct_types, enum_types, typedef_types, request.model.input_type)
        _referenced_types(struct_types, enum_types, typedef_types, request.model.output_type)

        # Request input and output structs
        _struct_section(body, request.model.input_type, 'h2', 'Input Parameters', 'The action has no input parameters.')
        if not request.wsgi_response:
            _struct_section(body, request.model.output_type, 'h2', 'Output Parameters', 'The action has no output parameters.')
            _enum_section(body, request.model.error_type, 'h2', 'Error Codes', 'The action returns no custom error codes.')

        # User types
        if typedef_types:
            body.add_child('h2', inline=True) \
                .add_child('Typedefs', text=True)
            for typedef_type in sorted(itervalues(typedef_types), key=lambda x: x.type_name.lower()):
                _typedef_section(body, typedef_type)
        if struct_types:
            body.add_child('h2', inline=True) \
                .add_child('Struct Types', text=True)
            for struct_type in sorted(itervalues(struct_types), key=lambda x: x.type_name.lower()):
                _struct_section(body, struct_type)
        if enum_types:
            body.add_child('h2', inline=True) \
                .add_child('Enum Types', text=True)
            for enum_type in sorted(itervalues(enum_types), key=lambda x: x.type_name.lower()):
                _enum_section(body, enum_type)

    return root


def _add_style(parent):
    parent.add_child('style', _type='text/css') \
        .add_child('''\
html, body, div, span, h1, h2, h3 p, a, table, tr, th, td, ul, li, p {
    margin: 0;
    padding: 0;
    border: 0;
    outline: 0;
    font-size: 1em;
    vertical-align: baseline;
}
body, td, th {
    background-color: white;
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 10pt;
    line-height: 1.2em;
    color: black;
}
body {
    margin: 1em;
}
h1, h2, h3 {
    font-weight: bold;
}
h1 {
    font-size: 1.6em;
    margin: 1em 0 1em 0;
}
h2 {
    font-size: 1.4em;
    margin: 1.4em 0 1em 0;
}
h3 {
    font-size: 1.2em;
    margin: 1.5em 0 1em 0;
}
table {
    border-collapse: collapse;
    border-spacing: 0;
    margin: 1.2em 0 0 0;
}
th, td {
    padding: 0.5em 1em 0.5em 1em;
    text-align: left;
    background-color: #ECF0F3;
    border-color: white;
    border-style: solid;
    border-width: 2px;
}
th {
    font-weight: bold;
}
p {
    margin: 0.5em 0 0 0;
}
p:first-child {
    margin: 0;
}
a {
    color: #004B91;
}
a:link {
    text-decoration: none;
}
a:visited {
    text-decoration: none;
}
a:active {
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
a.linktarget {
    color: black;
}
a.linktarget:hover {
    text-decoration: none;
}
ul.chsl-request-list {
    list-style: none;
}
ul.chsl-request-list li {
    margin: 0.75em 0.5em;
}
ul.chsl-request-list li a {
    font-size: 1.25em;
}
div.chsl-header {
    margin: .25em 0;
}
div.chsl-notes {
    margin: 1.25em 0;
}
div.chsl-note {
    margin: .75em 0;
}
div.chsl-note ul {
    list-style: none;
    margin: .4em .2em;
}
div.chsl-note li {
    margin: 0 1em;
}
ul.chsl-constraint-list {
    list-style: none;
    white-space: nowrap;
}
.chsl-emphasis {
    font-style:italic;
}''', text_raw=True)


def _user_type_href(type_):
    return type_.type_name


_USER_TYPES = (Typedef, TypeStruct, TypeEnum)


def _add_type_name_helper(parent, type_):
    if isinstance(type_, _USER_TYPES):
        parent = parent.add_child('a', inline=True, href='#' + _user_type_href(type_))
    parent.add_child(type_.type_name, text=True, inline=True)


def _add_type_name(parent, type_):
    if isinstance(type_, TypeArray):
        _add_type_name_helper(parent, type_.type)
        parent.add_child('&nbsp;[]', text_raw=True)
    elif isinstance(type_, TypeDict):
        if not type_.has_default_key_type():
            _add_type_name_helper(parent, type_.key_type)
            parent.add_child('&nbsp;:&nbsp;', text_raw=True)
        _add_type_name_helper(parent, type_.type)
        parent.add_child('&nbsp;{}', text_raw=True)
    else:
        _add_type_name_helper(parent, type_)


# Get attribute list - [(lhs, operator, rhs), ...]
def _attribute_list(attr, value_name, len_name):
    if attr is None:
        return
    if attr.op_gt is not None:
        yield (value_name, '>', str(JsonFloat(attr.op_gt, 6)))
    if attr.op_gte is not None:
        yield (value_name, '>=', str(JsonFloat(attr.op_gte, 6)))
    if attr.op_lt is not None:
        yield (value_name, '<', str(JsonFloat(attr.op_lt, 6)))
    if attr.op_lte is not None:
        yield (value_name, '<=', str(JsonFloat(attr.op_lte, 6)))
    if attr.op_eq is not None:
        yield (value_name, '==', str(JsonFloat(attr.op_eq, 6)))
    if attr.op_len_gt is not None:
        yield (len_name, '>', str(JsonFloat(attr.op_len_gt, 6)))
    if attr.op_len_gte is not None:
        yield (len_name, '>=', str(JsonFloat(attr.op_len_gte, 6)))
    if attr.op_len_lt is not None:
        yield (len_name, '<', str(JsonFloat(attr.op_len_lt, 6)))
    if attr.op_len_lte is not None:
        yield (len_name, '<=', str(JsonFloat(attr.op_len_lte, 6)))
    if attr.op_len_eq is not None:
        yield (len_name, '==', str(JsonFloat(attr.op_len_eq, 6)))


def _add_type_attr_helper(ul_type_attr, lhs, operator, rhs):
    li_type_attr = ul_type_attr.add_child('li', inline=True)
    li_type_attr.add_child('span', _class='chsl-emphasis').add_child(lhs, text=True)
    if operator is not None and rhs is not None:
        li_type_attr.add_child(' ' + operator + ' ' + repr(float(rhs)).rstrip('0').rstrip('.'), text=True)


def _add_type_attr(parent, type_, attr, optional):
    ul_type_attr = parent.add_child('ul', _class='chsl-constraint-list')
    if optional:
        _add_type_attr_helper(ul_type_attr, 'optional', None, None)
    type_name = 'array' if isinstance(type_, TypeArray) else ('dict' if isinstance(type_, TypeDict) else 'value')
    for lhs, operator, rhs in _attribute_list(attr, type_name, 'len(' + type_name + ')'):
        _add_type_attr_helper(ul_type_attr, lhs, operator, rhs)
    if hasattr(type_, 'key_type'):
        for lhs, operator, rhs in _attribute_list(type_.key_attr, 'key', 'len(key)'):
            _add_type_attr_helper(ul_type_attr, lhs, operator, rhs)
    if hasattr(type_, 'type'):
        for lhs, operator, rhs in _attribute_list(type_.attr, 'elem', 'len(elem)'):
            _add_type_attr_helper(ul_type_attr, lhs, operator, rhs)

    # No constraints?
    if not ul_type_attr.children:
        _add_type_attr_helper(ul_type_attr, 'none', None, None)


def _add_text(parent, texts):
    div = None
    for text in texts:
        if div is None:
            div = parent.add_child('div', _class='chsl-text')
        div.add_child('p') \
           .add_child(text, text=True)


def _add_doc_text(parent, doc):

    # Group paragraphs
    paragraphs = []
    lines = []
    for line in doc if isinstance(doc, (list, tuple)) else (line.strip() for line in doc.splitlines()):
        if line:
            lines.append(line)
        else:
            if lines:
                paragraphs.append(lines)
                lines = []
    if lines:
        paragraphs.append(lines)

    # Add the text DOM elements
    _add_text(parent, ('\n'.join(lines) for lines in paragraphs))


def _typedef_section(parent, type_):

    # Section title
    parent.add_child('h3', inline=True, _id=_user_type_href(type_)) \
        .add_child('a', _class='linktarget') \
        .add_child('typedef ' + type_.type_name, text=True)
    _add_doc_text(parent, type_.doc)

    # Table header
    table = parent.add_child('table')
    tr_header = table.add_child('tr')
    tr_header.add_child('th', inline=True).add_child('Type', text=True)
    tr_header.add_child('th', inline=True).add_child('Attributes', text=True)

    # Typedef type/attr rows
    tr_type = table.add_child('tr')
    _add_type_name(tr_type.add_child('td', inline=True), type_.type)
    _add_type_attr(tr_type.add_child('td'), type_.type, type_.attr, False)


def _struct_section(parent, type_, title_tag=None, title=None, empty_message=None):
    if title_tag is None:
        title_tag = 'h3'
    if title is None:
        title = ('union ' if type_.union else 'struct ') + type_.type_name
    if empty_message is None:
        empty_message = 'The struct is empty.'

    # Section title
    parent.add_child(title_tag, inline=True, _id=_user_type_href(type_)) \
        .add_child('a', _class='linktarget') \
        .add_child(title, text=True)
    _add_doc_text(parent, type_.doc)

    # Empty struct?
    if not type_.members:
        _add_text(parent, (empty_message,))
    else:
        # Has description header?
        has_description = any(member.doc for member in type_.members)

        # Table header
        table = parent.add_child('table')
        tr_header = table.add_child('tr')
        tr_header.add_child('th', inline=True).add_child('Name', text=True)
        tr_header.add_child('th', inline=True).add_child('Type', text=True)
        tr_header.add_child('th', inline=True).add_child('Attributes', text=True)
        if has_description:
            tr_header.add_child('th', inline=True).add_child('Description', text=True)

        # Struct member rows
        for member in type_.members:
            tr_member = table.add_child('tr')
            tr_member.add_child('td', inline=True).add_child(member.name, text=True)
            _add_type_name(tr_member.add_child('td', inline=True), member.type)
            _add_type_attr(tr_member.add_child('td'), member.type, member.attr, member.optional)
            if has_description:
                _add_doc_text(tr_member.add_child('td'), member.doc)


def _enum_section(parent, type_, title_tag=None, title=None, empty_message=None):
    if title_tag is None:
        title_tag = 'h3'
    if title is None:
        title = 'enum ' + type_.type_name
    if empty_message is None:
        empty_message = 'The enum is empty.'

    # Section title
    parent.add_child(title_tag, inline=True, _id=_user_type_href(type_)) \
        .add_child('a', _class='linktarget') \
        .add_child(title, text=True)
    _add_doc_text(parent, type_.doc)

    # Empty enum?
    if not type_.values:
        _add_text(parent, (empty_message,))
    else:
        # Has description header?
        has_description = any(value.doc for value in type_.values)

        # Table header
        table = parent.add_child('table')
        tr_header = table.add_child('tr')
        tr_header.add_child('th', inline=True).add_child('Value', text=True)
        if has_description:
            tr_header.add_child('th', inline=True).add_child('Description', text=True)

        # Enum value rows
        for value in type_.values:
            tr_value = table.add_child('tr')
            tr_value.add_child('td', inline=True).add_child(value.value, text=True)
            if has_description:
                _add_doc_text(tr_value.add_child('td'), value.doc)
