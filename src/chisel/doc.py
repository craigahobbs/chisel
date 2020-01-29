# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from html import escape
from http import HTTPStatus
from itertools import chain
import re
from xml.sax.saxutils import quoteattr

from .action import Action
from .model import get_referenced_types, Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict
from .request import Request


class SimpleMarkdown:
    """
    TODO
    """

    __slots__ = ()

    _RE_MARKDOWN_NEW_PARAGRAPH = re.compile(r'^\s*([#=\+\-\*]|[0-9]\.)')

    def __call__(self, markdown_text):
        """
        TODO
        """

        paragraphs = []
        lines = []
        for line in (line.strip() for line in markdown_text.splitlines()):
            if line:
                if self._RE_MARKDOWN_NEW_PARAGRAPH.match(line):
                    if lines:
                        paragraphs.append(lines)
                    lines = [line]
                else:
                    lines.append(line)
            elif lines:
                paragraphs.append(lines)
                lines = []
        if lines:
            paragraphs.append(lines)

        # Do a simple markdown-like rendering
        if not paragraphs:
            return ''
        return '\n'.join('<p>\n' + escape('\n'.join(paragraph)) + '\n</p>' for paragraph in paragraphs)


# Create the markdown object
try:
    import mistune
    MARKDOWN = mistune.create_markdown(plugins=['strikethrough', 'table', 'url'])
except ImportError: # pragma: no cover
    MARKDOWN = SimpleMarkdown()


class Element:
    """
    TODO
    """

    __slots__ = ('name', 'text', 'text_raw', 'closed', 'indent', 'inline', 'attrs', 'children')

    def __init__(self, name, text=False, text_raw=False, closed=True, indent=True, inline=False, children=None, **attrs):
        """
        TODO
        """

        #: TODO
        self.name = name

        #: TODO
        self.text = text

        #: TODO
        self.text_raw = text_raw

        #: TODO
        self.closed = closed

        #: TODO
        self.indent = indent

        #: TODO
        self.inline = inline

        #: TODO
        self.attrs = attrs

        #: TODO
        self.children = children

    def serialize(self, indent='  ', html=True):
        """
        TODO
        """

        return ''.join(chain(['<!doctype html>\n'] if html else [], self.serialize_chunks(indent=indent)))

    def serialize_chunks(self, indent='  ', indent_index=0, inline=False):
        """
        TODO
        """

        # Initial newline and indent as necessary...
        if indent is not None and not inline and indent_index > 0 and self.indent:
            yield '\n'
            if indent and not self.text and not self.text_raw:
                yield indent * indent_index

        # Text element?
        if self.text:
            yield escape(self.name)
            return
        if self.text_raw:
            yield self.name
            return

        # Element open
        yield '<' + self.name
        for attr_key, attr_value in sorted((key_value[0].lstrip('_'), key_value[1]) for key_value in self.attrs.items()):
            if attr_value is not None:
                yield ' ' + attr_key + '=' + quoteattr(attr_value)

        # Child elements
        has_children = False
        for child in self._iterate_children_helper(self.children):
            if not has_children:
                has_children = True
                yield '>'
            yield from child.serialize_chunks(indent=indent, indent_index=indent_index + 1, inline=inline or self.inline)

        # Element close
        if not has_children:
            yield ' />' if self.closed else '>'
            return
        if indent is not None and not inline and not self.inline:
            yield '\n' + indent * indent_index
        yield '</' + self.name + '>'

    @classmethod
    def _iterate_children_helper(cls, children):
        if isinstance(children, Element):
            yield children
        elif children is not None:
            for child in children:
                if isinstance(child, Element):
                    yield child
                elif child is not None:
                    yield from cls._iterate_children_helper(child)


class DocAction(Action):
    """
    TODO
    """

    __slots__ = ()

    def __init__(self, name='doc', urls=(('GET', None),), doc=None, doc_group=None):
        """
        TODO
        """

        super().__init__(self._action_callback, name=name, urls=urls, doc=doc, doc_group=doc_group,
                         wsgi_response=True, spec='''\
# Generate the application's documentation HTML page.
action {name}
  query
    # The request name. If the name is not specified the documentation index is generated.
    optional string name

    # Remove navigation links.
    optional bool nonav
'''.format(name=name))

    @staticmethod
    def _action_callback(ctx, req):
        request_name = req.get('name')
        if request_name is None:
            root = _index_html(ctx, sorted(ctx.app.requests.values(), key=lambda x: x.name.lower()))
            content = root.serialize(indent='  ' if ctx.app.pretty_output else '')
            return ctx.response_text(HTTPStatus.OK, content, content_type='text/html')
        if request_name in ctx.app.requests:
            content = DocPage.content(ctx, ctx.app.requests[request_name], nonav=req.get('nonav'))
            return ctx.response_text(HTTPStatus.OK, content, content_type='text/html')
        return ctx.response_text(HTTPStatus.NOT_FOUND, 'Unknown Request')


class DocPage(Action):
    """
    TODO
    """

    __slots__ = ('request', 'request_urls')

    def __init__(self, request, request_urls=None, name=None, urls=(('GET', None),), doc=None, doc_group=None):
        """
        TODO
        """

        request_name = request.name if isinstance(request, Request) else request.type_name
        if name is None:
            name = 'doc_' + request_name
        super().__init__(self._action_callback, name=name, urls=urls, doc=doc, doc_group=doc_group,
                         wsgi_response=True, spec='''\
# Documentation page for {request_name}.
action {name}
'''.format(name=name, request_name=request_name))

        #: TODO
        self.request = request

        #: TODO
        self.request_urls = request_urls

    def _action_callback(self, ctx, unused_req):
        return ctx.response_text(HTTPStatus.OK, self.content(ctx, self.request, self.request_urls), content_type='text/html')

    @staticmethod
    def content(ctx, request, request_urls=None, nonav=True):
        """
        TODO
        """

        root = _request_html(ctx, request, request_urls, nonav)
        return root.serialize(indent='  ' if ctx.app.pretty_output else '')


def _index_html(ctx, requests):
    title = ctx.environ.get('HTTP_HOST') or (ctx.environ['SERVER_NAME'] + ':' + ctx.environ['SERVER_PORT'])

    # Group requests
    has_groups = False
    group_requests = {}
    for request in requests:
        has_groups = has_groups or request.doc_group is not None
        group_name = request.doc_group or 'Uncategorized'
        if group_name not in group_requests:
            group_requests[group_name] = []
        group_requests[group_name].append(request)

    return Element('html', children=[
        Element('head', children=[
            Element('meta', closed=False, charset='UTF-8'),
            Element('title', inline=True, children=Element(title, text=True)),
            Element('style', _type='text/css', children=Element(STYLE_TEXT, text_raw=True))
        ]),
        Element('body', _class='chsl-index-body', children=[
            Element('h1', inline=True, children=Element(title, text=True)),
            [
                [
                    None if not has_groups else Element('h2', inline=True, children=Element(
                        'Uncategorized' if group_name is None else group_name, text=True)),
                    Element('ul', _class='chsl-request-list', children=[
                        Element('li', inline=True, children=
                                Element('a', href=ctx.reconstruct_url(query_string={'name': request.name}, relative=True), children=
                                        Element(request.name, text=True)))
                        for request in group_requests[group_name]
                    ])
                ]
                for group_name in sorted(group_requests.keys())
            ]
        ])
    ])


def _request_html(ctx, request, request_urls, nonav):
    is_request = isinstance(request, Request)
    is_action = isinstance(request, Action)
    if is_request and request_urls is None:
        request_urls = request.urls
        reconstruct_urls = True
    else:
        reconstruct_urls = False

    # Find all user types referenced by the action
    if is_action:
        struct_types = [typ for typ in get_referenced_types(request.model) if isinstance(typ, TypeStruct)]
        enum_types = [typ for typ in get_referenced_types(request.model) if isinstance(typ, TypeEnum)]
        typedef_types = [typ for typ in get_referenced_types(request.model) if isinstance(typ, Typedef)]
    elif not is_request:
        struct_types = [typ for typ in get_referenced_types(request) if isinstance(typ, TypeStruct)]
        enum_types = [typ for typ in get_referenced_types(request) if isinstance(typ, TypeEnum)]
        typedef_types = [typ for typ in get_referenced_types(request) if isinstance(typ, Typedef)]
    else:
        struct_types = enum_types = typedef_types = None

    return Element('html', children=[
        Element('head', children=[
            Element('meta', closed=False, charset='UTF-8'),
            Element('title', inline=True, children=Element(request.name if is_request else request.type_name, text=True)),
            Element('style', _type='text/css', children=Element(STYLE_TEXT, text_raw=True))
        ]),
        Element('body', _class='chsl-request-body', children=[

            # Request page header
            None if nonav else Element('div', _class='chsl-header', children=[
                Element('a', inline=True, href=ctx.reconstruct_url(query_string='', relative=True), children=
                        Element('Back to documentation index', text=True))
            ]),
            [
                Element('h1', inline=True, children=Element(request.name, text=True)),
                _doc_text(request.doc)
            ] if is_request else [
                _typedef_section(request, 'h1') if isinstance(request, Typedef) else None,
                _struct_section(request, 'h1') if isinstance(request, TypeStruct) else None,
                _enum_section(request, 'h1') if isinstance(request, TypeEnum) else None
            ],

            # Notes
            Element('div', _class='chsl-notes', children=[

                # Request URLs
                None if not is_request or not request_urls else Element('div', _class='chsl-note', children=[
                    Element('p', children=[
                        Element('b', inline=True, children=Element('Note: ', text=True)),
                        Element('The request is exposed at the following ' + ('URLs' if len(request_urls) > 1 else 'URL') + ':', text=True)
                    ]),
                    Element('ul', children=[
                        Element('li', inline=True, children=
                                Element(
                                    'a',
                                    href=ctx.reconstruct_url(path_info=url, query_string='', relative=True) if reconstruct_urls else url,
                                    children=Element(url if method is None else method + ' ' + url, text=True)
                                ))
                        for method, url in request_urls
                    ])
                ]),

                # Non-default response
                None if not (is_action and request.wsgi_response) else [
                    Element('div', _class='chsl-note', children=Element('p', children=[
                        Element('b', inline=True, children=Element('Note: ', text=True)),
                        Element('The action has a non-default response. See documentation for details.', text=True)
                    ]))
                ]
            ]),

            # Request input and output structs
            None if not is_action else [
                _struct_section(request.model.path_type, 'h2', 'Path Parameters', ('The action has no path parameters.',)),
                _struct_section(request.model.query_type, 'h2', 'Query Parameters', ('The action has no query parameters.',)),
                _struct_section(request.model.input_type, 'h2', 'Input Parameters', ('The action has no input parameters.',)),
                None if request.wsgi_response else [
                    _struct_section(request.model.output_type, 'h2', 'Output Parameters', ('The action has no output parameters.',)),
                    _enum_section(request.model.error_type, 'h2', 'Error Codes', ('The action returns no custom error codes.',))
                ]
            ],

            # User types
            None if not typedef_types else [
                Element('h2', inline=True, children=Element('Typedefs', text=True)),
                [_typedef_section(type_, 'h3') for type_ in typedef_types]
            ],
            None if not struct_types else [
                Element('h2', inline=True, children=Element('Struct Types', text=True)),
                [_struct_section(type_, 'h3') for type_ in struct_types]
            ],
            None if not enum_types else [
                Element('h2', inline=True, children=Element('Enum Types', text=True)),
                [_enum_section(type_, 'h3') for type_ in enum_types]
            ]
        ])
    ])


def _doc_text(doc):
    if not isinstance(doc, str):
        doc = '\n'.join(doc)
    markdown_html = MARKDOWN(doc).strip()
    if not markdown_html:
        return None
    return Element('div', _class='chsl-text', children=Element(markdown_html, text_raw=True))


def _type_name(type_):
    text_elem = Element(type_.type_name, text=True, inline=True)
    return text_elem if not isinstance(type_, (Typedef, TypeStruct, TypeEnum)) else \
        Element('a', inline=True, href='#' + type_.type_name, children=text_elem)


def _type_decl(type_):
    if isinstance(type_, TypeArray):
        return [_type_name(type_.type), Element('&nbsp;[]', text_raw=True)]
    if isinstance(type_, TypeDict):
        return [
            None if type_.has_default_key_type() else [_type_name(type_.key_type), Element('&nbsp;:&nbsp;', text_raw=True)],
            _type_name(type_.type), Element('&nbsp;{}', text_raw=True)
        ]
    return _type_name(type_)


def _type_attr_helper(attr, value_name, len_name):
    if attr is None:
        return
    if attr.op_gt is not None:
        yield (value_name, '>', '{0:.6f}'.format(attr.op_gt).rstrip('0').rstrip('.'))
    if attr.op_gte is not None:
        yield (value_name, '>=', '{0:.6f}'.format(attr.op_gte).rstrip('0').rstrip('.'))
    if attr.op_lt is not None:
        yield (value_name, '<', '{0:.6f}'.format(attr.op_lt).rstrip('0').rstrip('.'))
    if attr.op_lte is not None:
        yield (value_name, '<=', '{0:.6f}'.format(attr.op_lte).rstrip('0').rstrip('.'))
    if attr.op_eq is not None:
        yield (value_name, '==', '{0:.6f}'.format(attr.op_eq).rstrip('0').rstrip('.'))
    if attr.op_len_gt is not None:
        yield (len_name, '>', '{0:.6f}'.format(attr.op_len_gt).rstrip('0').rstrip('.'))
    if attr.op_len_gte is not None:
        yield (len_name, '>=', '{0:.6f}'.format(attr.op_len_gte).rstrip('0').rstrip('.'))
    if attr.op_len_lt is not None:
        yield (len_name, '<', '{0:.6f}'.format(attr.op_len_lt).rstrip('0').rstrip('.'))
    if attr.op_len_lte is not None:
        yield (len_name, '<=', '{0:.6f}'.format(attr.op_len_lte).rstrip('0').rstrip('.'))
    if attr.op_len_eq is not None:
        yield (len_name, '==', '{0:.6f}'.format(attr.op_len_eq).rstrip('0').rstrip('.'))


def _type_attr(type_, attr, optional, nullable):
    type_name = 'array' if isinstance(type_, TypeArray) else ('dict' if isinstance(type_, TypeDict) else 'value')
    type_attrs = []
    if optional:
        type_attrs.append(('optional', None, None))
    if nullable:
        type_attrs.append(('nullable', None, None))
    type_attrs.extend(_type_attr_helper(attr, type_name, 'len(' + type_name + ')'))
    if isinstance(type_, TypeDict):
        type_attrs.extend(_type_attr_helper(type_.key_attr, 'key', 'len(key)'))
    if isinstance(type_, (TypeArray, TypeDict)):
        type_attrs.extend(_type_attr_helper(type_.attr, 'elem', 'len(elem)'))

    return None if not type_attrs else Element('ul', _class='chsl-constraint-list', children=[
        Element('li', inline=True, children=[
            Element('span', _class='chsl-emphasis', children=Element(lhs, text=True)),
            None if operator is None else Element(' ' + operator + ' ' + repr(float(rhs)).rstrip('0').rstrip('.'), text=True)
        ]) for lhs, operator, rhs in type_attrs
    ])


def _typedef_section(type_, title_tag):
    attrs_element = _type_attr(type_.type, type_.attr, False, False)
    no_attrs = not attrs_element
    return [
        Element(title_tag, inline=True, _id=type_.type_name,
                children=Element('a', _class='linktarget', children=Element('typedef ' + type_.type_name, text=True))),
        _doc_text(type_.doc),
        Element('table', children=[
            Element('tr', children=[
                Element('th', inline=True, children=Element('Type', text=True)),
                None if no_attrs else Element('th', inline=True, children=Element('Attributes', text=True))
            ]),
            Element('tr', children=[
                Element('td', inline=True, children=_type_decl(type_.type)),
                None if no_attrs else Element('td', children=attrs_element)
            ])
        ])
    ]


def _struct_section(type_, title_tag, title=None, empty_doc=None):
    if not title:
        title = ('union ' if type_.union else 'struct ') + type_.type_name
    if not empty_doc:
        empty_doc = ('The struct is empty.',)
    attrs_elements = {member.name: _type_attr(member.type, member.attr, member.optional, member.nullable) for member in type_.members()}
    no_attrs = not any(attrs_elements.values())
    no_description = not any(member.doc for member in type_.members())
    return [
        Element(title_tag, inline=True, _id=type_.type_name,
                children=Element('a', _class='linktarget', children=Element(title, text=True))),
        _doc_text(type_.doc),
        _doc_text(empty_doc) if not any(type_.members()) else Element('table', children=[
            Element('tr', children=[
                Element('th', inline=True, children=Element('Name', text=True)),
                Element('th', inline=True, children=Element('Type', text=True)),
                None if no_attrs else Element('th', inline=True, children=Element('Attributes', text=True)),
                None if no_description else Element('th', inline=True, children=Element('Description', text=True))
            ]),
            [
                Element('tr', children=[
                    Element('td', inline=True, children=Element(member.name, text=True)),
                    Element('td', inline=True, children=_type_decl(member.type)),
                    None if no_attrs else Element('td', children=attrs_elements[member.name]),
                    None if no_description else Element('td', children=_doc_text(member.doc))
                ]) for member in type_.members()
            ]
        ])
    ]


def _enum_section(type_, title_tag, title=None, empty_doc=None):
    if not title:
        title = 'enum ' + type_.type_name
    if not empty_doc:
        empty_doc = ('The enum is empty.',)
    no_description = not any(value.doc for value in type_.values())
    return [
        Element(title_tag, inline=True, _id=type_.type_name,
                children=Element('a', _class='linktarget', children=Element(title, text=True))),
        _doc_text(type_.doc),
        _doc_text(empty_doc) if not any(type_.values()) else Element('table', children=[
            Element('tr', children=[
                Element('th', inline=True, children=Element('Value', text=True)),
                None if no_description else Element('th', inline=True, children=Element('Description', text=True))
            ]),
            [
                Element('tr', children=[
                    Element('td', inline=True, children=Element(value.value, text=True)),
                    None if no_description else Element('td', children=_doc_text(value.doc))
                ]) for value in type_.values()
            ]
        ])
    ]


STYLE_TEXT = '''\
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
}'''
