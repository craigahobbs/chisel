#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

try:
    import cPickle as pickle
except:
    import pickle


# Class-syntax wrapper around built-in dictionaries.
class Struct(object):

    def __init__(self, container = None, **members):

        if container is not None:
            object.__setattr__(self, "_container", container)
        else:
            object.__setattr__(self, "_container", members)

    def __call__(self):

        return object.__getattribute__(self, "_container")

    def __getattr__(self, key):

        container = self()
        if isinstance(container, dict) and (key in container or not hasattr(container, key)):
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
        elif isinstance(key, (int, long)) and key >= 0 and key < len(container):
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

    class _ContainerIter:

        def __init__(self, container):

            self._it = iter(container)

        def next(self):

            # Return the value - wrap containers
            value = self._it.next()
            return Struct(value) if isinstance(value, (dict, list, tuple)) else value

    def __iter__(self):

        return Struct._ContainerIter(self())

    def __cmp__(self, other):

        return cmp(self(), other() if isinstance(other, Struct) else other)

    def __repr__(self):

        return str(self())

    def __getstate__(self):

        return self()

    def __setstate__(self, d):

        object.__setattr__(self, "_container", d)
