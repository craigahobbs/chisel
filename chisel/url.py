#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct

import urllib


# Encode an object as a URL query string
def encodeQueryString(o):

    # Helper to quote strings
    def quote(o):
        if isinstance(o, str):
            return urllib.quote(o)
        elif isinstance(o, unicode):
            return urllib.quote(o.encode("utf-8"))
        else:
            return urllib.quote(str(o))

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
def decodeQueryString(queryString):

    # Helper to make a key - int means array index
    def makeKey(keyString):
        try:
            return int(keyString)
        except:
            return keyString

    # Split-out and unquote the flattened keys and values
    keysValues = []
    for keysValueString in queryString.split("&"):
        if keysValueString:
            keysValue = keysValueString.split("=")
            if len(keysValue) == 2:
                keys = [makeKey(urllib.unquote(key)) for key in keysValue[0].split(".")]
                value = urllib.unquote(keysValue[1])
                keysValues.append((keys, value, keysValueString))
            else:
                raise ValueError("Invalid key/value pair '%s'" % (keysValueString))

    # Build the object
    oResult = [None]
    for keys, value, keysValueString in keysValues:

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
                    raise ValueError("Invalid key/value pair '%s'" % (keysValueString))

                # Create the index for this key
                if key == len(o):
                    o.extend([None])
                elif key < 0 or key > len(o):
                    raise ValueError("Invalid key/value pair '%s'" % (keysValueString))

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
                    raise ValueError("Invalid key/value pair '%s'" % (keysValueString))

                # Create the index for this key
                if o.get(key) is None:
                    o[key] = None

                # Update the parent object and key
                oParent = o
                keyParent = key

        # Set the value
        oParent[keyParent] = value

    return oResult[0] if (oResult[0] is not None) else {}
