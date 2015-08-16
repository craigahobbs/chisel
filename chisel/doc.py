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

from .action import Action
from .compat import html_escape, iteritems, itervalues, urllib_parse_quote
from .model import JsonFloat, Typedef, TypeStruct, TypeEnum, TypeArray, TypeDict

from xml.sax.saxutils import quoteattr as saxutils_quoteattr


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
# Generate a documentation HTML for the requests implemented by the application.
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
            content = _index_html(ctx.environ, sorted(itervalues(ctx.app.requests), key=lambda x: x.name.lower())).serialize()
            return ctx.response_text('200 OK', content, content_type='text/html')
        elif request_name in ctx.app.requests:
            content = _request_html(ctx.environ, ctx.app.requests[request_name], req.get('nonav')).serialize()
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
        content = _request_html(ctx.environ, self.request, nonav=True).serialize()
        return ctx.response_text('200 OK', content, content_type='text/html')


class Element(object):
    """
    HTML5 DOM element
    """

    __slots__ = ('name', 'text', 'text_raw', 'closed', 'inline', 'attrs', 'children')

    def __init__(self, name, text=False, text_raw=False, closed=True, inline=False, **attrs):
        self.name = name
        self.text = text
        self.text_raw = text_raw
        self.closed = closed
        self.inline = inline
        self.attrs = attrs
        self.children = []

    def add_child(self, name, inline=None, **attrs):
        if inline is None:
            inline = self.inline
        child = Element(name, inline=inline, **attrs)
        self.children.append(child)
        return child

    def serialize_chunks(self, indent='  ', indent_index=0):

        # HTML5
        if indent_index <= 0:
            yield '<!doctype html>\n'

        # Initial newline and indent as necessary...
        if not self.inline and indent_index > 0:
            yield '\n'
            if not self.text and not self.text_raw:
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
        inline = self.inline
        for child in self.children:
            for chunk in child.serialize_chunks(indent=indent, indent_index=indent_index + 1):
                yield chunk
            inline = child.inline

        # Element close
        if not inline:
            yield '\n' + indent * indent_index
        yield '</' + self.name + '>'

    def serialize(self, indent='  '):
        return ''.join(self.serialize_chunks(indent=indent))


# Generate the top-level action documentation index
def _index_html(environ, requests):
    docRootUri = environ['SCRIPT_NAME'] + environ['PATH_INFO']

    # Index page header
    root = Element('html')
    head = root.add_child('head')
    head.add_child('meta', closed=False, charset='UTF-8')
    head.add_child('title').add_child('Actions', text=True, inline=True)
    _add_style(head)
    body = root.add_child('body', _class='chsl-index-body')

    # Index page title
    if 'HTTP_HOST' in environ:
        title = environ['HTTP_HOST']
    else:
        title = environ['SERVER_NAME'] + (':' + environ['SERVER_PORT'] if environ['SERVER_NAME'] != 80 else '')
    body.add_child('h1').add_child(title, text=True, inline=True)

    # Action and request links
    ulSections = body.add_child('ul', _class='chsl-request-section')
    for sectionTitle, sectionFilter in \
        (('Actions', lambda request: isinstance(request, Action)),
         ('Other Requests', lambda request: not isinstance(request, Action))):

        sectionRequests = [request for request in requests if sectionFilter(request)]
        if sectionRequests:
            liSection = ulSections.add_child('li')
            liSection.add_child('span', inline=True) \
                     .add_child(sectionTitle, text=True, inline=True)
            ulRequests = liSection.add_child('ul', _class='chsl-request-list')
            for request in sectionRequests:
                liRequest = ulRequests.add_child('li')
                liRequest.add_child('a', inline=True, href=docRootUri + '?name=' + urllib_parse_quote(request.name)) \
                         .add_child(request.name, text=True)

    return root


# Generate the documentation for a request
def _request_html(environ, request, nonav=False):
    docRootUri = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    isAction = isinstance(request, Action)

    # Request page header
    root = Element('html')
    head = root.add_child('head')
    head.add_child('meta', closed=False, charset='UTF-8')
    head.add_child('title').add_child(request.name, text=True, inline=True)
    _add_style(head)
    body = root.add_child('body', _class='chsl-request-body')
    if not nonav:
        header = body.add_child('div', _class='chsl-header')
        header.add_child('a', href=docRootUri) \
            .add_child('Back to documentation index', text=True, inline=True)

    # Request title
    body.add_child('h1') \
        .add_child(request.name, text=True, inline=True)
    _addDocText(body, request.model.doc if isAction else request.doc)

    # Note for request URLs
    notes = body.add_child('div', _class='chsl-notes')
    if request.urls:
        noteUrl = notes.add_child('div', _class='chsl-note')
        noteUrlP = noteUrl.add_child('p')
        noteUrlP.add_child('b').add_child('Note: ', text=True, inline=True)
        noteUrlP.add_child('The request is exposed at the following ' + ('URLs' if len(request.urls) > 1 else 'URL') + ':', text=True)
        ulUrls = noteUrl.add_child('ul')
        for url in request.urls:
            ulUrls.add_child('li').add_child('a', inline=True, href=url) \
                .add_child(url, text=True, inline=True)

    if isAction:
        # Note for custom response callback
        if request.wsgi_response:
            noteResponse = notes.add_child('div', _class='chsl-note')
            noteResponseP = noteResponse.add_child('p')
            noteResponseP.add_child('b').add_child('Note: ', text=True, inline=True)
            noteResponseP.add_child('The action has a non-default response. See documentation for details.', text=True)

        # Find all user types referenced by the action
        typedefTypes = {}
        structTypes = {}
        enumTypes = {}

        def addType(type_, membersOnly=False):
            if isinstance(type_, TypeStruct) and type_.typeName not in structTypes:
                if not membersOnly:
                    structTypes[type_.typeName] = type_
                for member in type_.members:
                    addType(member.type)
            elif isinstance(type_, TypeEnum) and type_.typeName not in enumTypes:
                enumTypes[type_.typeName] = type_
            elif isinstance(type_, Typedef) and type_.typeName not in typedefTypes:
                typedefTypes[type_.typeName] = type_
                addType(type_.type)
            elif isinstance(type_, TypeArray):
                addType(type_.type)
            elif isinstance(type_, TypeDict):
                addType(type_.type)
                addType(type_.keyType)

        addType(request.model.inputType, membersOnly=True)
        if not request.wsgi_response:
            addType(request.model.outputType, membersOnly=True)

        # Request input and output structs
        _structSection(body, request.model.inputType, 'h2', 'Input Parameters', 'The action has no input parameters.')
        if not request.wsgi_response:
            _structSection(body, request.model.outputType, 'h2', 'Output Parameters', 'The action has no output parameters.')
            _enumSection(body, request.model.errorType, 'h2', 'Error Codes', 'The action returns no custom error codes.')

        # User types
        if typedefTypes:
            body.add_child('h2') \
                .add_child('Typedefs', text=True, inline=True)
            for typedefType in sorted(itervalues(typedefTypes), key=lambda x: x.typeName.lower()):
                _typedefSection(body, typedefType)
        if structTypes:
            body.add_child('h2') \
                .add_child('Struct Types', text=True, inline=True)
            for structType in sorted(itervalues(structTypes), key=lambda x: x.typeName.lower()):
                _structSection(body, structType)
        if enumTypes:
            body.add_child('h2') \
                .add_child('Enum Types', text=True, inline=True)
            for enumType in sorted(itervalues(enumTypes), key=lambda x: x.typeName.lower()):
                _enumSection(body, enumType)

    return root


# Add style DOM helper
def _add_style(parent):

    # Built-in style
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
ul.chsl-request-section {
    list-style: none;
    margin: 0 0.5em;
}
ul.chsl-request-section li {
    margin: 1.5em 0;
}
ul.chsl-request-section li span {
    font-size: 1.4em;
    font-weight: bold;
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


# User type href helper
def _userTypeHref(type_):
    return type_.typeName

# Type name HTML helper
_userTypes = (Typedef, TypeStruct, TypeEnum)


def _addTypeNameHelper(parent, type_):
    if isinstance(type_, _userTypes):
        parent = parent.add_child('a', inline=True, href='#' + _userTypeHref(type_))
    parent.add_child(type_.typeName, text=True, inline=True)


def _addTypeName(parent, type_):
    if isinstance(type_, TypeArray):
        _addTypeNameHelper(parent, type_.type)
        parent.add_child('&nbsp;[]', text_raw=True, inline=True)
    elif isinstance(type_, TypeDict):
        if not type_.hasDefaultKeyType():
            _addTypeNameHelper(parent, type_.keyType)
            parent.add_child('&nbsp;:&nbsp;', text_raw=True, inline=True)
        _addTypeNameHelper(parent, type_.type)
        parent.add_child('&nbsp;{}', text_raw=True, inline=True)
    else:
        _addTypeNameHelper(parent, type_)


# Get attribute list - [(lhs, op, rhs), ...]
def _attributeList(attr, valueName, lenName):
    if attr is None:
        return
    if attr.gt is not None:
        yield (valueName, '>', str(JsonFloat(attr.gt, 6)))
    if attr.gte is not None:
        yield (valueName, '>=', str(JsonFloat(attr.gte, 6)))
    if attr.lt is not None:
        yield (valueName, '<', str(JsonFloat(attr.lt, 6)))
    if attr.lte is not None:
        yield (valueName, '<=', str(JsonFloat(attr.lte, 6)))
    if attr.eq is not None:
        yield (valueName, '==', str(JsonFloat(attr.eq, 6)))
    if attr.len_gt is not None:
        yield (lenName, '>', str(JsonFloat(attr.len_gt, 6)))
    if attr.len_gte is not None:
        yield (lenName, '>=', str(JsonFloat(attr.len_gte, 6)))
    if attr.len_lt is not None:
        yield (lenName, '<', str(JsonFloat(attr.len_lt, 6)))
    if attr.len_lte is not None:
        yield (lenName, '<=', str(JsonFloat(attr.len_lte, 6)))
    if attr.len_eq is not None:
        yield (lenName, '==', str(JsonFloat(attr.len_eq, 6)))


# Attribute DOM helper
def _attributeDom(ul, lhs, op, rhs):
    li = ul.add_child('li')
    li.add_child('span', inline=True, _class='chsl-emphasis').add_child(lhs, text=True)
    if op is not None and rhs is not None:
        li.add_child(' ' + op + ' ' + repr(float(rhs)).rstrip('0').rstrip('.'), text=True, inline=True)


# Type attributes HTML helper
def _addTypeAttr(parent, type_, attr, isOptional):

    # Add attribute DOM elements
    ul = parent.add_child('ul', _class='chsl-constraint-list')
    if isOptional:
        _attributeDom(ul, 'optional', None, None)
    typeName = 'array' if isinstance(type_, TypeArray) else ('dict' if isinstance(type_, TypeDict) else 'value')
    for lhs, op, rhs in _attributeList(attr, typeName, 'len(' + typeName + ')'):
        _attributeDom(ul, lhs, op, rhs)
    if hasattr(type_, 'keyType'):
        for lhs, op, rhs in _attributeList(type_.keyAttr, 'key', 'len(key)'):
            _attributeDom(ul, lhs, op, rhs)
    if hasattr(type_, 'type'):
        for lhs, op, rhs in _attributeList(type_.attr, 'elem', 'len(elem)'):
            _attributeDom(ul, lhs, op, rhs)

    # No constraints?
    if not ul.children:
        _attributeDom(ul, 'none', None, None)


# Add text DOM elements
def _addText(parent, texts):
    div = None
    for text in texts:
        if div is None:
            div = parent.add_child('div', _class='chsl-text')
        div.add_child('p') \
           .add_child(text, text=True)


# Documentation comment text HTML helper
def _addDocText(parent, doc):

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
    _addText(parent, ('\n'.join(lines) for lines in paragraphs))


# Typedef section helper
def _typedefSection(parent, type_):

    # Section title
    parent.add_child('h3', _id=_userTypeHref(type_)) \
        .add_child('a', inline=True, _class='linktarget') \
        .add_child('typedef ' + type_.typeName, text=True)
    _addDocText(parent, type_.doc)

    # Table header
    table = parent.add_child('table')
    tr = table.add_child('tr')
    tr.add_child('th').add_child('Type', text=True, inline=True)
    tr.add_child('th').add_child('Attributes', text=True, inline=True)

    # Typedef type/attr rows
    tr = table.add_child('tr')
    _addTypeName(tr.add_child('td'), type_.type)
    _addTypeAttr(tr.add_child('td'), type_.type, type_.attr, False)


# Struct section helper
def _structSection(parent, type_, titleTag=None, title=None, emptyMessage=None):

    # Defaults
    if titleTag is None:
        titleTag = 'h3'
    if title is None:
        title = ('union ' if type_.isUnion else 'struct ') + type_.typeName
    if emptyMessage is None:
        emptyMessage = 'The struct is empty.'

    # Section title
    parent.add_child(titleTag, _id=_userTypeHref(type_)) \
        .add_child('a', inline=True, _class='linktarget') \
        .add_child(title, text=True)
    _addDocText(parent, type_.doc)

    # Empty struct?
    if not type_.members:
        _addText(parent, (emptyMessage,))
    else:
        # Has description header?
        hasDescription = any(member.doc for member in type_.members)

        # Table header
        table = parent.add_child('table')
        tr = table.add_child('tr')
        tr.add_child('th').add_child('Name', text=True, inline=True)
        tr.add_child('th').add_child('Type', text=True, inline=True)
        tr.add_child('th').add_child('Attributes', text=True, inline=True)
        if hasDescription:
            tr.add_child('th').add_child('Description', text=True, inline=True)

        # Struct member rows
        for member in type_.members:
            tr = table.add_child('tr')
            tr.add_child('td').add_child(member.name, text=True, inline=True)
            _addTypeName(tr.add_child('td'), member.type)
            _addTypeAttr(tr.add_child('td'), member.type, member.attr, member.isOptional)
            if hasDescription:
                _addDocText(tr.add_child('td'), member.doc)


# Enum section helper
def _enumSection(parent, type_, titleTag=None, title=None, emptyMessage=None):

    # Defaults
    if titleTag is None:
        titleTag = 'h3'
    if title is None:
        title = 'enum ' + type_.typeName
    if emptyMessage is None:
        emptyMessage = 'The enum is empty.'

    # Section title
    parent.add_child(titleTag, _id=_userTypeHref(type_)) \
        .add_child('a', inline=True, _class='linktarget') \
        .add_child(title, text=True)
    _addDocText(parent, type_.doc)

    # Empty enum?
    if not type_.values:
        _addText(parent, (emptyMessage,))
    else:
        # Has description header?
        hasDescription = any(value.doc for value in type_.values)

        # Table header
        table = parent.add_child('table')
        tr = table.add_child('tr')
        tr.add_child('th').add_child('Value', text=True, inline=True)
        if hasDescription:
            tr.add_child('th').add_child('Description', text=True, inline=True)

        # Enum value rows
        for value in type_.values:
            tr = table.add_child('tr')
            tr.add_child('td').add_child(value.value, text=True, inline=True)
            if hasDescription:
                _addDocText(tr.add_child('td'), value.doc)
