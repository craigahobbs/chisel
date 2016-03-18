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

from xml.sax.saxutils import quoteattr as saxutils_quoteattr

from .action import Action
from .compat import html_escape, iteritems, itervalues, urllib_parse_quote
from .model import JsonFloat, Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict


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
    # The request name. If the name is not specified the documentation index is generated.
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

    def __init__(self, name, text=False, text_raw=False, closed=True, indent=True, inline=False, children=None, **attrs):
        self.name = name
        self.text = text
        self.text_raw = text_raw
        self.closed = closed
        self.indent = indent
        self.inline = inline
        self.attrs = attrs
        self.children = children or []

    def serialize(self, indent='  '):
        return ''.join(self.serialize_chunks(indent=indent))

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
            yield html_escape(self.name) # pylint: disable=deprecated-method
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

        # Child elements
        for child in self.iterate_children():
            for chunk in child.serialize_chunks(indent=indent, indent_index=indent_index + 1, inline=inline or self.inline):
                yield chunk

        # Element close
        if indent is not None and not inline and not self.inline:
            yield '\n' + indent * indent_index
        yield '</' + self.name + '>'

    def iterate_children(self):
        for child in self._iterate_children_helper(self.children):
            yield child

    @classmethod
    def _iterate_children_helper(cls, children):
        if isinstance(children, Element):
            yield children
        elif children is not None:
            for child in children:
                for subchild in cls._iterate_children_helper(child):
                    yield subchild


def _index_html(environ, requests):
    doc_root_url = environ['SCRIPT_NAME'] + environ['PATH_INFO']

    # Index page title
    if 'HTTP_HOST' in environ:
        title = environ['HTTP_HOST']
    else:
        title = environ['SERVER_NAME'] + (':' + environ['SERVER_PORT'] if environ['SERVER_NAME'] != 80 else '')

    return Element('html', children=[
        Element('head', children=[
            Element('meta', closed=False, charset='UTF-8'),
            Element('title', inline=True, children=Element(title, text=True)),
            _style_element()
        ]),
        Element('body', _class='chsl-index-body', children=[
            Element('h1', inline=True, children=Element(title, text=True)),
            Element('ul', _class='chsl-request-list', children=[
                Element('li', inline=True, children=[
                    Element('a', href=doc_root_url + '?name=' + urllib_parse_quote(request.name), children=Element(request.name, text=True))
                ]) for request in requests
            ])
        ])
    ])


def _request_html(environ, request, nonav=False):
    doc_root_url = environ['SCRIPT_NAME'] + environ['PATH_INFO']

    # Find all user types referenced by the action
    struct_types = {}
    enum_types = {}
    typedef_types = {}
    if isinstance(request, Action):
        _referenced_types(struct_types, enum_types, typedef_types, request.model.input_type)
        _referenced_types(struct_types, enum_types, typedef_types, request.model.output_type)

    return Element('html', children=[
        Element('head', children=[
            Element('meta', closed=False, charset='UTF-8'),
            Element('title', inline=True, children=Element(request.name, text=True)),
            _style_element()
        ]),
        Element('body', _class='chsl-request-body', children=[

            # Request page header
            None if nonav else Element('div', _class='chsl-header', children=[
                Element('a', inline=True, href=doc_root_url, children=Element('Back to documentation index', text=True))
            ]),
            Element('h1', inline=True, children=Element(request.name, text=True)),
            _doc_text(request.doc),

            # Notes
            Element('div', _class='chsl-notes', children=[

                # Request URLs
                Element('div', _class='chsl-note', children=[
                    Element('p', children=[
                        Element('b', inline=True, children=Element('Note: ', text=True)),
                        Element('The request is exposed at the following ' + ('URLs' if len(request.urls) > 1 else 'URL') + ':', text=True)
                    ]),
                    Element('ul', children=[
                        Element('li', inline=True, children=
                                Element('a', href=url, children=Element(url if method is None else method + ' ' + url, text=True)))
                        for method, url in request.urls
                    ])
                ]),

                # Non-default response
                None if not request.wsgi_response else Element('div', _class='chsl-note', children=Element('p', children=[
                    Element('b', inline=True, children=Element('Note: ', text=True)),
                    Element('The action has a non-default response. See documentation for details.', text=True)
                ]))
            ]),

            # Request input and output structs
            _struct_section(request.model.input_type, 'h2', 'Input Parameters', 'The action has no input parameters.'),
            None if request.wsgi_response else [
                _struct_section(request.model.output_type, 'h2', 'Output Parameters', 'The action has no output parameters.'),
                _enum_section(request.model.error_type, 'h2', 'Error Codes', 'The action returns no custom error codes.')
            ],

            # User types
            None if not typedef_types else [
                Element('h2', inline=True, children=Element('Typedefs', text=True)),
                [_typedef_section(typedef_type)
                 for typedef_type in sorted(itervalues(typedef_types), key=lambda x: x.type_name.lower())]
            ],
            None if not struct_types else [
                Element('h2', inline=True, children=Element('Struct Types', text=True)),
                [_struct_section(struct_type)
                 for struct_type in sorted(itervalues(struct_types), key=lambda x: x.type_name.lower())]
            ],
            None if not enum_types else [
                Element('h2', inline=True, children=Element('Enum Types', text=True)),
                [_enum_section(enum_type)
                 for enum_type in sorted(itervalues(enum_types), key=lambda x: x.type_name.lower())]
            ]
        ])
    ])


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


def _style_element():
    return Element('style', _type='text/css', children=[
        Element('''\
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
    ])


def _type_name(type_):
    text_elem = Element(type_.type_name, text=True, inline=True)
    return text_elem if not isinstance(type_, (Typedef, TypeStruct, TypeEnum)) else \
        Element('a', inline=True, href='#' + type_.type_name, children=text_elem)


def _type_decl(type_):
    if isinstance(type_, TypeArray):
        return [_type_name(type_.type), Element('&nbsp;[]', text_raw=True)]
    elif isinstance(type_, TypeDict):
        return [
            None if type_.has_default_key_type() else [_type_name(type_.key_type), Element('&nbsp;:&nbsp;', text_raw=True)],
            _type_name(type_.type), Element('&nbsp;{}', text_raw=True)
        ]
    else:
        return _type_name(type_)


def _type_attributes(attr, value_name, len_name):
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


def _type_attr_helper(lhs, operator, rhs):
    return Element('li', inline=True, children=[
        Element('span', _class='chsl-emphasis', children=Element(lhs, text=True)),
        None if operator is None else Element(' ' + operator + ' ' + repr(float(rhs)).rstrip('0').rstrip('.'), text=True)
    ])


def _type_attr(type_, attr, optional):
    type_name = 'array' if isinstance(type_, TypeArray) else ('dict' if isinstance(type_, TypeDict) else 'value')
    type_attrs = []
    if optional:
        type_attrs.append(('optional', None, None))
    type_attrs.extend(_type_attributes(attr, type_name, 'len(' + type_name + ')'))
    if hasattr(type_, 'key_type'):
        type_attrs.extend(_type_attributes(type_.key_attr, 'key', 'len(key)'))
    if hasattr(type_, 'type'):
        type_attrs.extend(_type_attributes(type_.attr, 'elem', 'len(elem)'))
    if not type_attrs:
        type_attrs.append(('none', None, None))

    return Element('ul', _class='chsl-constraint-list', children=[
        _type_attr_helper(lhs, operator, rhs) for lhs, operator, rhs in type_attrs
    ])


def _doc_text(doc):
    paragraphs = []
    lines = []
    for line in doc if isinstance(doc, (list, tuple)) else (line.strip() for line in doc.splitlines()):
        if line:
            lines.append(line)
        else:
            if lines:
                paragraphs.append('\n'.join(lines))
                lines = []
    if lines:
        paragraphs.append('\n'.join(lines))

    return None if not paragraphs else Element('div', _class='chsl-text', children=[
        Element('p', children=Element(paragraph, text=True)) for paragraph in paragraphs
    ])


def _typedef_section(type_):
    return [
        Element('h3', inline=True, _id=type_.type_name,
                children=Element('a', _class='linktarget', children=Element('typedef ' + type_.type_name, text=True))),
        _doc_text(type_.doc),
        Element('table', children=[
            Element('tr', children=[
                Element('th', inline=True, children=Element('Type', text=True)),
                Element('th', inline=True, children=Element('Attributes', text=True))
            ]),
            Element('tr', children=[
                Element('td', inline=True, children=_type_decl(type_.type)),
                Element('td', children=_type_attr(type_.type, type_.attr, False))
            ])
        ])
    ]


def _struct_section(type_, title_tag=None, title=None, empty_message=None):
    if title_tag is None:
        title_tag = 'h3'
    if title is None:
        title = ('union ' if type_.union else 'struct ') + type_.type_name
    if empty_message is None:
        empty_message = 'The struct is empty.'
    no_description = not any(member.doc for member in type_.members)

    return [
        Element(title_tag, inline=True, _id=type_.type_name,
                children=Element('a', _class='linktarget', children=Element(title, text=True))),
        _doc_text(type_.doc),
        _doc_text(empty_message) if not type_.members else [
            Element('table', children=[
                Element('tr', children=[
                    Element('th', inline=True, children=Element('Name', text=True)),
                    Element('th', inline=True, children=Element('Type', text=True)),
                    Element('th', inline=True, children=Element('Attributes', text=True)),
                    None if no_description else Element('th', inline=True, children=Element('Description', text=True))
                ]),
                [
                    Element('tr', children=[
                        Element('td', inline=True, children=Element(member.name, text=True)),
                        Element('td', inline=True, children=_type_decl(member.type)),
                        Element('td', children=_type_attr(member.type, member.attr, member.optional)),
                        None if no_description else Element('td', children=_doc_text(member.doc))
                    ]) for member in type_.members
                ]
            ])
        ]
    ]


def _enum_section(type_, title_tag=None, title=None, empty_message=None):
    if title_tag is None:
        title_tag = 'h3'
    if title is None:
        title = 'enum ' + type_.type_name
    if empty_message is None:
        empty_message = 'The enum is empty.'
    no_description = not any(value.doc for value in type_.values)

    return [
        Element(title_tag, inline=True, _id=type_.type_name,
                children=Element('a', _class='linktarget', children=Element(title, text=True))),
        _doc_text(type_.doc),
        _doc_text(empty_message) if not type_.values else [
            Element('table', children=[
                Element('tr', children=[
                    Element('th', inline=True, children=Element('Value', text=True)),
                    None if no_description else Element('th', inline=True, children=Element('Description', text=True))
                ]),
                [
                    Element('tr', children=[
                        Element('td', inline=True, children=Element(value.value, text=True)),
                        None if no_description else Element('td', children=_doc_text(value.doc))
                    ]) for value in type_.values
                ]
            ])
        ]
    ]
