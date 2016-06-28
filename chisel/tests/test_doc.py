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

import unittest

from chisel import action, request, Action, Application, DocAction, DocPage, Element


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
    optional int(> 5) member1

    # My float member
    nullable float(< 6.5) member2

    optional nullable bool member3
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

action my_action1
    input
        MyStruct struct
        MyTypedef typedef

action my_action2
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
        self.app = Application()
        self.app.pretty_output = True
        self.app.specs.parse_string(self._spec)
        self.app.add_request(Action(lambda app, req: {}, name='my_action1'))
        self.app.add_request(Action(lambda app, req: {}, name='my_action2'))
        self.app.add_request(DocAction())

    # Test documentation index HTML generation
    def test_index(self):

        # Validate the HTML
        status, dummy_headers, response = self.app.request('GET', '/doc', environ=self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        html_expected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>localhost:8080</title>
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
    <ul class="chsl-request-list">
      <li><a href="/doc?name=doc">doc</a></li>
      <li><a href="/doc?name=my_action1">my_action1</a></li>
      <li><a href="/doc?name=my_action2">my_action2</a></li>
    </ul>
  </body>
</html>'''
        self.assertEqual(html_expected, html)

    # Test action model HTML generation
    def test_action(self):

        # Validate the first my_action1's HTML
        environ = dict(self._environ)
        environ['QUERY_STRING'] = 'name=my_action1'
        status, dummy_headers, response = self.app.request('GET', '/doc', environ=environ)
        self.assertEqual(status, '200 OK')
        html = response.decode('utf-8')
        html_expected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action1</title>
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
    <h1>my_action1</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URLs:
        </p>
        <ul>
          <li><a href="/my_action1">GET /my_action1</a></li>
          <li><a href="/my_action1">POST /my_action1</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action1_input"><a class="linktarget">Input Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td>struct</td>
        <td><a href="#MyStruct">MyStruct</a></td>
        <td />
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
    <h2 id="my_action1_output"><a class="linktarget">Output Parameters</a></h2>
    <div class="chsl-text">
      <p>
The action has no output parameters.
      </p>
    </div>
    <h2 id="my_action1_error"><a class="linktarget">Error Codes</a></h2>
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
            <li><span class="chsl-emphasis">optional</span></li>
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
            <li><span class="chsl-emphasis">nullable</span></li>
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
            <li><span class="chsl-emphasis">optional</span></li>
            <li><span class="chsl-emphasis">nullable</span></li>
          </ul>
        </td>
        <td />
      </tr>
      <tr>
        <td>member4</td>
        <td>string</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(value)</span> &gt; 0</li>
          </ul>
        </td>
        <td />
      </tr>
      <tr>
        <td>member5</td>
        <td>datetime</td>
        <td />
        <td />
      </tr>
      <tr>
        <td>member6</td>
        <td><a href="#MyEnum">MyEnum</a></td>
        <td />
        <td />
      </tr>
      <tr>
        <td>member7</td>
        <td><a href="#MyStruct">MyStruct</a></td>
        <td />
        <td />
      </tr>
      <tr>
        <td>member8</td>
        <td><a href="#MyEnum">MyEnum</a>&nbsp;[]</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(array)</span> &gt; 0</li>
          </ul>
        </td>
        <td />
      </tr>
      <tr>
        <td>member9</td>
        <td><a href="#MyStruct">MyStruct</a>&nbsp;{}</td>
        <td />
        <td />
      </tr>
      <tr>
        <td>member10</td>
        <td><a href="#MyEnum">MyEnum</a>&nbsp;:&nbsp;<a href="#MyStruct">MyStruct</a>&nbsp;{}</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(dict)</span> &gt; 0</li>
          </ul>
        </td>
        <td />
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
        <td />
      </tr>
      <tr>
        <td>member12</td>
        <td>date</td>
        <td />
        <td />
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
        <td />
      </tr>
    </table>
  </body>
</html>'''
        self.assertEqual(html_expected, html)

        # Validate the my_action2's HTML
        environ = dict(self._environ2)
        environ['QUERY_STRING'] = 'name=my_action2'
        status, dummy_headers, response = self.app.request('GET', '/doc', environ=environ)
        self.assertEqual(status, '200 OK')
        html = response.decode('utf-8')
        html_expected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action2</title>
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
    <h1>my_action2</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URLs:
        </p>
        <ul>
          <li><a href="/my_action2">GET /my_action2</a></li>
          <li><a href="/my_action2">POST /my_action2</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action2_input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
      <p>
The action has no input parameters.
      </p>
    </div>
    <h2 id="my_action2_output"><a class="linktarget">Output Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
      </tr>
      <tr>
        <td>union</td>
        <td><a href="#MyUnion">MyUnion</a></td>
      </tr>
    </table>
    <h2 id="my_action2_error"><a class="linktarget">Error Codes</a></h2>
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
        self.assertEqual(html_expected, html)

    def test_request(self):

        @request(doc='''
This is the request documentation.

And some other important information.
''')
        def my_request(dummy_environ, dummy_start_response):
            pass
        application = Application()
        application.add_request(DocAction())
        application.add_request(my_request)

        status, dummy_headers, response = application.request('GET', '/doc', query_string='name=my_request')
        self.assertEqual(status, '200 OK')
        html = response.decode('utf-8')
        html_expected = '''\
<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<title>my_request</title>
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
<h1>my_request</h1>
<div class="chsl-text">
<p>
This is the request documentation.
</p>
<p>
And some other important information.
</p>
</div>
<div class="chsl-notes">
<div class="chsl-note">
<p>
<b>Note: </b>
The request is exposed at the following URL:
</p>
<ul>
<li><a href="/my_request">/my_request</a></li>
</ul>
</div>
</div>
</body>
</html>'''
        self.assertEqual(html_expected, html)

    def test_request_not_found(self):

        @request(doc='''
This is the request documentation.
''')
        def my_request(dummy_environ, dummy_start_response):
            pass
        application = Application()
        application.add_request(DocAction())
        application.add_request(my_request)

        status, dummy_headers, response = application.request('GET', '/doc', query_string='name=my_unknown_request')
        self.assertEqual(status, '404 Not Found')
        self.assertEqual(response, b'Unknown Request')

    # Test doc generation element class
    def test_element(self):

        root = Element('a', children=[
            Element('b', inline=True, children=[
                Element('Hello!', text=True),
                Element('span', children=Element(' There!', text=True))
            ]),
            Element('c', closed=False, foo='bar'),
            Element('d', attr1='asdf', _attr2='sdfg', children=Element('e'))
        ])

        chunks = [
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
            ' />',
            '\n  ',
            '</d>',
            '\n',
            '</a>'
        ]
        self.assertEqual(list(root.serialize_chunks()), chunks)
        self.assertEqual(root.serialize(), '<!doctype html>\n' + ''.join(chunks))
        self.assertEqual(root.serialize(html=False), ''.join(chunks))

    def test_element_indent_empty(self):

        root = Element('a', children=[
            Element('b', inline=True, children=[
                Element('Hello!', text=True),
                Element('span', children=Element(' There!', text=True))
            ]),
            Element('c', closed=False, foo='bar'),
            Element('d', attr1='asdf', _attr2='sdfg', children=Element('e'))
        ])

        chunks = list(root.serialize_chunks(indent=''))
        expected_chunks = [
            '<a',
            '>',
            '\n',
            '<b',
            '>',
            'Hello!',
            '<span',
            '>',
            ' There!',
            '</span>',
            '</b>',
            '\n',
            '<c',
            ' foo="bar"',
            '>',
            '\n',
            '<d',
            ' attr1="asdf"',
            ' attr2="sdfg"',
            '>',
            '\n',
            '<e',
            ' />',
            '\n',
            '</d>',
            '\n',
            '</a>'
        ]
        self.assertEqual(chunks, expected_chunks)
        self.assertEqual(root.serialize(indent=''), '<!doctype html>\n' + ''.join(expected_chunks))
        self.assertEqual(root.serialize(indent='', html=False), ''.join(expected_chunks))

    def test_element_indent_none(self):

        root = Element('a', children=[
            Element('b', inline=True, children=[
                Element('Hello!', text=True),
                Element('span', children=Element(' There!', text=True))
            ]),
            Element('c', closed=False, foo='bar'),
            Element('d', attr1='asdf', _attr2='sdfg', children=Element('e'))
        ])

        chunks = list(root.serialize_chunks(indent=None))
        expected_chunks = [
            '<a',
            '>',
            '<b',
            '>',
            'Hello!',
            '<span',
            '>',
            ' There!',
            '</span>',
            '</b>',
            '<c',
            ' foo="bar"',
            '>',
            '<d',
            ' attr1="asdf"',
            ' attr2="sdfg"',
            '>',
            '<e',
            ' />',
            '</d>',
            '</a>'
        ]
        self.assertEqual(chunks, expected_chunks)
        self.assertEqual(root.serialize(indent=None), '<!doctype html>\n' + ''.join(expected_chunks))
        self.assertEqual(root.serialize(indent=None, html=False), ''.join(expected_chunks))

    def test_page(self):

        app = Application()
        app.pretty_output = True

        @action(spec='''\
action my_action
    input
        int a
        int b
    output
        int c
''')
        def my_action(dummy_ctx, req):
            return {'c': req['a'] + req['b']}

        app.add_request(DocAction())
        app.add_request(DocPage(my_action))

        status, dummy_headers, response = app.request('GET', '/doc', environ=self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        html_expected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>localhost:8080</title>
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
    <ul class="chsl-request-list">
      <li><a href="/doc?name=doc">doc</a></li>
      <li><a href="/doc?name=doc_my_action">doc_my_action</a></li>
    </ul>
  </body>
</html>'''
        self.assertEqual(html_expected, html)

        environ = dict(self._environ)
        environ['QUERY_STRING'] = 'name=doc_my_action'
        status, dummy_headers, response = app.request('GET', '/doc', environ=environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        html_expected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>doc_my_action</title>
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
    <h1>doc_my_action</h1>
    <div class="chsl-text">
      <p>
Documentation page for my_action.
      </p>
    </div>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/doc_my_action">GET /doc_my_action</a></li>
        </ul>
      </div>
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The action has a non-default response. See documentation for details.
        </p>
      </div>
    </div>
    <h2 id="doc_my_action_input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
      <p>
The action has no input parameters.
      </p>
    </div>
  </body>
</html>'''
        self.assertEqual(html_expected, html)

        status, dummy_headers, response = app.request('GET', '/doc_my_action', environ=self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        html_expected = '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action</title>
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
    <h1>my_action</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URLs:
        </p>
        <ul>
          <li><a href="/my_action">GET /my_action</a></li>
          <li><a href="/my_action">POST /my_action</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action_input"><a class="linktarget">Input Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
      </tr>
      <tr>
        <td>a</td>
        <td>int</td>
      </tr>
      <tr>
        <td>b</td>
        <td>int</td>
      </tr>
    </table>
    <h2 id="my_action_output"><a class="linktarget">Output Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
      </tr>
      <tr>
        <td>c</td>
        <td>int</td>
      </tr>
    </table>
    <h2 id="my_action_error"><a class="linktarget">Error Codes</a></h2>
    <div class="chsl-text">
      <p>
The action returns no custom error codes.
      </p>
    </div>
  </body>
</html>'''
        self.assertEqual(html_expected, html)
