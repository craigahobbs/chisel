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

from .compat import iteritems, itervalues, long_, pickle


# Class-syntax wrapper around built-in dictionaries.
class Struct(object):

    def __init__(self, container = None, **members):

        if container is not None:
            object.__setattr__(self, "_container", container)
        else:
            object.__setattr__(self, "_container", dict((k, v) for k, v in iteritems(members) if v is not None))

    def __call__(self):

        return object.__getattribute__(self, "_container")

    def __getattr__(self, key):

        container = self()
        if key.startswith("__") and key.endswith("__"):
            return object.__getattribute__(self, key)
        elif isinstance(container, dict) and (key in container or not hasattr(container, key)):
            return self[key]
        else:
            return getattr(container, key)

    def __setattr__(self, key, value):

        container = self()
        if isinstance(container, dict):
            self[key] = value
        else:
            return type(container).__setattr__(container, key, value)

    def __getitem__(self, key):

        # Lookup the value in the container - return None if not found
        container = self()
        if isinstance(container, dict):
            value = container.get(key)
        elif isinstance(key, (int, long_)) and key >= 0 and key < len(container):
            value = container[key]
        else:
            value = None

        # Return the value - wrap containers
        return Struct(value) if isinstance(value, (dict, list, tuple)) else value

    def __setitem__(self, key, value):

        # Delete member if value is None
        container = self()
        if value is None and isinstance(container, dict):
            if key in container:
                del container[key]
        else:
            container[key] = value

    def __delitem__(self, key):

        container = self()
        del container[key]

    def __contains__(self, item):

        return item in self()

    def __len__(self):

        return len(self())

    class _ContainerIter(object):

        def __init__(self, container):

            self._it = iter(container)

        def __next__(self):

            # Return the value - wrap containers
            value = next(self._it)
            return Struct(value) if isinstance(value, (dict, list, tuple)) else value

        def next(self):

            return self.__next__()

    def __iter__(self):

        return Struct._ContainerIter(self())

    def __eq__(self, other):

        return self() == (other() if isinstance(other, Struct) else other)

    def __repr__(self):

        return str(self())

    def __getstate__(self):

        return self()

    def __setstate__(self, d):

        object.__setattr__(self, "_container", d)
