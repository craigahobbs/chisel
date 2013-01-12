#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct

import urllib


# Encode an object as a URL query string
def encodeQueryString(o, encoding = "utf-8"):

    # Helper to quote strings
    def quote(o):
        return urllib.quote((o if isinstance(o, basestring) else str(o)).encode(encoding))

    # Get the flattened list of URL-quoted name/value pairs
    keysValues = []
    def iterateItems(o, parent):

        # Get the wrapped object of a Struct
        if isinstance(o, Struct):
            o = o()

        # Add the object keys
        if isinstance(o, dict):
            for member in o:
                iterateItems(o[member], parent + (quote(member),))
        elif isinstance(o, (list, tuple)):
            for ix in xrange(0, len(o)):
                iterateItems(o[ix], parent + (quote(ix),))
        elif o is not None:
            keysValues.append((parent, quote(o)))

    iterateItems(o, ())

    # Join the object query string
    return "&".join(["=".join((".".join(k), v)) for k, v in sorted(keysValues)])


# Decode an object from a URL query string
def decodeQueryString(queryString, encoding = "utf-8"):

    # Helper to make a key - int means array index
    def makeKey(keyString):
        try:
            return int(keyString)
        except:
            return keyString

    # Build the object
    oResult = [None]
    for keysValueString in queryString.split("&"):

        # Ignore empty key/value strings
        if not keysValueString:
            continue

        # Split the key/value string
        keysValue = keysValueString.split("=")
        if len(keysValue) != 2:
            raise ValueError("Invalid key/value pair '%s'" % (keysValueString,))
        keys = [makeKey(urllib.unquote(key).decode(encoding)) for key in keysValue[0].split(".")]
        value = urllib.unquote(keysValue[1]).decode(encoding)

        # Find/create the object on which to set the value
        oParent = oResult
        keyParent = 0
        for key in keys:

            # Array key?
            if isinstance(key, (int, long)):

                # Create this key's container, if necessary
                o = oParent[keyParent]
                if o is None:
                    o = oParent[keyParent] = []
                elif not isinstance(o, list):
                    raise ValueError("Invalid key/value pair '%s'" % (keysValueString,))

                # Create the index for this key
                if key == len(o):
                    o.extend([None])
                elif key < 0 or key > len(o):
                    raise ValueError("Invalid key/value pair '%s'" % (keysValueString,))

                # Update the parent object and key
                oParent = o
                keyParent = key

            # Dictionary key
            else:

                # Create this key's container, if necessary
                o = oParent[keyParent]
                if o is None:
                    o = oParent[keyParent] = {}
                elif not isinstance(o, dict):
                    raise ValueError("Invalid key/value pair '%s'" % (keysValueString,))

                # Create the index for this key
                if o.get(key) is None:
                    o[key] = None

                # Update the parent object and key
                oParent = o
                keyParent = key

        # Set the value
        oParent[keyParent] = value

    return oResult[0] if (oResult[0] is not None) else {}
