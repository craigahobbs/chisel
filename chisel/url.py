# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from datetime import date, datetime
from urllib.parse import quote, unquote
from uuid import UUID

from .util import TZLOCAL


# Encode an object as a URL query string
def encode_query_string(obj, encoding='utf-8'):
    return '&'.join(k + '=' + v for k, v in encode_query_string_items(obj, encoding=encoding))


def encode_query_string_items(obj, parent=None, encoding=None):
    if isinstance(obj, dict):
        if obj:
            for member, value in sorted(obj.items()):
                member_quoted = quote(str(member), encoding=encoding) if encoding else str(member)
                parent_member = parent + '.' + member_quoted if parent else member_quoted
                yield from encode_query_string_items(value, parent=parent_member, encoding=encoding)
        elif parent:
            yield parent, ''
    elif isinstance(obj, (list, tuple)):
        if obj:
            for idx, value in enumerate(obj):
                parent_member = parent + '.' + str(idx) if parent else str(idx)
                yield from encode_query_string_items(value, parent=parent_member, encoding=encoding)
        elif parent:
            yield parent, ''
    else:
        if isinstance(obj, bool):
            yield parent, 'true' if obj else 'false' # quote safe
        elif isinstance(obj, int):
            yield parent, str(obj) # quote safe
        elif isinstance(obj, datetime):
            if not obj.tzinfo:
                obj = obj.replace(tzinfo=TZLOCAL)
            yield parent, quote(obj.isoformat(), encoding=encoding) if encoding else obj.isoformat()
        elif isinstance(obj, date):
            yield parent, obj.isoformat() # quote safe
        elif isinstance(obj, UUID):
            yield parent, str(obj) # quote safe
        elif obj is None:
            yield parent, 'null' # quote safe
        else: # str, float
            yield parent, quote(str(obj), encoding=encoding) if encoding else str(obj)


# Decode an object from a URL query string
def decode_query_string(query_string, encoding='utf-8'):
    return decode_query_string_items(
        (key_value_str.split('=') for key_value_str in query_string.split('&') if key_value_str),
        encoding=encoding
    )


def decode_query_string_items(query_string_items, encoding=None):

    # Build the object
    result = [None]
    for key_value in query_string_items:

        # Split the key/value string
        try:
            key_str, value_str = key_value
            value = unquote(value_str, encoding=encoding) if encoding else value_str
        except ValueError:
            raise ValueError("Invalid key/value pair '" + '='.join(key_value) + "'")

        # Find/create the object on which to set the value
        parent = result
        key_parent = 0
        for key in (unquote(key, encoding=encoding) if encoding else key for key in key_str.split('.')):
            obj = parent[key_parent]

            # Array key?  First "key" of an array must start with "0".
            if isinstance(obj, list) or (obj is None and key == '0'):

                # Create this key's container, if necessary
                if obj is None:
                    obj = parent[key_parent] = []

                # Create the index for this key
                try:
                    key = int(key)
                except:
                    raise ValueError("Invalid key/value pair '" + '='.join(key_value) + "'")
                if key == len(obj):
                    obj.append(None)
                elif key < 0 or key > len(obj):
                    raise ValueError("Invalid key/value pair '" + '='.join(key_value) + "'")

            # Dictionary key
            else:

                # Create this key's container, if necessary
                if obj is None:
                    obj = parent[key_parent] = {}

                # Create the index for this key
                if obj.get(key) is None:
                    obj[key] = None

            # Update the parent object and key
            parent = obj
            key_parent = key

        # Set the value
        if parent[key_parent] is not None:
            raise ValueError("Duplicate key '" + '='.join(key_value) + "'")
        parent[key_parent] = value

    return result[0] if (result[0] is not None) else {}
