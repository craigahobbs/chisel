#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import Application, ResourceType

import os
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import unittest


# Main WSGI application callable-object tests
class TestAppApplication(unittest.TestCase):

    def getConfigPath(self):
        return os.path.join("test_app_files", "default.json")

    def getResourceTypes(self):

        resourceData = {
            "open": [],
            "close": []
            }
        def resourceTypeOpen(resourceString):
            resourceData["open"].append(resourceString)
            return len(resourceData["open"])
        def resourceTypeClose(resource):
            resourceData["close"].append(resource)

        return resourceData, [ResourceType("test_app_resource", resourceTypeOpen, resourceTypeClose),
                              ResourceType("mytype", lambda resourceString: 9, lambda resource: None)]

    # Test default application functionality
    def test_app_default(self):

        # Test WSGI environment
        environ = {
            Application.ENV_CONFIG: self.getConfigPath(),
            "SCRIPT_FILENAME": os.path.join(__file__),
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/myAction",
            "wsgi.errors": StringIO()
            }
        startResponseData = {
            "status": [],
            "responseHeaders": []
            }
        def startResponse(status, responseHeaders):
            startResponseData["status"].append(status)
            startResponseData["responseHeaders"].append(responseHeaders)

        # Verify that unknown resource type exception is raised
        try:
            app = Application()
            app(environ, startResponse)
        except Exception as e:
            self.assertEqual(str(e), "Unknown resource type 'test_app_resource'")
        except:
            self.fail()

        # Successfully create and call the application
        resourceData, resourceTypes = self.getResourceTypes()
        app = Application(resourceTypes = resourceTypes)
        responseParts = app(environ, startResponse)
        self.assertEqual(responseParts, ("{}",))
        self.assertEqual(startResponseData["status"], ["200 OK"])
        self.assertEqual(resourceData["open"], ["Hello"])
        self.assertEqual(resourceData["close"], [1])
        self.assertTrue("Some info" not in environ["wsgi.errors"].getvalue())
        self.assertTrue("A warning bar, thud" in environ["wsgi.errors"].getvalue())

        # Call the application again (skips reloading)
        responseParts = app(environ, startResponse)
        self.assertEqual(responseParts, ("{}",))
        self.assertEqual(startResponseData["status"], ["200 OK", "200 OK"])
        self.assertEqual(resourceData["open"], ["Hello", "Hello"])
        self.assertEqual(resourceData["close"], [1, 2])
        self.assertTrue("Some info" not in environ["wsgi.errors"].getvalue())
        self.assertTrue("A warning bar, thud" in environ["wsgi.errors"].getvalue())

    # Test callAction method
    def test_app_callAction(self):

        # Create the action caller
        resourceData, resourceTypes = self.getResourceTypes()
        app = Application(resourceTypes = resourceTypes, configPath = self.getConfigPath(),
                          scriptFilename = __file__)

        # Call action
        status, headers, response, logOutput = app.callAction("myAction2", { "value": 7 })
        self.assertEqual(response, { "result": 63 })
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(logOutput, "In myAction2\n")

        # Call action again
        status, headers, response, logOutput = app.callAction("myAction2", { "value": 8 })
        self.assertEqual(response, { "result": 72 })
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(logOutput, "In myAction2\n")

        # HTTP error
        status, headers, response, logOutput = app.callAction("unknownAction", {})
        self.assertEqual(response, "Not Found")
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(logOutput, "")

        # Call action with environ
        status, headers, response, logOutput = app.callAction("myAction2", { "value": 9 }, environ = { "MYENVIRON": "10" })
        self.assertEqual(response, { "result": 90 })
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(logOutput, "In myAction2\n")
