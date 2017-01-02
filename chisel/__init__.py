#
# Copyright (C) 2012-2016 Craig Hobbs
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

__version__ = '0.9.39'

from .action import \
    action, \
    Action, \
    ActionError

from .app import \
    Application, \
    Context

from .app_defs import \
    ENVIRON_CTX, \
    STATUS_200_OK, \
    STATUS_301_MOVED_PERMANENTLY, \
    STATUS_304_NOT_MODIFIED, \
    STATUS_400_BAD_REQUEST, \
    STATUS_401_UNAUTHORIZED, \
    STATUS_404_NOT_FOUND, \
    STATUS_405_METHOD_NOT_ALLOWED, \
    STATUS_500_INTERNAL_SERVER_ERROR

from .doc import \
    DocAction, \
    DocPage, \
    Element

from .model import \
    ValidationError, \
    VALIDATE_DEFAULT, \
    VALIDATE_QUERY_STRING, \
    VALIDATE_JSON_INPUT

from .request import \
    request, \
    Request

from .spec import \
    SpecParser, \
    SpecParserError

from .url import \
    decode_query_string, \
    encode_query_string

from .util import \
    JSONEncoder, \
    TZLOCAL, \
    TZUTC
