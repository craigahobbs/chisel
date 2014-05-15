#
# Copyright (C) 2012-2013 Craig Hobbs
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
from .compat import cgi, iteritems, itervalues, StringIO, urllib
from .model import TypeStruct, TypeEnum, TypeArray, TypeDict

import xml.sax.saxutils as saxutils


# Doc action callback
class DocAction(Action):

    def __init__(self):
        Action.__init__(self, self.action, response = self.actionResponse,
                        spec = '''\
# Generate a documentation HTML for the requests implemented by the application.
action doc
  input
    # Generate documentation for the specified request name; generate the
    # documentation index if the request name is not specified.
    [optional] string name

    # Remove navigation links.
    [optional] bool nonav
''')

    def action(self, app, req):
        return {}

    def actionResponse(self, app, req, response):

        requestName = req.get('name')
        if requestName is None:
            requests = sorted(itervalues(app.requests), key = lambda x: x.name.lower())
            return app.responseText('200 OK', createIndexHtml(app.environ, requests), contentType = 'text/html')
        elif requestName in app.requests:
            return app.responseText('200 OK', createRequestHtml(app.environ, app.requests[requestName], req.get('nonav')), contentType = 'text/html')
        else:
            return app.responseText('500 Internal Server Error', 'Unknown Action')


# HTML DOM helper class
class Element(object):
    __slots__ = ('name', 'isText', 'isTextEscaped', 'isClosed', 'isInline', 'attrs', 'children')

    def __init__(self, name, isText = False, isTextEscaped = True, isClosed = True, isInline = False, **attrs):
        self.name = name
        self.isText = isText
        self.isTextEscaped = isTextEscaped
        self.isClosed = isClosed
        self.isInline = isInline
        self.attrs = attrs
        self.children = []

    def addChild(self, name, isInline = None, **attrs):
        if isInline is None:
            isInline = self.isInline
        child = Element(name, isInline = isInline, **attrs)
        self.children.append(child)
        return child

    def serialize(self, out, indent = '  ', indentIndex = 0, isRoot = True):

        indentCur = indent * indentIndex

        # Initial newline and indent as necessary...
        if not self.isInline and not isRoot:
            out.write('\n')
            if not self.isText:
                out.write(indentCur)

        # Text element?
        if self.isText:
            out.write(cgi.escape(self.name) if self.isTextEscaped else self.name)
            return

        # Element open
        out.write('<' + self.name)
        for attrKey, attrValue in sorted(iteritems(self.attrs), key = lambda x: x[0].lstrip('_')):
            out.write(' ' + attrKey.lstrip('_') + '=' + saxutils.quoteattr(attrValue))
        out.write('>')
        if not self.isClosed and not self.children:
            return

        # Children elements
        childPrevInline = self.isInline
        for child in self.children:
            child.serialize(out, indent, indentIndex + 1, False)
            childPrevInline = child.isInline

        # Element close
        if not childPrevInline:
            out.write('\n' + indentCur)
        out.write('</' + self.name + '>')


# Generate the top-level action documentation index
def createIndexHtml(environ, requests):

    docRootUri = environ['SCRIPT_NAME'] + environ['PATH_INFO']

    # Index page header
    root = Element('html')
    head = root.addChild('head')
    head.addChild('meta', isClosed = False, charset = 'UTF-8')
    head.addChild('title').addChild('Actions', isText = True, isInline = True)
    _addStyle(head)
    body = root.addChild('body', _class = 'chsl-index-body')

    # Index page title
    if 'HTTP_HOST' in environ:
        title = environ['HTTP_HOST']
    else:
        title = environ['SERVER_NAME'] + (':' + environ['SERVER_PORT'] if environ['SERVER_NAME'] != 80 else '')
    body.addChild('h1').addChild(title, isText = True, isInline = True)

    # Action and request links
    ulSections = body.addChild('ul', _class = 'chsl-request-section')
    for sectionTitle, sectionFilter in \
        (('Actions', lambda request: isinstance(request, Action)),
         ('Other Requests', lambda request: not isinstance(request, Action))):

        sectionRequests = [request for request in requests if sectionFilter(request)]
        if sectionRequests:
            liSection = ulSections.addChild('li')
            liSection.addChild('span', isInline = True) \
                     .addChild(sectionTitle, isText = True, isInline = True)
            ulRequests = liSection.addChild('ul', _class = 'chsl-request-list')
            for request in sectionRequests:
                liRequest = ulRequests.addChild('li')
                liRequest.addChild('a', isInline = True, href = docRootUri + '?name=' + urllib.quote(request.name)) \
                         .addChild(request.name, isText = True)

    # Serialize
    out = StringIO()
    out.write('<!doctype html>')
    root.serialize(out)
    return out.getvalue()


# Generate the documentation for a request
def createRequestHtml(environ, request, nonav = False):

    docRootUri = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    isAction = isinstance(request, Action)

    # Request page header
    root = Element('html')
    head = root.addChild('head')
    head.addChild('meta', isClosed = False, charset = 'UTF-8')
    head.addChild('title').addChild(request.name, isText = True, isInline = True)
    _addStyle(head)
    body = root.addChild('body', _class = 'chsl-request-body')
    if not nonav:
        header = body.addChild('div', _class = 'chsl-header');
        header.addChild('a', href = docRootUri) \
            .addChild('Back to documentation index', isText = True, isInline = True)

    # Request title
    body.addChild('h1') \
        .addChild(request.name, isText = True, isInline = True)
    _addDocText(body, request.model.doc if isAction else request.doc)

    # Note for request URLs
    notes = body.addChild('div', _class = 'chsl-notes')
    if request.urls:
        noteUrl = notes.addChild('div', _class = 'chsl-note')
        noteUrlP = noteUrl.addChild('p')
        noteUrlP.addChild('b').addChild('Note: ', isText = True, isInline = True)
        noteUrlP.addChild('The request is exposed at the following ' + ('URLs' if len(request.urls) > 1 else 'URL') + ':', isText = True)
        ulUrls = noteUrl.addChild('ul')
        for url in request.urls:
            ulUrls.addChild('li').addChild('a', isInline = True, href = url) \
                .addChild(url, isText = True, isInline = True)

    if isAction:
        # Note for custom response callback
        if request.response is not None:
            noteResponse = notes.addChild('div', _class = 'chsl-note')
            noteResponseP = noteResponse.addChild('p')
            noteResponseP.addChild('b').addChild('Note: ', isText = True, isInline = True)
            noteResponseP.addChild('The action has a non-default response. See documentation for details.', isText = True)

        # Find all user types referenced by the action
        structTypes = {}
        enumTypes = {}
        def findUserTypes(structType):
            for member in structType.members:
                baseType = member.typeInst.typeInst if hasattr(member.typeInst, 'typeInst') else member.typeInst
                if isinstance(baseType, TypeStruct) and baseType.typeName not in structTypes:
                    structTypes[baseType.typeName] = baseType
                    findUserTypes(baseType)
                elif isinstance(baseType, TypeEnum) and baseType.typeName not in enumTypes:
                    enumTypes[baseType.typeName] = baseType
        findUserTypes(request.model.inputType)
        if request.response is None:
            findUserTypes(request.model.outputType)

        # Request input and output structs
        _structSection(body, request.model.inputType, 'h2', 'Input Parameters', 'The action has no input parameters.')
        if request.response is None:
            _structSection(body, request.model.outputType, 'h2', 'Output Parameters', 'The action has no output parameters.')
            _enumSection(body, request.model.errorType, 'h2', 'Error Codes', 'The action returns no custom error codes.')

        # User types
        if structTypes:
            body.addChild('h2') \
                .addChild('Struct Types', isText = True, isInline = True)
            for structType in sorted(itervalues(structTypes), key = lambda x: x.typeName.lower()):
                _structSection(body, structType)
        if enumTypes:
            body.addChild('h2') \
                .addChild('Enum Types', isText = True, isInline = True)
            for enumType in sorted(itervalues(enumTypes), key = lambda x: x.typeName.lower()):
                _enumSection(body, enumType)

    # Serialize
    out = StringIO()
    out.write('<!doctype html>')
    root.serialize(out)
    return out.getvalue()


# Add style DOM helper
def _addStyle(parent):

    # Built-in style
    parent.addChild('style', _type = 'text/css') \
        .addChild('''\
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
}''', isText = True, isTextEscaped = False)

# User type href helper
def _userTypeHref(typeInst):
    return typeInst.typeName

# Type name HTML helper
def _addTypeName(parent, typeInst):

    # Compute the type string
    if isinstance(typeInst, TypeArray):
        baseTypeInst = typeInst.typeInst
        typeExtra = '[]'
    elif isinstance(typeInst, TypeDict):
        baseTypeInst = typeInst.typeInst
        typeExtra = '{}'
    else:
        baseTypeInst = typeInst
        typeExtra = None

    # Generate the type string DOM
    if isinstance(baseTypeInst, TypeStruct) or isinstance(baseTypeInst, TypeEnum):
        parent.addChild('a', isInline = True, href = '#' + _userTypeHref(baseTypeInst)) \
            .addChild(baseTypeInst.typeName, isText = True)
    else:
        parent.addChild(baseTypeInst.typeName, isText = True, isInline = True)
    if typeExtra:
        parent.addChild(typeExtra, isText = True, isInline = True)

# Attribute DOM helper
def _attributeDom(ul, lhs, op, rhs):
    li = ul.addChild('li')
    li.addChild('span', isInline = True, _class = 'chsl-emphasis').addChild(lhs, isText = True)
    if op is not None and rhs is not None:
        li.addChild(' ' + op + ' ' + repr(float(rhs)).rstrip('0').rstrip('.'), isText = True, isInline = True)

# Type attributes HTML helper
def _addTypeAttr(parent, member):
    typeInst = member.typeInst

    # Add attribute DOM elements
    ul = parent.addChild('ul', _class = 'chsl-constraint-list')
    if member.isOptional:
        _attributeDom(ul, 'optional', None, None)
    if hasattr(typeInst, 'constraint_gt') and typeInst.constraint_gt is not None:
        _attributeDom(ul, 'value', '>', typeInst.constraint_gt)
    if hasattr(typeInst, 'constraint_gte') and typeInst.constraint_gte is not None:
        _attributeDom(ul, 'value', '>=', typeInst.constraint_gte)
    if hasattr(typeInst, 'constraint_lt') and typeInst.constraint_lt is not None:
        _attributeDom(ul, 'value', '<', typeInst.constraint_lt)
    if hasattr(typeInst, 'constraint_lte') and typeInst.constraint_lte is not None:
        _attributeDom(ul, 'value', '<=', typeInst.constraint_lte)
    if hasattr(typeInst, 'constraint_len_gt') and typeInst.constraint_len_gt is not None:
        _attributeDom(ul, 'len', '>', typeInst.constraint_len_gt)
    if hasattr(typeInst, 'constraint_len_gte') and typeInst.constraint_len_gte is not None:
        _attributeDom(ul, 'len', '>=', typeInst.constraint_len_gte)
    if hasattr(typeInst, 'constraint_len_lt') and typeInst.constraint_len_lt is not None:
        _attributeDom(ul, 'len', '<', typeInst.constraint_len_lt)
    if hasattr(typeInst, 'constraint_len_lte') and typeInst.constraint_len_lte is not None:
        _attributeDom(ul, 'len', '<=', typeInst.constraint_len_lte)

    # No constraints?
    if not ul.children:
        _attributeDom(ul, 'none', None, None)

# Add text DOM elements
def _addText(parent, texts):
    div = None
    for text in texts:
        if div is None:
            div = parent.addChild('div', _class = 'chsl-text')
        div.addChild('p') \
           .addChild(text, isText = True)

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

# Struct section helper
def _structSection(parent, typeInst, titleTag = None, title = None, emptyMessage = None):

    # Defaults
    if titleTag is None:
        titleTag = 'h3'
    if title is None:
        title = ('union ' if typeInst.isUnion else 'struct ') + typeInst.typeName
    if emptyMessage is None:
        emptyMessage = 'The struct is empty.'

    # Section title
    parent.addChild(titleTag, _id = _userTypeHref(typeInst)) \
        .addChild('a', isInline = True, _class = 'linktarget') \
        .addChild(title, isText = True)
    _addDocText(parent, typeInst.doc)

    # Empty struct?
    if not typeInst.members:
        _addText(parent, (emptyMessage,))
    else:
        # Has description header?
        hasDescription = any(member.doc for member in typeInst.members)

        # Table header
        table = parent.addChild('table')
        tr = table.addChild('tr')
        tr.addChild('th').addChild('Name', isText = True, isInline = True)
        tr.addChild('th').addChild('Type', isText = True, isInline = True)
        tr.addChild('th').addChild('Attributes', isText = True, isInline = True)
        if hasDescription:
            tr.addChild('th').addChild('Description', isText = True, isInline = True)

        # Struct member rows
        for member in typeInst.members:
            tr = table.addChild('tr')
            tr.addChild('td').addChild(member.name, isText = True, isInline = True)
            _addTypeName(tr.addChild('td'), member.typeInst)
            _addTypeAttr(tr.addChild('td'), member)
            if hasDescription:
                _addDocText(tr.addChild('td'), member.doc)

# Enum section helper
def _enumSection(parent, typeInst, titleTag = None, title = None, emptyMessage = None):

    # Defaults
    if titleTag is None:
        titleTag = 'h3'
    if title is None:
        title = 'enum ' + typeInst.typeName
    if emptyMessage is None:
        emptyMessage = 'The enum is empty.'

    # Section title
    parent.addChild(titleTag, _id = _userTypeHref(typeInst)) \
        .addChild('a', isInline = True, _class = 'linktarget') \
        .addChild(title, isText = True)
    _addDocText(parent, typeInst.doc)

    # Empty enum?
    if not typeInst.values:
        _addText(parent, (emptyMessage,))
    else:
        # Has description header?
        hasDescription = any(value.doc for value in typeInst.values)

        # Table header
        table = parent.addChild('table')
        tr = table.addChild('tr')
        tr.addChild('th').addChild('Value', isText = True, isInline = True)
        if hasDescription:
            tr.addChild('th').addChild('Description', isText = True, isInline = True)

        # Enum value rows
        for value in typeInst.values:
            tr = table.addChild('tr')
            tr.addChild('td').addChild(value.value, isText = True, isInline = True)
            if hasDescription:
                _addDocText(tr.addChild('td'), value.doc)
