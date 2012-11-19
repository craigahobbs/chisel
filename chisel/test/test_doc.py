#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import SpecParser
from chisel.doc import joinUrl, createIndexHtml, createActionHtml, Element

from HTMLParser import HTMLParser
from StringIO import StringIO
import unittest


# joinUrl tests
class TestJoinUrl(unittest.TestCase):

    def test_doc_joinUrl(self):

        # No trailing slash
        self.assertEqual(joinUrl("http://foo", "bar"), "http://foo/bar")

        # Trailing slash
        self.assertEqual(joinUrl("http://foo/", "bar"), "http://foo/bar")

        # Trailing slash and preceding slash
        self.assertEqual(joinUrl("http://foo/", "/bar"), "http://foo/bar")

        # Fully slashed
        self.assertEqual(joinUrl("http://foo/", "/bar/"), "http://foo/bar")

        # Preceding slash
        self.assertEqual(joinUrl("http://foo", "/bar"), "http://foo/bar")


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
        assert not self.elements, "Un-popped HTML elements! %r" % (self.elements)
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
    enum member6
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
        specParser.parse(self._spec)
        self.assertEqual(len(specParser.errors), 0)

        # Validate the HTML
        html = createIndexHtml("/", specParser.model.actions.itervalues())
        HTMLValidator.validate(html)
        self.assertTrue('<li><a href="/myAction1">myAction1</a></li>' in html)
        self.assertTrue('<li><a href="/myAction2">myAction2</a></li>' in html)
        self.assertTrue('<style type="text/css">' in html)

        # Validate the HTML (custom CSS)
        html = createIndexHtml("/", specParser.model.actions.itervalues(), docCssUri = "/mystyle.css")
        HTMLValidator.validate(html)
        self.assertTrue('<li><a href="/myAction1">myAction1</a></li>' in html)
        self.assertTrue('<li><a href="/myAction2">myAction2</a></li>' in html)
        self.assertTrue('<link href="/mystyle.css" rel="stylesheet" type="text/css">' in html)

    # Test action model HTML generation
    def test_doc_createActionHtml(self):

        # Create the action models
        specParser = SpecParser()
        specParser.parse(self._spec)
        self.assertEqual(len(specParser.errors), 0)

        # Validate the first myAction1's HTML
        html = createActionHtml("/", specParser.model.actions["myAction1"])
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
        html = createActionHtml("/", specParser.model.actions["myAction2"])
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
        html = createActionHtml("/", specParser.model.actions["myAction1"], docCssUri = "/mystyle.css")
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
