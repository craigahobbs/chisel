#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import cgi
from StringIO import StringIO
import urllib
import xml.sax.saxutils as saxutils

from .model import TypeStruct, TypeEnum, TypeArray, TypeDict


# Helper function to join parts of a URL
def joinUrl(*args):

    return '/'.join(s.strip('/') for s in args)


# HTML DOM helper class
class Element:

    def __init__(self, name, isText = False, isClosed = True, isInline = False, **attrs):

        self.name = name
        self.isText = isText
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

    def serialize(self, out, indent = "  ", indentIndex = 0):

        indentCur = indent * indentIndex

        # Initial newline and indent as necessary...
        if not self.isInline:
            out.write("\n")
            if not self.isText:
                out.write(indentCur)

        # Text element?
        if self.isText:
            out.write(cgi.escape(self.name))
            return

        # Element open
        out.write("<")
        out.write(self.name)
        for attrKey, attrValue in self.attrs.iteritems():
            out.write(" ")
            out.write(attrKey.lstrip("_"))
            out.write("=")
            out.write(saxutils.quoteattr(attrValue))
        out.write(">")
        if not self.isClosed and not self.children:
            return

        # Children elements
        childPrevInline = self.isInline
        for child in self.children:
            child.serialize(out, indent = indent, indentIndex = indentIndex + 1)
            childPrevInline = child.isInline

        # Element close
        if not childPrevInline:
            out.write("\n")
            out.write(indentCur)
        out.write("</")
        out.write(self.name)
        out.write(">")


# Generate the top-level action documentation index
def docIndex(docRootUri, actionModels, docCssUri = None):

    # Index page header
    root = Element("html")
    head = root.addChild("head")
    head.addChild("meta", isClosed = False, charset = "UTF-8")
    head.addChild("title").addChild("Actions", isText = True, isInline = True)
    _addStyle(head, docCssUri)
    body = root.addChild("body", _class = "chsl-index-body")
    body.addChild("h1") \
        .addChild("Actions", isText = True, isInline = True)

    # Action docs hyperlinks
    ul = body.addChild("ul", _class = "chsl-action-list")
    for actionModel in sorted(actionModels, key = lambda x: x.name):
        li = ul.addChild("li")
        li.addChild("a", isInline = True, href = joinUrl(docRootUri, urllib.quote(actionModel.name))) \
            .addChild(actionModel.name, isText = True)

    # Serialize
    out = StringIO()
    out.write("<!doctype html>")
    root.serialize(out)
    return out.getvalue()


# Generate the documentation for an action
def docAction(docRootUri, actionModel, docCssUri = None):

    # Find all user types referenced by the action
    userTypes = {}
    def findUserTypes(structType):
        for member in structType.members:
            baseType = member.typeInst.typeInst if hasattr(member.typeInst, "typeInst") else member.typeInst
            if isinstance(baseType, TypeStruct) or isinstance(baseType, TypeEnum):
                if baseType.typeName not in userTypes:
                    userTypes[baseType.typeName] = baseType
            if isinstance(baseType, TypeStruct):
                findUserTypes(baseType)
    findUserTypes(actionModel.inputType)
    findUserTypes(actionModel.outputType)

    # Action page header
    root = Element("html")
    head = root.addChild("head")
    head.addChild("meta", isClosed = False, charset = "UTF-8")
    head.addChild("title").addChild(actionModel.name, isText = True, isInline = True)
    _addStyle(head, docCssUri)
    body = root.addChild("body", _class = "chsl-action-body")
    header = body.addChild("div", _class = "chsl-header");
    header.addChild("a", href = docRootUri) \
        .addChild("Back to documentation index", isText = True, isInline = True)

    # Action title
    body.addChild("h1") \
        .addChild(actionModel.name, isText = True, isInline = True)
    _addDocText(body, actionModel.doc)

    # Action input and output structs
    _structSection(body, actionModel.inputType, "h2", "Input Parameters", "The action has no input parameters.")
    _structSection(body, actionModel.outputType, "h2", "Output Parameters", "The action has no output parameters.")
    _enumSection(body, actionModel.errorType, "h2", "Error Codes", "The action returns no custom error codes.")

    # User types
    if userTypes:
        body.addChild("h2") \
            .addChild("User Types", isText = True, isInline = True)
        for userType in sorted(userTypes.itervalues(), key = lambda x: x.typeName):
            if isinstance(userType, TypeStruct):
                _structSection(body, userType)
            elif isinstance(userType, TypeEnum):
                _enumSection(body, userType)

    # Serialize
    out = StringIO()
    out.write("<!doctype html>")
    root.serialize(out)
    return out.getvalue()


# Add style DOM helper
def _addStyle(parent, docCssUri = None):

    # External CSS URL provided?
    if docCssUri is not None:

        # External style
        parent.addChild("link", isClosed = False, _type = "text/css", rel = "stylesheet", href = docCssUri)

    else:

        # Default style
        parent.addChild("style", _type = "text/css") \
            .addChild("""\
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
    font-family: "Helvetica", "Arial", sans-serif;
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
    border-style: none none solid none;
    border-width: 1px;
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
ul.chsl-action-list {
    list-style: none;
    margin: 0 .2em;
}
ul.chsl-action-list li {
    margin: 0.75em 0.5em;
    font-size: 1.25em;
}
div.chsl-header {
    margin: .25em 0;
}
ul.chsl-constraint-list {
    list-style: none;
}
.chsl-emphasis {
    font-style:italic;
}""", isText = True)

# Is user type?
def _isUserType(typeInst):

    return isinstance(typeInst, TypeStruct) or isinstance(typeInst, TypeEnum)

# User type href helper
def _userTypeHref(typeInst):

    return typeInst.typeName

# Type name HTML helper
def _addTypeName(parent, typeInst):

    # Compute the type string
    if isinstance(typeInst, TypeArray):
        baseTypeInst = typeInst.typeInst
        typeExtra = "[]"
    elif isinstance(typeInst, TypeDict):
        baseTypeInst = typeInst.typeInst
        typeExtra = "{}"
    else:
        baseTypeInst = typeInst
        typeExtra = None

    # Generate the type string DOM
    if _isUserType(baseTypeInst):
        parent.addChild("a", isInline = True, href = "#" + _userTypeHref(baseTypeInst)) \
            .addChild(baseTypeInst.typeName, isText = True)
    else:
        parent.addChild(baseTypeInst.typeName, isText = True, isInline = True)
    if typeExtra:
        parent.addChild(typeExtra, isText = True, isInline = True)

# Type attributes HTML helper
def _addTypeAttr(parent, typeInst):

    # Constraint DOM helper
    def constraintDom(ul, lhs, op, rhs):
        li = ul.addChild("li")
        li.addChild("span", isInline = True, _class = "chsl-emphasis").addChild(lhs, isText = True)
        if op and rhs:
            li.addChild(" %s %f" % (op, rhs), isText = True, isInline = True)

    # Add constraint DOM elements
    ul = parent.addChild("ul", _class = "chsl-constraint-list")
    if hasattr(typeInst, "constraint_gt") and typeInst.constraint_gt is not None:
        constraintDom(ul, "value", ">", typeInst.constraint_gt)
    if hasattr(typeInst, "constraint_gte") and typeInst.constraint_gte is not None:
        constraintDom(ul, "value", ">=", typeInst.constraint_gte)
    if hasattr(typeInst, "constraint_lt") and typeInst.constraint_lt is not None:
        constraintDom(ul, "value", "<", typeInst.constraint_lt)
    if hasattr(typeInst, "constraint_lte") and typeInst.constraint_lte is not None:
        constraintDom(ul, "value", "<=", typeInst.constraint_lte)
    if hasattr(typeInst, "constraint_len_gt") and typeInst.constraint_len_gt is not None:
        constraintDom(ul, "len", ">", typeInst.constraint_len_gt)
    if hasattr(typeInst, "constraint_len_gte") and typeInst.constraint_len_gte is not None:
        constraintDom(ul, "len", ">=", typeInst.constraint_len_gte)
    if hasattr(typeInst, "constraint_len_lt") and typeInst.constraint_len_lt is not None:
        constraintDom(ul, "len", "<", typeInst.constraint_len_lt)
    if hasattr(typeInst, "constraint_len_lte") and typeInst.constraint_len_lte is not None:
        constraintDom(ul, "len", "<=", typeInst.constraint_len_lte)

    # No constraints?
    if not ul.children:
        constraintDom(ul, "None", None, None)

# Add text DOM elements
def _addText(parent, texts):

    if texts:
        div = parent.addChild("div", _class = "chsl-text")
        for text in texts:
            div.addChild("p") \
                .addChild(text, isText = True)

# Documentation comment text HTML helper
def _addDocText(parent, doc):

    # Group paragraphs
    paragraphs = []
    if doc:
        lines = []
        for line in doc:
            if line:
                lines.append(line)
            else:
                if lines:
                    paragraphs.append(lines)
                    lines = []
        if lines:
            paragraphs.append(lines)

    # Add the text DOM elements
    _addText(parent, ["\n".join(lines) for lines in paragraphs])

# Struct section helper
def _structSection(parent, typeInst, titleTag = None, title = None, emptyMessage = None):

    # Defaults
    if titleTag is None:
        titleTag = "h3"
    if title is None:
        title = "struct " + typeInst.typeName
    if emptyMessage is None:
        emptyMessage = "The struct is empty."

    # Section title
    parent.addChild(titleTag, _id = _userTypeHref(typeInst)) \
        .addChild("a", isInline = True, _class = "linktarget") \
        .addChild(title, isText = True)
    _addDocText(parent, typeInst.doc)

    # Empty struct?
    if not typeInst.members:

        _addText(parent, [emptyMessage])

    else:

        # Table header
        table = parent.addChild("table")
        tr = table.addChild("tr")
        tr.addChild("th").addChild("Name", isText = True, isInline = True)
        tr.addChild("th").addChild("Type", isText = True, isInline = True)
        tr.addChild("th").addChild("Optional", isText = True, isInline = True)
        tr.addChild("th").addChild("Constraints", isText = True, isInline = True)
        tr.addChild("th").addChild("Description", isText = True, isInline = True)

        # Struct member rows
        for member in typeInst.members:
            tr = table.addChild("tr")
            tr.addChild("td").addChild(member.name, isText = True, isInline = True)
            _addTypeName(tr.addChild("td"), member.typeInst)
            tr.addChild("td").addChild("yes" if member.isOptional else "no", isText = True, isInline = True)
            _addTypeAttr(tr.addChild("td"), member.typeInst)
            _addDocText(tr.addChild("td"), member.doc)

# Enum section helper
def _enumSection(parent, typeInst, titleTag = None, title = None, emptyMessage = None):

    # Defaults
    if titleTag is None:
        titleTag = "h3"
    if title is None:
        title = "enum " + typeInst.typeName
    if emptyMessage is None:
        emptyMessage = "The enum is empty."

    # Section title
    parent.addChild(titleTag, _id = _userTypeHref(typeInst)) \
        .addChild("a", isInline = True, _class = "linktarget") \
        .addChild(title, isText = True)
    _addDocText(parent, typeInst.doc)

    # Empty struct?
    if not typeInst.values:

        _addText(parent, [emptyMessage])

    else:

        # Table header
        table = parent.addChild("table")
        tr = table.addChild("tr")
        tr.addChild("th").addChild("Value", isText = True, isInline = True)
        tr.addChild("th").addChild("Description", isText = True, IsInline = True)

        # Enum value rows
        for value in typeInst.values:
            tr = table.addChild("tr")
            tr.addChild("td").addChild(value.value, isText = True, isInline = True)
            _addDocText(tr.addChild("td"), value.doc)
