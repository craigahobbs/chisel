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

    # Build the object
    result = [None]
    for key_value_str in query_string.split('&'):

        # Ignore empty key/value strings
        if not key_value_str:
            continue

        # Split the key/value string
        key_value = key_value_str.split('=')
        if len(key_value) != 2:
            raise ValueError("Invalid key/value pair '" + key_value_str + "'")
        value = unquote(key_value[1], encoding=encoding)

        # Find/create the object on which to set the value
        parent = result
        key_parent = 0
        for key in (unquote(key, encoding=encoding) for key in key_value[0].split('.')):
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
                    raise ValueError("Invalid key/value pair '" + key_value_str + "'")
                if key == len(obj):
                    obj.append(None)
                elif key < 0 or key > len(obj):
                    raise ValueError("Invalid key/value pair '" + key_value_str + "'")

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
            raise ValueError("Duplicate key '" + key_value_str + "'")
        parent[key_parent] = value

    return result[0] if (result[0] is not None) else {}
