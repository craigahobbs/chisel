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

from chisel import Action, SpecParser
from chisel.compat import HTMLParser, itervalues, StringIO
from chisel.doc import createIndexHtml, createActionHtml, Element

import unittest


# Simple HTML validator class
class HTMLValidator(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.elements = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("br", "img", "link", "meta"):
            self.elements.append(tag)

    def handle_endtag(self, tag):
        expectedTag = self.elements.pop() if self.elements else None
        assert expectedTag == tag, "Expected '%s' element, got '%s'" % (expectedTag, tag)

    def close(self):
        assert not self.elements, "Un-popped HTML elements! %r" % (self.elements,)
        HTMLParser.close(self)

    @staticmethod
    def validate(html):
        htmlParser = HTMLValidator()
        htmlParser.feed(html)
        htmlParser.close()


# Documentation generation tests
class TestDoc(unittest.TestCase):

    _spec = """
enum MyEnum
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

action myAction1
    input
        MyStruct struct

action myAction2
    output
        MyEnum enum
    errors
        MyError1
        MyError2
"""

    # Test documentation index HTML generation
    def test_doc_createIndexHtml(self):

        # Create the action models
        specParser = SpecParser()
        specParser.parseString(self._spec)
        self.assertEqual(len(specParser.errors), 0)

        # Validate the HTML
        html = createIndexHtml("", "/", itervalues(specParser.actions))
        HTMLValidator.validate(html)
        self.assertTrue('<li><a href="/?action=myAction1">myAction1</a></li>' in html)
        self.assertTrue('<li><a href="/?action=myAction2">myAction2</a></li>' in html)
        self.assertTrue('<style type="text/css">' in html)

        # Validate the HTML (custom CSS)
        html = createIndexHtml("", "/", itervalues(specParser.actions), docCssUri = "/mystyle.css")
        HTMLValidator.validate(html)
        self.assertTrue('<li><a href="/?action=myAction1">myAction1</a></li>' in html)
        self.assertTrue('<li><a href="/?action=myAction2">myAction2</a></li>' in html)
        self.assertTrue('<link href="/mystyle.css" rel="stylesheet" type="text/css">' in html)

    # Test action model HTML generation
    def test_doc_createActionHtml(self):

        myAction1 = Action(name = "myAction1", actionSpec = self._spec)
        myAction2 = Action(name = "myAction2", actionSpec = self._spec)

        # Validate the first myAction1's HTML
        html = createActionHtml("", "/", myAction1)
        HTMLValidator.validate(html)
        self.assertTrue('<h1>myAction1</h1>' in html)
        self.assertTrue('<h2 id="myAction1_Input"><a class="linktarget">Input Parameters</a></h2>' in html)
        self.assertTrue('The action has no input parameters.' not in html)
        self.assertTrue('<h2 id="myAction1_Output"><a class="linktarget">Output Parameters</a></h2>' in html)
        self.assertTrue('The action has no output parameters.' in html)
        self.assertTrue('<h2 id="myAction1_Error"><a class="linktarget">Error Codes</a></h2>' in html)
        self.assertTrue('The action returns no custom error codes.' in html)
        self.assertTrue('<h2>User Types</h2>' in html)
        self.assertTrue('<style type="text/css">' in html)

        # Validate the myAction2's HTML
        html = createActionHtml("", "/", myAction2)
        HTMLValidator.validate(html)
        self.assertTrue('<h1>myAction2</h1>' in html)
        self.assertTrue('<h2 id="myAction2_Input"><a class="linktarget">Input Parameters</a></h2>' in html)
        self.assertTrue('The action has no input parameters.' in html)
        self.assertTrue('<h2 id="myAction2_Output"><a class="linktarget">Output Parameters</a></h2>' in html)
        self.assertTrue('The action has no output parameters.' not in html)
        self.assertTrue('<h2 id="myAction2_Error"><a class="linktarget">Error Codes</a></h2>' in html)
        self.assertTrue('The action returns no custom error codes.' not in html)
        self.assertTrue('<h2>User Types</h2>' in html)
        self.assertTrue('<style type="text/css">' in html)

        # Validate the first myAction1's HTML (custom CSS)
        html = createActionHtml("", "/", myAction1, docCssUri = "/mystyle.css")
        HTMLValidator.validate(html)
        self.assertTrue('<h1>myAction1</h1>' in html)
        self.assertTrue('<h2 id="myAction1_Input"><a class="linktarget">Input Parameters</a></h2>' in html)
        self.assertTrue('The action has no input parameters.' not in html)
        self.assertTrue('<h2 id="myAction1_Output"><a class="linktarget">Output Parameters</a></h2>' in html)
        self.assertTrue('The action has no output parameters.' in html)
        self.assertTrue('<h2 id="myAction1_Error"><a class="linktarget">Error Codes</a></h2>' in html)
        self.assertTrue('The action returns no custom error codes.' in html)
        self.assertTrue('<h2>User Types</h2>' in html)
        self.assertTrue('<link href="/mystyle.css" rel="stylesheet" type="text/css">' in html)

    # Test doc generation element class
    def test_doc_element(self):

        # Test basic DOM element serialization functionality
        root = Element("a")
        b = root.addChild("b")
        b.addChild("Hello!", isInline = True, isText = True)
        b.addChild("span", isInline = True).addChild(" There!", isText = True)
        root.addChild("c", isClosed = False, foo = "bar")
        root.addChild("d", attr1 = "asdf", _attr2 = "sdfg").addChild("e")

        # Default (indented)
        out = StringIO()
        root.serialize(out)
        self.assertEqual(out.getvalue(), """\
<a>
  <b>Hello!<span> There!</span></b>
  <c foo="bar">
  <d attr1="asdf" attr2="sdfg">
    <e>
    </e>
  </d>
</a>""")

        # Not indented
        out = StringIO()
        root.serialize(out, indent = "")
        self.assertEqual(out.getvalue(), """\
<a>
<b>Hello!<span> There!</span></b>
<c foo="bar">
<d attr1="asdf" attr2="sdfg">
<e>
</e>
</d>
</a>""")
