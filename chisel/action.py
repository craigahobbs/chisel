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

from collections import namedtuple

from .compat import func_name, itervalues
from .spec import SpecParser


# Action path helper class
class ActionPath(namedtuple("ActionPath", "method path")):
    def __new__(cls, method, path):
        return super(cls, cls).__new__(cls, method.upper(), path)


# API callback decorator - used to identify action callback functions during module loading
class Action(object):

    def __init__(self, _fn = None, name = None, path = None, actionSpec = None, actionModel = None,
                 responseCallback = None, validateResponse = True):

        # Spec provided?
        if actionModel is None and actionSpec is not None:
            specParser = SpecParser()
            specParser.parseString(actionSpec)
            if name is not None:
                actionModel = specParser.actions[name]
            else:
                for actionModel in itervalues(specParser.actions):
                    break

        self.fn = _fn
        self.name = name
        self.path = path if path is None else [ActionPath(*p) for p in path]
        self.model = actionModel
        self._setDefaults()
        self.responseCallback = responseCallback
        self.validateResponse = validateResponse

    def _setDefaults(self):

        # Set the name - default is the function name
        if self.name is None:
            if self.model is not None:
                self.name = self.model.name
            elif self.fn is not None:
                self.name = func_name(self.fn)

        # Set the path - default is name at root
        if self.path is None and self.name is not None:
            defaultPath = "/" + self.name
            self.path = [ActionPath("GET", defaultPath),
                         ActionPath("POST", defaultPath)]

    def __call__(self, *args):

        # If not constructed as function decorator, first call must be function decorator...
        if self.fn is None:
            self.fn = args[0]
            self._setDefaults()
            return self
        else:
            return self.fn(*args)


# Action error response exception
class ActionError(Exception):

    def __init__(self, error, message = None):

        Exception.__init__(self, error)
        self.error = error
        self.message = message
