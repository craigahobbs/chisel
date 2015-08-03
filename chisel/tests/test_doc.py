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

import chisel
from chisel.compat import HTMLParser
from chisel.doc import Element

import sys
import unittest


# Simple HTML validator class
class HTMLValidator(HTMLParser):

    def __init__(self):
        # Default value for convert_charrefs (added in Python 3.4) changed in Python 3.5
        if sys.version_info >= (3, 4):
            HTMLParser.__init__(self, convert_charrefs=True)
        else:
            HTMLParser.__init__(self)
        self.elements = []

    def handle_starttag(self, tag, attrs):
        if tag not in ('br', 'img', 'link', 'meta'):
            self.elements.append(tag)

    def handle_endtag(self, tag):
        expectedTag = self.elements.pop() if self.elements else None
        assert expectedTag == tag, "Expected '%s' element, got '%s'" % (expectedTag, tag)

    def close(self):
        assert not self.elements, 'Un-popped HTML elements! %r' % (self.elements,)
        HTMLParser.close(self)

    @staticmethod
    def validate(html):
        htmlParser = HTMLValidator()
        htmlParser.feed(html)
        htmlParser.close()


# Documentation generation tests
class TestDoc(unittest.TestCase):

    _spec = '''\
# My enum
enum MyEnum
    # A value
    Value1
    Value2

#
# My struct
# - continuing
#
# Another paragraph
struct MyStruct

    # My int member
    # - continuing
    #
    # Another paragraph
    #
    int(> 5) member1

    # My float member
    float(< 6.5) member2

    bool member3
    string(len > 0) member4
    datetime member5
    MyEnum member6
    MyStruct member7
    MyEnum[len > 0] member8
    MyStruct{} member9
    MyEnum : MyStruct{len > 0} member10
    string(len == 2) : int(> 5){len > 0} member11
    date member12

# An unused struct
# My Union
union MyUnion
    int a
    string b

# A typedef
typedef string(len == 2) : MyStruct {len > 0} MyTypedef

action myAction1
    input
        MyStruct struct
        MyTypedef typedef

action myAction2
    output
        MyUnion union
    errors
        MyError1
        MyError2
'''

    _environ = {
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'HTTP_HOST': 'localhost:8080'
    }

    _environ2 = {
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8080'
    }

    def setUp(self):

        # Application object
        self.app = chisel.Application()
        self.app.loadSpecString(self._spec)
        self.app.addRequest(chisel.Action(lambda app, req: {}, name='myAction1'))
        self.app.addRequest(chisel.Action(lambda app, req: {}, name='myAction2'))
        self.app.addRequest(chisel.DocAction())

    # Test documentation index HTML generation
    def test_doc_DocAction_index(self):

        # Validate the HTML
        status, dummy_headers, response = self.app.request('GET', '/doc', environ=self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        HTMLValidator.validate(html)
        htmlExpected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Actions</title>
    <style type="text/css">
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
}
    </style>
  </head>
  <body class="chsl-index-body">
    <h1>localhost:8080</h1>
    <ul class="chsl-request-section">
      <li><span>Actions</span>
        <ul class="chsl-request-list">
          <li><a href="/doc?name=doc">doc</a></li>
          <li><a href="/doc?name=myAction1">myAction1</a></li>
          <li><a href="/doc?name=myAction2">myAction2</a></li>
        </ul>
      </li>
    </ul>
  </body>
</html>'''
        self.assertEqual(htmlExpected, html)

    # Test action model HTML generation
    def test_doc_DocAction_request(self):

        # Validate the first myAction1's HTML
        environ = dict(self._environ)
        environ['QUERY_STRING'] = 'name=myAction1'
        dummy_status, dummy_headers, response = self.app.request('GET', '/doc', environ=environ)
        html = response.decode('utf-8')
        HTMLValidator.validate(html)
        htmlExpected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>myAction1</title>
    <style type="text/css">
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
}
    </style>
  </head>
  <body class="chsl-request-body">
    <div class="chsl-header">
      <a href="/doc">Back to documentation index</a>
    </div>
    <h1>myAction1</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/myAction1">/myAction1</a></li>
        </ul>
      </div>
    </div>
    <h2 id="myAction1_Input"><a class="linktarget">Input Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td>struct</td>
        <td><a href="#MyStruct">MyStruct</a></td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>typedef</td>
        <td><a href="#MyTypedef">MyTypedef</a></td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(elem)</span> &gt; 0</li>
          </ul>
        </td>
      </tr>
    </table>
    <h2 id="myAction1_Output"><a class="linktarget">Output Parameters</a></h2>
    <div class="chsl-text">
      <p>
The action has no output parameters.
      </p>
    </div>
    <h2 id="myAction1_Error"><a class="linktarget">Error Codes</a></h2>
    <div class="chsl-text">
      <p>
The action returns no custom error codes.
      </p>
    </div>
    <h2>Typedefs</h2>
    <h3 id="MyTypedef"><a class="linktarget">typedef MyTypedef</a></h3>
    <div class="chsl-text">
      <p>
A typedef
      </p>
    </div>
    <table>
      <tr>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td><a href="#MyStruct">MyStruct</a>&nbsp;{}</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(dict)</span> &gt; 0</li>
            <li><span class="chsl-emphasis">len(key)</span> == 2</li>
          </ul>
        </td>
      </tr>
    </table>
    <h2>Struct Types</h2>
    <h3 id="MyStruct"><a class="linktarget">struct MyStruct</a></h3>
    <div class="chsl-text">
      <p>
My struct
- continuing
      </p>
      <p>
Another paragraph
      </p>
    </div>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
        <th>Description</th>
      </tr>
      <tr>
        <td>member1</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">value</span> &gt; 5</li>
          </ul>
        </td>
        <td>
          <div class="chsl-text">
            <p>
My int member
- continuing
            </p>
            <p>
Another paragraph
            </p>
          </div>
        </td>
      </tr>
      <tr>
        <td>member2</td>
        <td>float</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">value</span> &lt; 6.5</li>
          </ul>
        </td>
        <td>
          <div class="chsl-text">
            <p>
My float member
            </p>
          </div>
        </td>
      </tr>
      <tr>
        <td>member3</td>
        <td>bool</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member4</td>
        <td>string</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(value)</span> &gt; 0</li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member5</td>
        <td>datetime</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member6</td>
        <td><a href="#MyEnum">MyEnum</a></td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member7</td>
        <td><a href="#MyStruct">MyStruct</a></td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member8</td>
        <td><a href="#MyEnum">MyEnum</a>&nbsp;[]</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(array)</span> &gt; 0</li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member9</td>
        <td><a href="#MyStruct">MyStruct</a>&nbsp;{}</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member10</td>
        <td><a href="#MyEnum">MyEnum</a>&nbsp;:&nbsp;<a href="#MyStruct">MyStruct</a>&nbsp;{}</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(dict)</span> &gt; 0</li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member11</td>
        <td>int&nbsp;{}</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(dict)</span> &gt; 0</li>
            <li><span class="chsl-emphasis">len(key)</span> == 2</li>
            <li><span class="chsl-emphasis">elem</span> &gt; 5</li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
      <tr>
        <td>member12</td>
        <td>date</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
        <td>
        </td>
      </tr>
    </table>
    <h2>Enum Types</h2>
    <h3 id="MyEnum"><a class="linktarget">enum MyEnum</a></h3>
    <div class="chsl-text">
      <p>
My enum
      </p>
    </div>
    <table>
      <tr>
        <th>Value</th>
        <th>Description</th>
      </tr>
      <tr>
        <td>Value1</td>
        <td>
          <div class="chsl-text">
            <p>
A value
            </p>
          </div>
        </td>
      </tr>
      <tr>
        <td>Value2</td>
        <td>
        </td>
      </tr>
    </table>
  </body>
</html>'''
        self.assertEqual(htmlExpected, html)

        # Validate the myAction2's HTML
        environ = dict(self._environ2)
        environ['QUERY_STRING'] = 'name=myAction2'
        dummy_status, dummy_headers, response = self.app.request('GET', '/doc', environ=environ)
        html = response.decode('utf-8')
        HTMLValidator.validate(html)
        htmlExpected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>myAction2</title>
    <style type="text/css">
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
}
    </style>
  </head>
  <body class="chsl-request-body">
    <div class="chsl-header">
      <a href="/doc">Back to documentation index</a>
    </div>
    <h1>myAction2</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/myAction2">/myAction2</a></li>
        </ul>
      </div>
    </div>
    <h2 id="myAction2_Input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
      <p>
The action has no input parameters.
      </p>
    </div>
    <h2 id="myAction2_Output"><a class="linktarget">Output Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td>union</td>
        <td><a href="#MyUnion">MyUnion</a></td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
      </tr>
    </table>
    <h2 id="myAction2_Error"><a class="linktarget">Error Codes</a></h2>
    <table>
      <tr>
        <th>Value</th>
      </tr>
      <tr>
        <td>MyError1</td>
      </tr>
      <tr>
        <td>MyError2</td>
      </tr>
    </table>
    <h2>Struct Types</h2>
    <h3 id="MyUnion"><a class="linktarget">union MyUnion</a></h3>
    <div class="chsl-text">
      <p>
An unused struct
My Union
      </p>
    </div>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td>a</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">optional</span></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>b</td>
        <td>string</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">optional</span></li>
          </ul>
        </td>
      </tr>
    </table>
  </body>
</html>'''
        self.assertEqual(htmlExpected, html)

    # Test doc generation element class
    def test_doc_element(self):

        root = Element('a')
        b = root.addChild('b')
        b.addChild('Hello!', isInline=True, isText=True)
        b.addChild('span', isInline=True).addChild(' There!', isText=True)
        root.addChild('c', isClosed=False, foo='bar')
        root.addChild('d', attr1='asdf', _attr2='sdfg').addChild('e')

        chunks = [
            '<!doctype html>\n',
            '<a',
            '>',
            '\n',
            '  ',
            '<b',
            '>',
            'Hello!',
            '<span',
            '>',
            ' There!',
            '</span>',
            '</b>',
            '\n',
            '  ',
            '<c',
            ' foo="bar"',
            '>',
            '\n',
            '  ',
            '<d',
            ' attr1="asdf"',
            ' attr2="sdfg"',
            '>',
            '\n',
            '    ',
            '<e',
            '>',
            '\n    ',
            '</e>',
            '\n  ',
            '</d>',
            '\n',
            '</a>'
        ]
        self.assertEqual(list(root.serialize_chunks()), chunks)
        self.assertEqual(root.serialize(), ''.join(chunks))

    # Test doc generation element class - no indent
    def test_doc_element_noindent(self):

        root = Element('a')
        b = root.addChild('b')
        b.addChild('Hello!', isInline=True, isText=True)
        b.addChild('span', isInline=True).addChild(' There!', isText=True)
        root.addChild('c', isClosed=False, foo='bar')
        root.addChild('d', attr1='asdf', _attr2='sdfg').addChild('e')

        chunks = [
            '<!doctype html>\n',
            '<a',
            '>',
            '\n',
            '',
            '<b',
            '>',
            'Hello!',
            '<span',
            '>',
            ' There!',
            '</span>',
            '</b>',
            '\n',
            '',
            '<c',
            ' foo="bar"',
            '>',
            '\n',
            '',
            '<d',
            ' attr1="asdf"',
            ' attr2="sdfg"',
            '>',
            '\n',
            '',
            '<e',
            '>',
            '\n',
            '</e>',
            '\n',
            '</d>',
            '\n',
            '</a>'
        ]
        self.assertEqual(list(root.serialize_chunks(indent='')), chunks)
        self.assertEqual(root.serialize(indent=''), ''.join(chunks))

    def test_doc_page(self):

        app = chisel.Application()

        @chisel.action(spec='''\
action myAction
    input
        int a
        int b
    output
        int c
''')
        def myAction(dummy_ctx, req):
            return {'c': req['a'] + req['b']}

        app.addRequest(chisel.DocAction())
        app.addRequest(chisel.DocPage(myAction))

        status, dummy_headers, response = app.request('GET', '/doc', environ=self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        HTMLValidator.validate(html)
        htmlExpected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Actions</title>
    <style type="text/css">
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
}
    </style>
  </head>
  <body class="chsl-index-body">
    <h1>localhost:8080</h1>
    <ul class="chsl-request-section">
      <li><span>Actions</span>
        <ul class="chsl-request-list">
          <li><a href="/doc?name=doc">doc</a></li>
          <li><a href="/doc?name=doc_action_myAction">doc_action_myAction</a></li>
        </ul>
      </li>
    </ul>
  </body>
</html>'''
        self.assertEqual(htmlExpected, html)

        environ = dict(self._environ)
        environ['QUERY_STRING'] = 'name=doc_action_myAction'
        status, dummy_headers, response = app.request('GET', '/doc', environ=environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        HTMLValidator.validate(html)
        htmlExpected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>doc_action_myAction</title>
    <style type="text/css">
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
}
    </style>
  </head>
  <body class="chsl-request-body">
    <div class="chsl-header">
      <a href="/doc">Back to documentation index</a>
    </div>
    <h1>doc_action_myAction</h1>
    <div class="chsl-text">
      <p>
Documentation page for action myAction.
      </p>
    </div>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/doc/action/myAction">/doc/action/myAction</a></li>
        </ul>
      </div>
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The action has a non-default response. See documentation for details.
        </p>
      </div>
    </div>
    <h2 id="doc_action_myAction_Input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
      <p>
The action has no input parameters.
      </p>
    </div>
  </body>
</html>'''
        self.assertEqual(htmlExpected, html)

        status, dummy_headers, response = app.request('GET', '/doc/action/myAction', environ=self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        HTMLValidator.validate(html)
        htmlExpected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>myAction</title>
    <style type="text/css">
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
}
    </style>
  </head>
  <body class="chsl-request-body">
    <h1>myAction</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/myAction">/myAction</a></li>
        </ul>
      </div>
    </div>
    <h2 id="myAction_Input"><a class="linktarget">Input Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td>a</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>b</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
      </tr>
    </table>
    <h2 id="myAction_Output"><a class="linktarget">Output Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td>c</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">none</span></li>
          </ul>
        </td>
      </tr>
    </table>
    <h2 id="myAction_Error"><a class="linktarget">Error Codes</a></h2>
    <div class="chsl-text">
      <p>
The action returns no custom error codes.
      </p>
    </div>
  </body>
</html>'''
        self.assertEqual(htmlExpected, html)
