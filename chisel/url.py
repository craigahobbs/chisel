#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

from .struct import Struct

import urllib

# Encode an object as a URL query string
def encodeQueryString(o):

    # Get the flattened list of URL-quoted name/value pairs
    members = []
    def iterateItems(o, parent):
        if isinstance(o, dict) or isinstance(o, Struct):
            for member in o:
                iterateItems(o[member], parent + (urllib.quote(str(member)),))
        elif isinstance(o, list):
            for ix in xrange(0, len(o)):
                iterateItems(o[ix], parent + (str(ix),))
        elif o is not None:
            members.append((parent, urllib.quote(str(o))))
    iterateItems(o, ())

    # Join the object query string
    return "&".join(["=".join(('.'.join(k), v)) for k, v in sorted(members)])


# Decode an object from a URL query string
def decodeQueryString(queryString):

    # Split-out and unquote the flattened members
    members = [([urllib.unquote(k) for k in kq.split('.')], v) for
               kq, v in [kv.split('=') for kv in queryString.split('&')]]

    # Integer member?
    def isArrayMember(member):
        try:
            int(member)
            return True
        except:
            return False

    # Create the top-level container
    if members and isArrayMember(members[0][0][0]):
        o = []
    else:
        o = {}

    # Construct the object
    for key, value in sorted(members):
        oCur = o
        nMembers = len(key)
        for ixMember in xrange(0, nMembers - 1):
            member = key[ixMember]
            memberNext = key[ixMember + 1]

            # Create the sub-container
            oNext = None if isinstance(oCur, list) else oCur.get(member)
            if oNext is None:
                oNext = [] if isArrayMember(memberNext) else {}
            if isinstance(oCur, list):
                oCur.append(oNext)
            else:
                oCur[member] = oNext
            oCur = oNext

        # Set the member value
        if isinstance(oCur, list):
            oCur.append(value)
        else:
            oCur[key[-1]] = urllib.unquote(value)

    return o
