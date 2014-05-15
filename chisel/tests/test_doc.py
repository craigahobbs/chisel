#
# Copyright (C) 2012-2014 Craig Hobbs
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
from chisel.compat import HTMLParser, StringIO
from chisel.doc import Element

import unittest


# Simple HTML validator class
class HTMLValidator(HTMLParser):

    def __init__(self):
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
    [> 5] int member1

    # My float member
    [< 6.5] float member2

    bool member3
    [len > 0] string member4
    datetime member5
    MyEnum member6
    MyStruct member7
    MyEnum[] member8
    MyStruct{} member9

# An unused struct
# My Union
union MyUnion
    int a
    string b

action myAction1
    input
        MyStruct struct

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
        self.logStream = StringIO()
        self.app = chisel.Application(logStream = self.logStream)
        self.app.loadSpecString(self._spec)
        self.app.addRequest(chisel.Action(lambda app, req: {}, name = 'myAction1'))
        self.app.addRequest(chisel.Action(lambda app, req: {}, name = 'myAction2'))
        self.app.addDocRequest()

    # Test documentation index HTML generation
    def test_doc_DocAction_index(self):

        # Validate the HTML
        status, headers, response = self.app.request('GET', '/doc', environ = self._environ)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        HTMLValidator.validate(html)
        self.assertTrue('<h1>localhost:8080</h1>' in html)
        self.assertTrue('<li><a href="/doc?name=doc">doc</a></li>' in html)
        self.assertTrue('<li><a href="/doc?name=myAction1">myAction1</a></li>' in html)
        self.assertTrue('<li><a href="/doc?name=myAction2">myAction2</a></li>' in html)
        self.assertTrue('<style type="text/css">' in html)

        # Validate the HTML (custom CSS)
        status, headers, response = self.app.request('GET', '/doc', environ = self._environ2)
        html = response.decode('utf-8')
        self.assertEqual(status, '200 OK')
        HTMLValidator.validate(html)
        self.assertTrue('<h1>localhost:8080</h1>' in html)
        self.assertTrue('<li><a href="/doc?name=doc">doc</a></li>' in html)
        self.assertTrue('<li><a href="/doc?name=myAction1">myAction1</a></li>' in html)
        self.assertTrue('<li><a href="/doc?name=myAction2">myAction2</a></li>' in html)

    # Test action model HTML generation
    def test_doc_DocAction_request(self):

        # Validate the first myAction1's HTML
        environ = dict(self._environ)
        environ['QUERY_STRING'] = 'name=myAction1'
        status, headers, response = self.app.request('GET', '/doc', environ = environ)
        html = response.decode('utf-8')
        HTMLValidator.validate(html)
        self.assertTrue('<h1>myAction1</h1>' in html)
        self.assertTrue('<h2 id="myAction1_Input"><a class="linktarget">Input Parameters</a></h2>' in html)
        self.assertTrue('The action has no input parameters.' not in html)
        self.assertTrue('<h2 id="myAction1_Output"><a class="linktarget">Output Parameters</a></h2>' in html)
        self.assertTrue('The action has no output parameters.' in html)
        self.assertTrue('<h2 id="myAction1_Error"><a class="linktarget">Error Codes</a></h2>' in html)
        self.assertTrue('The action returns no custom error codes.' in html)
        self.assertTrue('<h2>Struct Types</h2>' in html)
        self.assertTrue('<h3 id="MyStruct"><a class="linktarget">struct MyStruct</a></h3>' in html)
        self.assertTrue('<li><span class="chsl-emphasis">value</span> &gt; 5</li>' in html)
        self.assertTrue('<li><span class="chsl-emphasis">value</span> &lt; 6.5</li>' in html)
        self.assertTrue('<li><span class="chsl-emphasis">len</span> &gt; 0</li>' in html)
        self.assertTrue('<h3 id="MyUnion"><a class="linktarget">union MyUnion</a></h3>' not in html)
        self.assertTrue('<h2>Enum Types</h2>' in html)
        self.assertTrue('<h3 id="MyEnum"><a class="linktarget">enum MyEnum</a></h3>' in html)
        self.assertTrue('<style type="text/css">' in html)

        # Validate the myAction2's HTML
        environ = dict(self._environ2)
        environ['QUERY_STRING'] = 'name=myAction2'
        status, headers, response = self.app.request('GET', '/doc', environ = environ)
        html = response.decode('utf-8')
        HTMLValidator.validate(html)
        self.assertTrue('<h1>myAction2</h1>' in html)
        self.assertTrue('<h2 id="myAction2_Input"><a class="linktarget">Input Parameters</a></h2>' in html)
        self.assertTrue('The action has no input parameters.' in html)
        self.assertTrue('<h2 id="myAction2_Output"><a class="linktarget">Output Parameters</a></h2>' in html)
        self.assertTrue('The action has no output parameters.' not in html)
        self.assertTrue('<h2 id="myAction2_Error"><a class="linktarget">Error Codes</a></h2>' in html)
        self.assertTrue('The action returns no custom error codes.' not in html)
        self.assertTrue('<h2>Struct Types</h2>' in html)
        self.assertTrue('<h3 id="MyStruct"><a class="linktarget">struct MyStruct</a></h3>' not in html)
        self.assertTrue('<h3 id="MyUnion"><a class="linktarget">union MyUnion</a></h3>' in html)
        self.assertTrue('<h2>Enum Types</h2>' not in html)
        self.assertTrue('<h3 id="MyEnum"><a class="linktarget">enum MyEnum</a></h3>' not in html)
        self.assertTrue('<style type="text/css">' in html)

    # Test doc generation element class
    def test_doc_element(self):

        # Test basic DOM element serialization functionality
        root = Element('a')
        b = root.addChild('b')
        b.addChild('Hello!', isInline = True, isText = True)
        b.addChild('span', isInline = True).addChild(' There!', isText = True)
        root.addChild('c', isClosed = False, foo = 'bar')
        root.addChild('d', attr1 = 'asdf', _attr2 = 'sdfg').addChild('e')

        # Default (indented)
        out = StringIO()
        root.serialize(out)
        self.assertEqual(out.getvalue(), '''\
<a>
  <b>Hello!<span> There!</span></b>
  <c foo="bar">
  <d attr1="asdf" attr2="sdfg">
    <e>
    </e>
  </d>
</a>''')

        # Not indented
        out = StringIO()
        root.serialize(out, indent = '')
        self.assertEqual(out.getvalue(), '''\
<a>
<b>Hello!<span> There!</span></b>
<c foo="bar">
<d attr1="asdf" attr2="sdfg">
<e>
</e>
</d>
</a>''')
