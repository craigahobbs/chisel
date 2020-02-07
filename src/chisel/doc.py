# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from http import HTTPStatus
import re

from .action import Action
from .model import get_referenced_types, Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict
from .request import Request
from .util import Element


class DocAction(Action):
    """
    TODO
    """

    __slots__ = ('_markdown', '_styles')

    def __init__(self, name='doc', urls=(('GET', None),), doc=None, doc_group=None, markdown=None, styles=None):
        super().__init__(self._action_callback, name=name, urls=urls, doc=doc, doc_group=doc_group, wsgi_response=True, spec=f'''\
# Generate the application's documentation HTML page.
action {name}
  query
    # The request name. If the name is not specified the documentation index is generated.
    optional string name

    # Remove navigation links.
    optional bool nonav
''')
        self._markdown = markdown
        self._styles = styles

    def _action_callback(self, ctx, req):
        request_name = req.get('name')
        root = None
        if request_name is None:
            root = self._index_html(ctx)
        elif request_name in ctx.app.requests:
            root = _DocElements(ctx.app.requests[request_name], nonav=req.get('nonav'), markdown=self._markdown, styles=self._styles)(ctx)
        if root is None:
            return ctx.response_text(HTTPStatus.NOT_FOUND, 'Unknown Request')
        content = root.serialize(indent='  ' if ctx.app.pretty_output else '')
        return ctx.response_text(HTTPStatus.OK, content, content_type='text/html')

    def _index_html(self, ctx):
        title = ctx.environ.get('HTTP_HOST') or (ctx.environ['SERVER_NAME'] + ':' + ctx.environ['SERVER_PORT'])

        # Group requests
        has_groups = False
        group_requests = {}
        for request in sorted(ctx.app.requests.values(), key=lambda x: x.name.lower()):
            has_groups = has_groups or request.doc_group is not None
            group_name = request.doc_group or 'Uncategorized'
            if group_name not in group_requests:
                group_requests[group_name] = []
            group_requests[group_name].append(request)

        return Element('html', children=[
            Element('head', children=[
                Element('meta', closed=False, charset='UTF-8'),
                Element('title', inline=True, children=Element(title, text=True)),
                Element('style', _type='text/css', children=Element(self._styles or STYLE_TEXT, text_raw=True))
            ]),
            Element('body', _class='chsl-index-body', children=[
                Element('h1', inline=True, children=Element(title, text=True)),
                [
                    [
                        Element('h2', inline=True, children=Element('Uncategorized' if group_name is None else group_name, text=True)) \
                        if has_groups else None,
                        Element('ul', _class='chsl-request-list', children=[
                            Element('li', inline=True, children=
                                    Element('a', href=ctx.reconstruct_url(query_string={'name': request.name}, relative=True),
                                            children=Element(request.name, text=True)))
                            for request in group_requests[group_name]
                        ])
                    ]
                    for group_name in sorted(group_requests.keys())
                ]
            ])
        ])


class DocPage(Action):
    """
    TODO
    """

    __slots__ = ('_request', '_request_urls', '_markdown', '_styles')

    def __init__(self, request, request_urls=None, markdown=None, styles=None, name=None, urls=(('GET', None),), doc=None, doc_group=None):
        request_name = request.name if isinstance(request, Request) else request.type_name
        if name is None:
            name = 'doc_' + request_name
        super().__init__(self._action_callback, name=name, urls=urls, doc=doc, doc_group=doc_group, wsgi_response=True, spec=f'''\
# Documentation page for {request_name}.
action {name}
''')
        self._request = request
        self._request_urls = request_urls
        self._markdown = markdown
        self._styles = styles

    def _action_callback(self, ctx, unused_req):
        root = _DocElements(self._request, request_urls=self._request_urls, markdown=self._markdown, styles=self._styles)(ctx)
        content = root.serialize(indent='  ' if ctx.app.pretty_output else '')
        return ctx.response_text(HTTPStatus.OK, content, content_type='text/html')


class _DocElements:
    __slots__ = ('_request', '_request_urls', '_nonav', '_markdown', '_styles')

    def __init__(self, request, request_urls=None, nonav=True, markdown=None, styles=None):
        self._request = request
        self._request_urls = request_urls
        self._nonav = nonav
        self._markdown = markdown
        self._styles = styles

    def __call__(self, ctx):
        is_request = isinstance(self._request, Request)
        is_action = isinstance(self._request, Action)
        if is_request and self._request_urls is None:
            request_urls = self._request.urls
        elif is_request and self._request_urls is not None:
            request_urls = [
                (method, ctx.reconstruct_url(path_info=url, query_string='', relative=True))
                for method, url in self._request_urls
            ]
        else:
            request_urls = None

        # Find all user types referenced by the action
        if is_action:
            struct_types = [typ for typ in get_referenced_types(self._request.model) if isinstance(typ, TypeStruct)]
            enum_types = [typ for typ in get_referenced_types(self._request.model) if isinstance(typ, TypeEnum)]
            typedef_types = [typ for typ in get_referenced_types(self._request.model) if isinstance(typ, Typedef)]
        elif not is_request:
            struct_types = [typ for typ in get_referenced_types(self._request) if isinstance(typ, TypeStruct)]
            enum_types = [typ for typ in get_referenced_types(self._request) if isinstance(typ, TypeEnum)]
            typedef_types = [typ for typ in get_referenced_types(self._request) if isinstance(typ, Typedef)]
        else:
            struct_types = enum_types = typedef_types = None

        return Element('html', children=[
            Element('head', children=[
                Element('meta', closed=False, charset='UTF-8'),
                Element('title', inline=True, children=Element(self._request.name if is_request else self._request.type_name, text=True)),
                Element('style', _type='text/css', children=Element(self._styles or STYLE_TEXT, text_raw=True))
            ]),
            Element('body', _class='chsl-request-body', children=[

                # Request page header
                None if self._nonav else Element('div', _class='chsl-header', children=[
                    Element('a', inline=True, href=ctx.reconstruct_url(query_string='', relative=True),
                            children=Element('Back to documentation index', text=True))
                ]),
                [
                    Element('h1', inline=True, children=Element(self._request.name, text=True)),
                    self._doc_text(self._request.doc)
                ] if is_request else [
                    self._typedef_section(self._request, 'h1') if isinstance(self._request, Typedef) else None,
                    self._struct_section(self._request, 'h1') if isinstance(self._request, TypeStruct) else None,
                    self._enum_section(self._request, 'h1') if isinstance(self._request, TypeEnum) else None
                ],

                # Notes
                Element('div', _class='chsl-notes', children=[

                    # Request URLs
                    None if not is_request or not request_urls else Element('div', _class='chsl-note', children=[
                        Element('p', children=[
                            Element('b', inline=True, children=Element('Note: ', text=True)),
                            Element(
                                'The request is exposed at the following ' + ('URLs' if len(request_urls) > 1 else 'URL') + ':',
                                text=True
                            )
                        ]),
                        Element('ul', children=[
                            Element('li', inline=True, children=Element(
                                'a', href=url, children=Element(url if method is None else method + ' ' + url, text=True)
                            ))
                            for method, url in request_urls
                        ])
                    ]),

                    # Non-default response
                    None if not (is_action and self._request.wsgi_response) else [
                        Element('div', _class='chsl-note', children=Element('p', children=[
                            Element('b', inline=True, children=Element('Note: ', text=True)),
                            Element('The action has a non-default response. See documentation for details.', text=True)
                        ]))
                    ]
                ]),

                # Request input and output structs
                None if not is_action else [
                    self._struct_section(self._request.model.path_type, 'h2', 'Path Parameters',
                                         ('The action has no path parameters.',)),
                    self._struct_section(self._request.model.query_type, 'h2', 'Query Parameters',
                                         ('The action has no query parameters.',)),
                    self._struct_section(self._request.model.input_type, 'h2', 'Input Parameters',
                                         ('The action has no input parameters.',)),
                    None if self._request.wsgi_response else [
                        self._struct_section(self._request.model.output_type, 'h2', 'Output Parameters',
                                             ('The action has no output parameters.',)),
                        self._enum_section(self._request.model.error_type, 'h2', 'Error Codes',
                                           ('The action returns no custom error codes.',))
                    ]
                ],

                # User types
                None if not typedef_types else [
                    Element('h2', inline=True, children=Element('Typedefs', text=True)),
                    [self._typedef_section(type_, 'h3') for type_ in typedef_types]
                ],
                None if not struct_types else [
                    Element('h2', inline=True, children=Element('Struct Types', text=True)),
                    [self._struct_section(type_, 'h3') for type_ in struct_types]
                ],
                None if not enum_types else [
                    Element('h2', inline=True, children=Element('Enum Types', text=True)),
                    [self._enum_section(type_, 'h3') for type_ in enum_types]
                ]
            ])
        ])

    RE_MARKDOWN_NEW_PARAGRAPH = re.compile(r'^\s*([#=\+\-\*]|[0-9]\.)')

    def _doc_text(self, doc):

        # User-provided markdown?
        if self._markdown is not None:
            if not isinstance(doc, str):
                doc = '\n'.join(doc)
            markdown_text = self._markdown(doc).strip()
            if not markdown_text:
                return None
            return Element('div', _class='chsl-text', children=Element(markdown_text, text_raw=True))

        # Separate text lines into paragraphs
        if isinstance(doc, str):
            doc = doc.splitlines()
        paragraphs = []
        lines = []
        for line in (line.strip() for line in doc):
            if line:
                if self.RE_MARKDOWN_NEW_PARAGRAPH.match(line):
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

        # Create the paragraph elements
        if not paragraphs:
            return None
        return Element('div', _class='chsl-text', children=[
            Element('p', children=Element('\n'.join(paragraph), text=True)) for paragraph in paragraphs
        ])

    @staticmethod
    def _type_name(type_):
        text_elem = Element(type_.type_name, text=True, inline=True)
        return text_elem if not isinstance(type_, (Typedef, TypeStruct, TypeEnum)) else \
            Element('a', inline=True, href='#' + type_.type_name, children=text_elem)

    @classmethod
    def _type_decl(cls, type_):
        if isinstance(type_, TypeArray):
            return [cls._type_name(type_.type), Element('&nbsp;[]', text_raw=True)]
        if isinstance(type_, TypeDict):
            return [
                None if type_.has_default_key_type() else [
                    cls._type_name(type_.key_type),
                    Element('&nbsp;:&nbsp;', text_raw=True)
                ],
                cls._type_name(type_.type),
                Element('&nbsp;{}', text_raw=True)
            ]
        return cls._type_name(type_)

    @staticmethod
    def _type_attr_helper(attr, value_name, len_name):
        if attr is None:
            return
        if attr.op_gt is not None:
            yield (value_name, '>', f'{attr.op_gt:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_gte is not None:
            yield (value_name, '>=', f'{attr.op_gte:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_lt is not None:
            yield (value_name, '<', f'{attr.op_lt:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_lte is not None:
            yield (value_name, '<=', f'{attr.op_lte:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_eq is not None:
            yield (value_name, '==', f'{attr.op_eq:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_len_gt is not None:
            yield (len_name, '>', f'{attr.op_len_gt:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_len_gte is not None:
            yield (len_name, '>=', f'{attr.op_len_gte:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_len_lt is not None:
            yield (len_name, '<', f'{attr.op_len_lt:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_len_lte is not None:
            yield (len_name, '<=', f'{attr.op_len_lte:.6f}'.rstrip('0').rstrip('.'))
        if attr.op_len_eq is not None:
            yield (len_name, '==', f'{attr.op_len_eq:.6f}'.rstrip('0').rstrip('.'))

    @classmethod
    def _type_attr(cls, type_, attr, optional, nullable):
        type_name = 'array' if isinstance(type_, TypeArray) else ('dict' if isinstance(type_, TypeDict) else 'value')
        type_attrs = []
        if optional:
            type_attrs.append(('optional', None, None))
        if nullable:
            type_attrs.append(('nullable', None, None))
        type_attrs.extend(cls._type_attr_helper(attr, type_name, 'len(' + type_name + ')'))
        if isinstance(type_, TypeDict):
            type_attrs.extend(cls._type_attr_helper(type_.key_attr, 'key', 'len(key)'))
        if isinstance(type_, (TypeArray, TypeDict)):
            type_attrs.extend(cls._type_attr_helper(type_.attr, 'elem', 'len(elem)'))

        return None if not type_attrs else Element('ul', _class='chsl-constraint-list', children=[
            Element('li', inline=True, children=[
                Element('span', _class='chsl-emphasis', children=Element(lhs, text=True)),
                None if operator is None else Element(' ' + operator + ' ' + repr(float(rhs)).rstrip('0').rstrip('.'), text=True)
            ])
            for lhs, operator, rhs in type_attrs
        ])

    def _typedef_section(self, type_, title_tag):
        attrs_element = self._type_attr(type_.type, type_.attr, False, False)
        no_attrs = not attrs_element
        return [
            Element(title_tag, inline=True, _id=type_.type_name,
                    children=Element('a', _class='linktarget', children=Element('typedef ' + type_.type_name, text=True))),
            self._doc_text(type_.doc),
            Element('table', children=[
                Element('tr', children=[
                    Element('th', inline=True, children=Element('Type', text=True)),
                    None if no_attrs else Element('th', inline=True, children=Element('Attributes', text=True))
                ]),
                Element('tr', children=[
                    Element('td', inline=True, children=self._type_decl(type_.type)),
                    None if no_attrs else Element('td', children=attrs_element)
                ])
            ])
        ]

    def _struct_section(self, type_, title_tag, title=None, empty_doc=None):
        if not title:
            title = ('union ' if type_.union else 'struct ') + type_.type_name
        if not empty_doc:
            empty_doc = ('The struct is empty.',)
        attrs_elements = {
            member.name: self._type_attr(member.type, member.attr, member.optional, member.nullable)
            for member in type_.members()
        }
        no_attrs = not any(attrs_elements.values())
        no_description = not any(member.doc for member in type_.members())
        return [
            Element(title_tag, inline=True, _id=type_.type_name,
                    children=Element('a', _class='linktarget', children=Element(title, text=True))),
            self._doc_text(type_.doc),
            self._doc_text(empty_doc) if not any(type_.members()) else Element('table', children=[
                Element('tr', children=[
                    Element('th', inline=True, children=Element('Name', text=True)),
                    Element('th', inline=True, children=Element('Type', text=True)),
                    None if no_attrs else Element('th', inline=True, children=Element('Attributes', text=True)),
                    None if no_description else Element('th', inline=True, children=Element('Description', text=True))
                ]),
                [
                    Element('tr', children=[
                        Element('td', inline=True, children=Element(member.name, text=True)),
                        Element('td', inline=True, children=self._type_decl(member.type)),
                        None if no_attrs else Element('td', children=attrs_elements[member.name]),
                        None if no_description else Element('td', children=self._doc_text(member.doc))
                    ])
                    for member in type_.members()
                ]
            ])
        ]

    def _enum_section(self, type_, title_tag, title=None, empty_doc=None):
        if not title:
            title = 'enum ' + type_.type_name
        if not empty_doc:
            empty_doc = ('The enum is empty.',)
        no_description = not any(value.doc for value in type_.values())
        return [
            Element(title_tag, inline=True, _id=type_.type_name,
                    children=Element('a', _class='linktarget', children=Element(title, text=True))),
            self._doc_text(type_.doc),
            self._doc_text(empty_doc) if not any(type_.values()) else Element('table', children=[
                Element('tr', children=[
                    Element('th', inline=True, children=Element('Value', text=True)),
                    None if no_description else Element('th', inline=True, children=Element('Description', text=True))
                ]),
                [
                    Element('tr', children=[
                        Element('td', inline=True, children=Element(value.value, text=True)),
                        None if no_description else Element('td', children=self._doc_text(value.doc))
                    ])
                    for value in type_.values()
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
