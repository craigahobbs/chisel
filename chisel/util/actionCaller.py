#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import json
from StringIO import StringIO

from .. import Application


# Mock application for testing action calls - returns (status, headers, response, logOutput)
class ActionCaller:

    def __init__(self, scriptFilename, resourceTypes = None, configString = None, configPath = None):

        self._application = Application(resourceTypes = resourceTypes, configString = configString)
        self._scriptFilename = scriptFilename
        self._configPath = configPath

    def __call__(self, actionName, request):

        # Serialize the request
        requestJson = json.dumps(request)

        # Test WSGI environment
        environ = {
            Application.ENV_CONFIG: self._configPath,
            "SCRIPT_FILENAME": self._scriptFilename,
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/" + actionName,
            "CONTENT_LENGTH": str(len(requestJson)),
            "wsgi.input": StringIO(requestJson),
            "wsgi.errors": StringIO()
            }

        # Call the action
        startResponseArgs = {}
        def startResponse(status, responseHeaders):
            startResponseArgs["status"] = status
            startResponseArgs["responseHeaders"] = responseHeaders
        responseParts = self._application(environ, startResponse)
        responseString = "".join(responseParts)

        # Deserialize the response
        try:
            response = json.loads(responseString)
        except:
            response = responseString

        return (startResponseArgs["status"],
                startResponseArgs["responseHeaders"],
                response,
                environ["wsgi.errors"].getvalue())
