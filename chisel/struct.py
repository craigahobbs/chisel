#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Class-syntax wrapper around built-in dictionaries.
class Struct(object):

    def __init__(self, members = None):

        # Set the member dictionary
        if members is None:
            members = {}
        elif isinstance(members, Struct):
            members = members()
        object.__setattr__(self, "__members", members)

        # Wrap all dictionary member attributes
        for name, value in members.iteritems():
            if isinstance(value, dict):
                members[name] = Struct(value)

    def __call__(self):

        return object.__getattribute__(self, "__members")

    def __getattribute__(self, name):

        return self[name]

    def __setattr__(self, name, value):

        self[name] = value

    def __getitem__(self, key):

        # Get the member - return None if unset
        return self().get(key)

    def __setitem__(self, key, value):

        # Wrap dictionary values
        if isinstance(value, dict):
            value = Struct(value)

        # Delete member if value is None
        if value is None:
            del self()[key]
        else:
            self()[key] = value

    def __contains__(self, item):

        return item in self()

    def __len__(self):

        return len(self())

    def __iter__(self):

        return iter(self())

    def __cmp__(self, other):

        #  Unwrap other structs
        if isinstance(other, Struct):
            return cmp(self(), other())
        else:
            return cmp(self(), other)
