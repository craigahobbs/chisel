#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from chisel import ResourceType
from chisel.util import ActionCaller

import unittest


# Test action caller functionality
class TestLoadModules(unittest.TestCase):

    # Test basic action call
    def test_util_actionCaller(self):

        # Create the action caller
        resourceTypes = [
            ResourceType("mytype",
                         lambda resourceName, resourceString: 9,
                         lambda resource: None)
            ]
        configString = """\
{
    "specPaths": ["test_util_actionCaller_files"],
    "modulePaths": ["test_util_actionCaller_files"],
    "resources": [
        {
            "name": "myresource",
            "type": "mytype",
            "resourceString": "mystring"
        }
    ],
    "logLevel": "Info"
}
"""
        ac = ActionCaller(__file__, resourceTypes = resourceTypes, configString = configString)

        # Call action
        status, headers, response, logOutput = ac("myAction", { "value": 7 })
        self.assertEqual(response, { "result": 63 })
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(logOutput, "In myAction\n")

        # Call action again
        status, headers, response, logOutput = ac("myAction", { "value": 8 })
        self.assertEqual(status, "200 OK")
        self.assertTrue(('Content-Type', 'application/json') in headers)
        self.assertEqual(response, { "result": 72 })
        self.assertEqual(logOutput, "In myAction\n")

        # HTTP error
        status, headers, response, logOutput = ac("unknownAction", {})
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(('Content-Type', 'text/plain') in headers)
        self.assertEqual(response, "Not Found")
        self.assertEqual(logOutput, "")
