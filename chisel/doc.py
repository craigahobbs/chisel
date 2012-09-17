#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import cgi
from StringIO import StringIO
import urllib
import xml.sax.saxutils as saxutils

# Helper function to join parts of a URL
def joinUrl(*args):

    return '/'.join(s.strip('/') for s in args)

# Generate the top-level action documentation index
def docIndex(docRootUri, actionModels):

    out = StringIO()

    # HTML header
    out.write("""\
<!doctype html>
<html>
<body>
<h1 class="doc-index">Actions</h1>
<ul>
""")

    # Action docs hyperlinks
    for actionModel in actionModels.itervalues():
        out.write("""\
<li>
<a href="%s">%s</a>
</li>
""" % (joinUrl(docRootUri, urllib.quote(actionModel.name)), cgi.escape(actionModel.name)))

    # HTML footer
    out.write("""\
</ul>
</body>
</html>
""")
    return out.getvalue()

# Generate the documentation for an action
def docAction(docRootUri, actionModel):

    out = StringIO()

    # HTML header
    out.write("""\
<!doctype html>
<html>
<body>
<h1 class="doc-index">%s</h1>
<a href="%s">Back to documentation index</a>
""" % (actionModel.name, docRootUri))

    # HTML footer
    out.write("""\
</body>
</html>
""")
    return out.getvalue()
