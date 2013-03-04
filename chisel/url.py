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

from .compat import basestring_, long_, PY3, unicode_, urllib, xrange_
from .struct import Struct


# Encode an object as a URL query string
def encodeQueryString(o, encoding = "utf-8"):

    # Helper to quote strings
    def quote(o):
        if PY3: # pragma: no cover
            return urllib.quote(o if isinstance(o, str) else str(o), encoding = encoding)
        else:
            return urllib.quote((o if isinstance(o, basestring_) else str(o)).encode(encoding))

    # Get the flattened list of URL-quoted name/value pairs
    keysValues = []
    def iterateItems(o, parent, topLevel = False):

        # Get the wrapped object of a Struct
        if isinstance(o, Struct):
            o = o()

        # Add the object keys
        if isinstance(o, dict):
            if o:
                for member in o:
                    iterateItems(o[member], parent + (quote(member),))
            elif not topLevel:
                keysValues.append((parent, ""))
        elif isinstance(o, (list, tuple)):
            if o:
                for ix in xrange_(0, len(o)):
                    iterateItems(o[ix], parent + (quote(ix),))
            elif not topLevel:
                keysValues.append((parent, ""))
        elif o is not None:
            keysValues.append((parent, quote(o)))

    iterateItems(o, (), topLevel = True)

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
        if PY3: # pragma: no cover
            keys = [makeKey(urllib.unquote(key, encoding = encoding)) for key in keysValue[0].split(".")]
            value = urllib.unquote(keysValue[1], encoding = encoding)
        else:
            keys = [makeKey(urllib.unquote(key).decode(encoding)) for key in keysValue[0].split(".")]
            value = urllib.unquote(keysValue[1]).decode(encoding)

        # Find/create the object on which to set the value
        oParent = oResult
        keyParent = 0
        for key in keys:

            # Array key?
            if isinstance(key, (int, long_)):

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
