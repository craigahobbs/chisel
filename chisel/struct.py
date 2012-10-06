#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Class-syntax wrapper around built-in dictionaries.
class Struct(object):

    def __init__(self, _wrap_ = None, **members):

        if _wrap_ is not None:
            assert isinstance(_wrap_, (dict, list, tuple))
            object.__setattr__(self, "_container", _wrap_)
        else:
            object.__setattr__(self, "_container", members)

    def __call__(self):

        return object.__getattribute__(self, "_container")

    def __getattribute__(self, key):

        container = self()
        if isinstance(container, dict):
            return self[key]
        else:
            return type(container).__getattribute__(container, key)

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
        return Struct(_wrap_ = value) if isinstance(value, (dict, list, tuple)) else value

    def __setitem__(self, key, value):

        # Delete member if value is None
        container = self()
        if value is None:
            if isinstance(container, dict) and key in container:
                del container[key]
            elif isinstance(key, (int, long)) and key >= 0 and key < len(container):
                del container[key]
        else:
            container[key] = value

    def __contains__(self, item):

        return item in self()

    def __len__(self):

        return len(self())

    def __iter__(self):

        class WrapIter:
            def __init__(self, it):
                self._it = it
            def next(self):
                # Return the value - wrap containers
                value = self._it.next()
                return Struct(_wrap_ = value) if isinstance(value, (dict, list, tuple)) else value

        return WrapIter(iter(self()))

    def __cmp__(self, other):

        return cmp(self(), other() if isinstance(other, Struct) else other)
