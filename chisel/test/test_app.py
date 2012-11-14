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

    # Setup the test
    def setUp(self):

        # Change the current working directory
        self._cwdOrig = os.getcwd()
        self._rootDir = os.path.dirname(__file__)
        os.chdir(self._rootDir)

        # Config files
        self._configDefault = os.path.join(self._rootDir, "test_app_files", "default.json")

    # Tear down the test
    def tearDown(self):

        # Restore the current working directory
        os.chdir(self._cwdOrig)

    # Test default application functionality
    def test_app_default(self):

        # Verify that unknown resource type exception is raised
        try:
            app = Application(configPath = self._configDefault)
            self.fail()
        except Exception, e:
            self.assertEqual(str(e), "Unknown resource type 'test_app_resource'")

        # Test resource type
        def resourceTypeOpen(rs):
            appData["open"].append(rs)
            return len(appData["open"])
        def resourceTypeClose(r):
            appData["close"].append(r)
        resourceType = ResourceType("test_app_resource", resourceTypeOpen, resourceTypeClose)

        # Test WSGI environment
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/myAction",
            "wsgi.errors": StringIO()
            }
        def startResponse(status, responseHeaders):
            appData["status"].append(status)
            appData["responseHeaders"].append(responseHeaders)

        # Successfully create and call the application
        appData = {
            "open": [],
            "close": [],
            "status": [],
            "responseHeaders": []
            }
        app = Application(configPath = self._configDefault,
                          resourceTypes = [resourceType])
        app(environ, startResponse)
        self.assertEqual(appData["status"], ["200 OK"])
        self.assertEqual(appData["open"], ["Hello"])
        self.assertEqual(appData["close"], [1])
        self.assertTrue(environ["wsgi.errors"].getvalue().find("Some info") == -1)
        self.assertTrue(environ["wsgi.errors"].getvalue().find("A warning") != -1)
