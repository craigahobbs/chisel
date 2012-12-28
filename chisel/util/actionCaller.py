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

    def __init__(self, scriptFilename = None, resourceTypes = None,
                 configString = None, configPath = None, application = None):

        if application is not None:
            self._application = application
        else:
            self._application = Application(resourceTypes = resourceTypes, configString = configString)
        self._scriptFilename = scriptFilename
        self._configPath = configPath

    def __call__(self, actionName, request):

        # Serialize the request
        requestJson = json.dumps(request)

        # Call the action
        status, responseHeaders, responseString, wsgi_errors = \
            self.callRaw("POST", "/" + actionName, requestJson)

        # Deserialize the response
        try:
            response = json.loads(responseString)
        except:
            response = responseString

        return (status,
                responseHeaders,
                response,
                wsgi_errors)

    def callRaw(self, method, url, data = None):

        # Test WSGI environment
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": url,
            "wsgi.input": StringIO(data),
            "wsgi.errors": StringIO()
            }
        if self._configPath is not None:
            environ[Application.ENV_CONFIG] = self._configPath
        if self._scriptFilename is not None:
            environ["SCRIPT_FILENAME"] = self._scriptFilename
        if data is not None:
            environ["CONTENT_LENGTH"] = str(len(data))

        # Call the action
        startResponseArgs = {}
        def startResponse(status, responseHeaders):
            startResponseArgs["status"] = status
            startResponseArgs["responseHeaders"] = responseHeaders
        responseParts = self._application(environ, startResponse)
        responseString = "".join(responseParts)

        return (startResponseArgs["status"],
                startResponseArgs["responseHeaders"],
                responseString,
                environ["wsgi.errors"].getvalue())
