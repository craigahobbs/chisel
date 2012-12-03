#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Application, ResourceType

import os
from StringIO import StringIO
import unittest


# Main WSGI application callable-object tests
class TestApplication(unittest.TestCase):

    # Test default application functionality
    def test_app_default(self):

        # Test resource type
        def resourceTypeOpen(rs):
            appData["open"].append(rs)
            return len(appData["open"])
        def resourceTypeClose(r):
            appData["close"].append(r)
        resourceType = ResourceType("test_app_resource", resourceTypeOpen, resourceTypeClose)

        # Test WSGI environment
        environ = {
            Application.ENV_CONFIG: os.path.join(os.path.dirname(__file__), "test_app_files", "default.json"),
            "SCRIPT_FILENAME": os.path.join(__file__),
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/myAction",
            "wsgi.errors": StringIO()
            }
        def startResponse(status, responseHeaders):
            appData["status"].append(status)
            appData["responseHeaders"].append(responseHeaders)

        # Verify that unknown resource type exception is raised
        try:
            app = Application()
            app(environ, startResponse)
            self.fail()
        except Exception, e:
            self.assertEqual(str(e), "Unknown resource type 'test_app_resource'")

        # Successfully create and call the application
        app = Application(resourceTypes = [resourceType])
        appData = {
            "open": [],
            "close": [],
            "status": [],
            "responseHeaders": []
            }
        app(environ, startResponse)
        self.assertEqual(appData["status"], ["200 OK"])
        self.assertEqual(appData["open"], ["Hello"])
        self.assertEqual(appData["close"], [1])
        self.assertTrue("Some info" not in environ["wsgi.errors"].getvalue())
        self.assertTrue("A warning" in environ["wsgi.errors"].getvalue())

        # Call the application again (skips reloading)
        appData = {
            "open": [],
            "close": [],
            "status": [],
            "responseHeaders": []
            }
        app(environ, startResponse)
        self.assertEqual(appData["status"], ["200 OK"])
        self.assertEqual(appData["open"], ["Hello"])
        self.assertEqual(appData["close"], [1])
        self.assertTrue("Some info" not in environ["wsgi.errors"].getvalue())
        self.assertTrue("A warning" in environ["wsgi.errors"].getvalue())

