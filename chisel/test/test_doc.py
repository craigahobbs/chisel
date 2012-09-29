#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import SpecParser
from chisel.doc import joinUrl, docIndex, docAction

from HTMLParser import HTMLParser
from StringIO import StringIO
import unittest


# joinUrl tests
class TestJoinUrl(unittest.TestCase):

    def test_joinUrl(self):

        self.assertEqual("http://foo/bar", joinUrl("http://foo", "bar"))
        self.assertEqual("http://foo/bar", joinUrl("http://foo/", "bar"))
        self.assertEqual("http://foo/bar", joinUrl("http://foo/", "/bar"))
        self.assertEqual("http://foo/bar", joinUrl("http://foo/", "/bar/"))


# Simple HTML validator class
class HTMLValidator(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.elements = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("br", "img", "meta"):
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

    # Test documentation index HTML generation
    def test_docIndex(self):

        # Create the action models
        specParser = SpecParser()
        specParser.parse(StringIO("""\
action myAction1
action myAction2
"""))

        # Validate the HTML
        html = docIndex("/", specParser.model.actions.itervalues())
        HTMLValidator.validate(html)


    # Test action model HTML generation
    def test_docAction(self):

        # Create the action models
        specParser = SpecParser()
        specParser.parse(StringIO("""\
action myAction1
action myAction2
"""))

        # Validate the HTML
        html = docAction("/", specParser.model.actions["myAction1"])
        HTMLValidator.validate(html)
