# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

from chisel import action, request, Action, Application, DocAction, DocPage, Request, SpecParser
import chisel.doc

from . import TestCase


class TestSimpleMarkdown(TestCase):

    def test_basic(self):
        markdown = chisel.doc.SimpleMarkdown()
        self.assertEqual(
            markdown('''\
P1.
P1 2.

P2.


P3
''' + '  P3 2.  ' + '''
P3 3.

P4
'''),
            '''\
<p>
P1.
P1 2.
</p>
<p>
P2.
</p>
<p>
P3
P3 2.
P3 3.
</p>
<p>
P4
</p>''')

    def test_new_paragraph(self):
        markdown = chisel.doc.SimpleMarkdown()
        self.assertEqual(
            markdown('''\
# h1
## h2
* list1
+ list2
- list3

- list4
1. list5
2. list6
'''),
            '''\
<p>
# h1
</p>
<p>
## h2
</p>
<p>
* list1
</p>
<p>
+ list2
</p>
<p>
- list3
</p>
<p>
- list4
</p>
<p>
1. list5
</p>
<p>
2. list6
</p>'''
        )

    def test_empty(self):
        markdown = chisel.doc.SimpleMarkdown()
        self.assertEqual(
            markdown('   '),
            ''
        )


class TestDoc(TestCase):

    def setUp(self):

        spec_parser = SpecParser('''\
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
''')
        self.app = Application()
        self.app.pretty_output = True
        self.app.add_request(Action(None, name='my_action1', spec_parser=spec_parser))
        self.app.add_request(Action(None, name='my_action2', spec_parser=spec_parser))
        self.app.add_request(DocAction())

    def test_index(self):

        # Validate the HTML
        status, _, response = self.app.request('GET', '/doc')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>localhost:80</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-index-body">
    <h1>localhost:80</h1>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=doc">doc</a></li>
      <li><a href="/doc?name=my_action1">my_action1</a></li>
      <li><a href="/doc?name=my_action2">my_action2</a></li>
    </ul>
  </body>
</html>''')

    def test_doc_group(self):

        spec_parser = SpecParser('''\
action my_action1

group "My  Group   1"

action my_action2

group "My Group 1"

action my_action3

group "My Group 2"

action my_action4

group

action my_action5
''')
        app = Application()
        app.pretty_output = True
        app.add_request(DocAction())
        app.add_request(Action(None, name='my_action1', spec_parser=spec_parser))
        app.add_request(Action(None, name='my_action2', spec_parser=spec_parser))
        app.add_request(Action(None, name='my_action3', spec_parser=spec_parser))
        app.add_request(Action(None, name='my_action4', spec_parser=spec_parser))
        app.add_request(Action(None, name='my_action5', spec_parser=spec_parser))
        app.add_request(Request(None, name='my_request1'))
        app.add_request(Request(None, name='my_request2', doc_group='My  Group   2'))

        status, _, response = app.request('GET', '/doc')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>localhost:80</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-index-body">
    <h1>localhost:80</h1>
    <h2>My  Group   1</h2>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=my_action2">my_action2</a></li>
    </ul>
    <h2>My  Group   2</h2>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=my_request2">my_request2</a></li>
    </ul>
    <h2>My Group 1</h2>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=my_action3">my_action3</a></li>
    </ul>
    <h2>My Group 2</h2>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=my_action4">my_action4</a></li>
    </ul>
    <h2>Uncategorized</h2>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=doc">doc</a></li>
      <li><a href="/doc?name=my_action1">my_action1</a></li>
      <li><a href="/doc?name=my_action5">my_action5</a></li>
      <li><a href="/doc?name=my_request1">my_request1</a></li>
    </ul>
  </body>
</html>''')

    def test_action(self):

        # Validate the first my_action1's HTML
        status, _, response = self.app.request('GET', '/doc', query_string={'name': 'my_action1'})
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action1</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
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
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/my_action1">POST /my_action1</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action1_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no path parameters.</p>
    </div>
    <h2 id="my_action1_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no query parameters.</p>
    </div>
    <h2 id="my_action1_input"><a class="linktarget">Input Parameters</a></h2>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
      </tr>
      <tr>
        <td>struct</td>
        <td><a href="#MyStruct">MyStruct</a></td>
      </tr>
      <tr>
        <td>typedef</td>
        <td><a href="#MyTypedef">MyTypedef</a></td>
      </tr>
    </table>
    <h2 id="my_action1_output"><a class="linktarget">Output Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no output parameters.</p>
    </div>
    <h2 id="my_action1_error"><a class="linktarget">Error Codes</a></h2>
    <div class="chsl-text">
<p>The action returns no custom error codes.</p>
    </div>
    <h2>Typedefs</h2>
    <h3 id="MyTypedef"><a class="linktarget">typedef MyTypedef</a></h3>
    <div class="chsl-text">
<p>A typedef</p>
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
<p>My struct</p>
<ul>
<li>continuing</li>
</ul>
<p>Another paragraph</p>
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
<p>My int member</p>
<ul>
<li>continuing</li>
</ul>
<p>Another paragraph</p>
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
<p>My float member</p>
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
<p>My enum</p>
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
<p>A value</p>
          </div>
        </td>
      </tr>
      <tr>
        <td>Value2</td>
        <td />
      </tr>
    </table>
  </body>
</html>''')

        # Validate the my_action2's HTML
        status, _, response = self.app.request('GET', '/doc', query_string={'name': 'my_action2'})
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action2</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
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
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/my_action2">POST /my_action2</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action2_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no path parameters.</p>
    </div>
    <h2 id="my_action2_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no query parameters.</p>
    </div>
    <h2 id="my_action2_input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no input parameters.</p>
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
<p>An unused struct
 My Union</p>
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
</html>''')

    def test_action_no_markdown(self):

        @action(spec='''\
# This is an action. It does:
#
# - One thing
#
#
# - Another thing
action my_action
''')
        def my_action(unused_ctx, unused_req):
            pass # pragma: no cover
        @action(doc='Another action', spec='''\
action my_action2
''')
        def my_action2(unused_ctx, unused_req):
            pass # pragma: no cover
        application = Application()
        application.pretty_output = True
        application.add_request(DocAction())
        application.add_request(my_action)
        application.add_request(my_action2)

        # Generate the docs without markdown
        try:
            chisel_doc_markdown = chisel.doc.MARKDOWN
            chisel.doc.MARKDOWN = chisel.doc.SimpleMarkdown()
            status, _, response = application.request('GET', '/doc', query_string={'name': 'my_action'})
            application.pretty_output = False
            status2, _, response2 = application.request('GET', '/doc', query_string={'name': 'my_action2'})
        finally:
            chisel.doc.MARKDOWN = chisel_doc_markdown

        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <div class="chsl-header">
      <a href="/doc">Back to documentation index</a>
    </div>
    <h1>my_action</h1>
    <div class="chsl-text">
<p>
This is an action. It does:
</p>
<p>
- One thing
</p>
<p>
- Another thing
</p>
    </div>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/my_action">POST /my_action</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>
The action has no path parameters.
</p>
    </div>
    <h2 id="my_action_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>
The action has no query parameters.
</p>
    </div>
    <h2 id="my_action_input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
<p>
The action has no input parameters.
</p>
    </div>
    <h2 id="my_action_output"><a class="linktarget">Output Parameters</a></h2>
    <div class="chsl-text">
<p>
The action has no output parameters.
</p>
    </div>
    <h2 id="my_action_error"><a class="linktarget">Error Codes</a></h2>
    <div class="chsl-text">
<p>
The action returns no custom error codes.
</p>
    </div>
  </body>
</html>''')

        self.assertEqual(status2, '200 OK')
        self.assertEqual(response2.decode('utf-8'), '''\
<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<title>my_action2</title>
<style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
</style>
</head>
<body class="chsl-request-body">
<div class="chsl-header">
<a href="/doc">Back to documentation index</a>
</div>
<h1>my_action2</h1>
<div class="chsl-text">
<p>
Another action
</p>
</div>
<div class="chsl-notes">
<div class="chsl-note">
<p>
<b>Note: </b>
The request is exposed at the following URL:
</p>
<ul>
<li><a href="/my_action2">POST /my_action2</a></li>
</ul>
</div>
</div>
<h2 id="my_action2_path"><a class="linktarget">Path Parameters</a></h2>
<div class="chsl-text">
<p>
The action has no path parameters.
</p>
</div>
<h2 id="my_action2_query"><a class="linktarget">Query Parameters</a></h2>
<div class="chsl-text">
<p>
The action has no query parameters.
</p>
</div>
<h2 id="my_action2_input"><a class="linktarget">Input Parameters</a></h2>
<div class="chsl-text">
<p>
The action has no input parameters.
</p>
</div>
<h2 id="my_action2_output"><a class="linktarget">Output Parameters</a></h2>
<div class="chsl-text">
<p>
The action has no output parameters.
</p>
</div>
<h2 id="my_action2_error"><a class="linktarget">Error Codes</a></h2>
<div class="chsl-text">
<p>
The action returns no custom error codes.
</p>
</div>
</body>
</html>''')

    def test_member_attributes(self):

        spec_parser = SpecParser('''\
struct MyStruct
    int (> 5, < 10) a
    int (>= 5, <= 10) b
    int (== 5) c
    string (len > 5, len < 10) d
    string (len >= 5, len <= 10) e
    string (len == 5) f
''')
        app = Application()
        app.pretty_output = True
        app.add_request(DocPage(spec_parser.types['MyStruct']))

        status, _, response = app.request('GET', '/doc_MyStruct')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>MyStruct</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1 id="MyStruct"><a class="linktarget">struct MyStruct</a></h1>
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
            <li><span class="chsl-emphasis">value</span> &gt; 5</li>
            <li><span class="chsl-emphasis">value</span> &lt; 10</li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>b</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">value</span> &gt;= 5</li>
            <li><span class="chsl-emphasis">value</span> &lt;= 10</li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>c</td>
        <td>int</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">value</span> == 5</li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>d</td>
        <td>string</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(value)</span> &gt; 5</li>
            <li><span class="chsl-emphasis">len(value)</span> &lt; 10</li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>e</td>
        <td>string</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(value)</span> &gt;= 5</li>
            <li><span class="chsl-emphasis">len(value)</span> &lt;= 10</li>
          </ul>
        </td>
      </tr>
      <tr>
        <td>f</td>
        <td>string</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(value)</span> == 5</li>
          </ul>
        </td>
      </tr>
    </table>
    <div class="chsl-notes" />
  </body>
</html>''')

    def test_request(self):

        @request(doc='''
This is the request documentation.

And some other important information.
''')
        def my_request(unused_environ, unused_start_response):
            pass # pragma: no cover
        application = Application()
        application.add_request(DocAction())
        application.add_request(my_request)

        status, _, response = application.request('GET', '/doc', query_string='name=my_request')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<title>my_request</title>
<style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
</style>
</head>
<body class="chsl-request-body">
<div class="chsl-header">
<a href="/doc">Back to documentation index</a>
</div>
<h1>my_request</h1>
<div class="chsl-text">
<p>This is the request documentation.</p>
<p>And some other important information.</p>
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
</html>''')

    def test_request_not_found(self):

        @request(doc='''
This is the request documentation.
''')
        def my_request(unused_environ, unused_start_response):
            pass # pragma: no cover
        application = Application()
        application.add_request(DocAction())
        application.add_request(my_request)

        status, _, response = application.request('GET', '/doc', query_string='name=my_unknown_request')
        self.assertEqual(status, '404 Not Found')
        self.assertEqual(response, b'Unknown Request')

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
        def my_action(unused_ctx, unused_req):
            pass # pragma: no cover

        app.add_request(DocAction())
        app.add_request(DocPage(my_action))
        app.add_request(DocPage(my_action, name='my_action_docs'))

        status, _, response = app.request('GET', '/doc')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>localhost:80</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-index-body">
    <h1>localhost:80</h1>
    <ul class="chsl-request-list">
      <li><a href="/doc?name=doc">doc</a></li>
      <li><a href="/doc?name=doc_my_action">doc_my_action</a></li>
      <li><a href="/doc?name=my_action_docs">my_action_docs</a></li>
    </ul>
  </body>
</html>''')

        status, _, response = app.request('GET', '/doc', query_string={'name': 'doc_my_action'})
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>doc_my_action</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <div class="chsl-header">
      <a href="/doc">Back to documentation index</a>
    </div>
    <h1>doc_my_action</h1>
    <div class="chsl-text">
<p>Documentation page for my_action.</p>
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
    <h2 id="doc_my_action_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no path parameters.</p>
    </div>
    <h2 id="doc_my_action_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no query parameters.</p>
    </div>
    <h2 id="doc_my_action_input"><a class="linktarget">Input Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no input parameters.</p>
    </div>
  </body>
</html>''')

        status, _, response = app.request('GET', '/doc_my_action')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1>my_action</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/my_action">POST /my_action</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no path parameters.</p>
    </div>
    <h2 id="my_action_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no query parameters.</p>
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
<p>The action returns no custom error codes.</p>
    </div>
  </body>
</html>''')

        status, _, response = app.request('GET', '/my_action_docs')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1>my_action</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="/my_action">POST /my_action</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no path parameters.</p>
    </div>
    <h2 id="my_action_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no query parameters.</p>
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
<p>The action returns no custom error codes.</p>
    </div>
  </body>
</html>''')

    def test_page_urls(self):

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
        def my_action(unused_ctx, unused_req):
            pass # pragma: no cover

        app.add_request(DocPage(my_action, request_urls=[('GET', 'https://foo.com/my_action')]))

        status, _, response = app.request('GET', '/doc_my_action')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>my_action</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1>my_action</h1>
    <div class="chsl-notes">
      <div class="chsl-note">
        <p>
          <b>Note: </b>
The request is exposed at the following URL:
        </p>
        <ul>
          <li><a href="https://foo.com/my_action">GET https://foo.com/my_action</a></li>
        </ul>
      </div>
    </div>
    <h2 id="my_action_path"><a class="linktarget">Path Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no path parameters.</p>
    </div>
    <h2 id="my_action_query"><a class="linktarget">Query Parameters</a></h2>
    <div class="chsl-text">
<p>The action has no query parameters.</p>
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
<p>The action returns no custom error codes.</p>
    </div>
  </body>
</html>''')

    def test_page_struct(self):

        parser = SpecParser('''\
# This is my struct
struct MyStruct
    int a
    string b
    MyOtherStruct c

# This is my other struct
struct MyOtherStruct
    int x
    int y
''')
        app = Application()
        app.pretty_output = True
        app.add_request(DocAction())
        app.add_request(DocPage(parser.types['MyStruct']))

        status, _, response = app.request('GET', '/doc_MyStruct')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>MyStruct</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1 id="MyStruct"><a class="linktarget">struct MyStruct</a></h1>
    <div class="chsl-text">
<p>This is my struct</p>
    </div>
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
        <td>string</td>
      </tr>
      <tr>
        <td>c</td>
        <td><a href="#MyOtherStruct">MyOtherStruct</a></td>
      </tr>
    </table>
    <div class="chsl-notes" />
    <h2>Struct Types</h2>
    <h3 id="MyOtherStruct"><a class="linktarget">struct MyOtherStruct</a></h3>
    <div class="chsl-text">
<p>This is my other struct</p>
    </div>
    <table>
      <tr>
        <th>Name</th>
        <th>Type</th>
      </tr>
      <tr>
        <td>x</td>
        <td>int</td>
      </tr>
      <tr>
        <td>y</td>
        <td>int</td>
      </tr>
    </table>
  </body>
</html>''')

    def test_page_typedef(self):

        parser = SpecParser('''\
# This is my struct
struct MyStruct
    int a
    string b

# This is my typedef
typedef MyStruct[len > 1] MyTypedef
''')
        app = Application()
        app.pretty_output = True
        app.add_request(DocAction())
        app.add_request(DocPage(parser.types['MyTypedef']))

        status, _, response = app.request('GET', '/doc_MyTypedef')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>MyTypedef</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1 id="MyTypedef"><a class="linktarget">typedef MyTypedef</a></h1>
    <div class="chsl-text">
<p>This is my typedef</p>
    </div>
    <table>
      <tr>
        <th>Type</th>
        <th>Attributes</th>
      </tr>
      <tr>
        <td><a href="#MyStruct">MyStruct</a>&nbsp;[]</td>
        <td>
          <ul class="chsl-constraint-list">
            <li><span class="chsl-emphasis">len(array)</span> &gt; 1</li>
          </ul>
        </td>
      </tr>
    </table>
    <div class="chsl-notes" />
    <h2>Struct Types</h2>
    <h3 id="MyStruct"><a class="linktarget">struct MyStruct</a></h3>
    <div class="chsl-text">
<p>This is my struct</p>
    </div>
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
        <td>string</td>
      </tr>
    </table>
  </body>
</html>''')

    def test_page_enum(self):

        parser = SpecParser('''\
# This is my enum
enum MyEnum
    A
    B
''')
        app = Application()
        app.pretty_output = True
        app.add_request(DocAction())
        app.add_request(DocPage(parser.types['MyEnum']))

        status, _, response = app.request('GET', '/doc_MyEnum')
        self.assertEqual(status, '200 OK')
        self.assertEqual(response.decode('utf-8'), '''\
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>MyEnum</title>
    <style type="text/css">
''' + chisel.doc.STYLE_TEXT + '''
    </style>
  </head>
  <body class="chsl-request-body">
    <h1 id="MyEnum"><a class="linktarget">enum MyEnum</a></h1>
    <div class="chsl-text">
<p>This is my enum</p>
    </div>
    <table>
      <tr>
        <th>Value</th>
      </tr>
      <tr>
        <td>A</td>
      </tr>
      <tr>
        <td>B</td>
      </tr>
    </table>
    <div class="chsl-notes" />
  </body>
</html>''')
