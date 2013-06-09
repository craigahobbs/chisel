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


# Resource type
class ResourceType(object):

    def __init__(self, name, resourceOpen, resourceClose):
        self.name = name
        self.__open = resourceOpen
        self.__close = resourceClose

    def open(self, resourceString):
        return self.__open(resourceString)

    def close(self, resource):
        if self.__close is not None:
            return self.__close(resource)


# Resource context manager
class ResourceContext(object):

    def __init__(self, resourceOpen, resourceClose, resourceString):
        self._resourceOpen = resourceOpen
        self._resourceClose = resourceClose
        self._resourceString = resourceString
        self._resource = None

    def __enter__(self):
        self._resource = self._resourceOpen(self._resourceString)
        return self._resource

    def __exit__(self, exc_type, exc_value, traceback):
        if self._resourceClose:
            self._resourceClose(self._resource)
        self._resource = None


# Resource collection
class ResourceCollection(object):

    Resource = namedtuple('Resource', ('resourceName', 'resourceOpen', 'resourceClose', 'resourceString'))

    def __init__(self):
        self._resources = {}

    def add(self, resourceName, resourceOpen, resourceClose, resourceString):
        object.__getattribute__(self, '_resources')[resourceName] = self.Resource(resourceName, resourceOpen, resourceClose, resourceString)

    def __getattribute__(self, name):
        resource = object.__getattribute__(self, '_resources').get(name)
        if resource is None:
            return object.__getattribute__(self, name)
        return ResourceContext(resource.resourceOpen, resource.resourceClose, resource.resourceString)

    def __getitem__(self, name):
        resource = object.__getattribute__(self, '_resources').get(name)
        if resource is None:
            raise IndexError("No resource named '" + name + "'")
        return ResourceContext(resource.resourceOpen, resource.resourceClose, resource.resourceString)
