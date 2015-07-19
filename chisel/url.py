#
# Copyright (C) 2012-2015 Craig Hobbs
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

from .compat import basestring_, urllib_parse_quote, urllib_parse_unquote, xrange_
from .model import JsonDate, JsonDatetime, JsonUUID

from datetime import date, datetime
from uuid import UUID


# Encode an object as a URL query string
def encodeQueryString(o, encoding='utf-8'):

    # Get the flattened list of URL-quoted name/value pairs
    def iterateItems(o, parent, topLevel=False):
        if isinstance(o, dict):
            if o:
                for member in o:
                    for child in iterateItems(o[member], parent + (urllib_parse_quote(member, encoding=encoding),)):
                        yield child
            elif not topLevel:
                yield (parent, '')
        elif isinstance(o, list) or isinstance(o, tuple):
            if o:
                for ix in xrange_(0, len(o)):
                    for child in iterateItems(o[ix], parent + (urllib_parse_quote(str(ix), encoding=encoding),)):
                        yield child
            elif not topLevel:
                yield (parent, '')
        else:
            if isinstance(o, date):
                ostr = str(JsonDate(o)).strip('"')
            elif isinstance(o, datetime):
                ostr = str(JsonDatetime(o)).strip('"')
            elif isinstance(o, UUID):
                ostr = str(JsonUUID(o)).strip('"')
            elif isinstance(o, bool):
                ostr = 'true' if o else 'false'
            else:
                ostr = o if isinstance(o, basestring_) else str(o)
            yield (parent, urllib_parse_quote(ostr, encoding=encoding))

    # Join the object query string
    return '&'.join('='.join(('.'.join(k), v)) for k, v in sorted(iterateItems(o, (), topLevel=True)))


# Decode an object from a URL query string
def decodeQueryString(queryString, encoding='utf-8'):

    # Build the object
    oResult = [None]
    for keysValueString in queryString.split('&'):

        # Ignore empty key/value strings
        if not keysValueString:
            continue

        # Split the key/value string
        keysValue = keysValueString.split('=')
        if len(keysValue) != 2:
            raise ValueError("Invalid key/value pair '" + keysValueString + "'")
        value = urllib_parse_unquote(keysValue[1], encoding=encoding)

        # Find/create the object on which to set the value
        oParent = oResult
        keyParent = 0
        for key in (urllib_parse_unquote(key, encoding=encoding) for key in keysValue[0].split('.')):
            o = oParent[keyParent]

            # Array key?  First "key" of an array must start with "0".
            if isinstance(o, list) or (o is None and key == '0'):

                # Create this key's container, if necessary
                if o is None:
                    o = oParent[keyParent] = []

                # Create the index for this key
                try:
                    key = int(key)
                except:
                    raise ValueError("Invalid key/value pair '" + keysValueString + "'")
                if key == len(o):
                    o.append(None)
                elif key < 0 or key > len(o):
                    raise ValueError("Invalid key/value pair '" + keysValueString + "'")

            # Dictionary key
            else:

                # Create this key's container, if necessary
                if o is None:
                    o = oParent[keyParent] = {}

                # Create the index for this key
                if o.get(key) is None:
                    o[key] = None

            # Update the parent object and key
            oParent = o
            keyParent = key

        # Set the value
        if oParent[keyParent] is not None:
            raise ValueError("Duplicate key '" + keysValueString + "'")
        oParent[keyParent] = value

    return oResult[0] if (oResult[0] is not None) else {}
