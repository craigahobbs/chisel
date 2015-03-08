#
# Copyright (C) 2012-2014 Craig Hobbs
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

from . import action as _action
from . import app as _app
from . import doc as _doc
from . import model as _model
from . import request as _request
from . import spec as _spec
from . import url as _url

Action = _action.Action
action = _action.Action
ActionError = _action.ActionError

Application = _app.Application

DocAction = _doc.DocAction
DocPage = _doc.DocPage

JsonDate = _model.JsonDate
JsonDatetime = _model.JsonDatetime
JsonFloat = _model.JsonFloat
JsonUUID = _model.JsonUUID
AttributeValidationError = _model.ValidationError
ValidationError = _model.ValidationError
tzutc = _model.tzutc
tzlocal = _model.tzlocal
VALIDATE_DEFAULT = _model.VALIDATE_DEFAULT
VALIDATE_QUERY_STRING = _model.VALIDATE_QUERY_STRING
VALIDATE_JSON_INPUT = _model.VALIDATE_JSON_INPUT
VALIDATE_JSON_OUTPUT = _model.VALIDATE_JSON_OUTPUT

Request = _request.Request
request = _request.Request

SpecParser = _spec.SpecParser
SpecParserError = _spec.SpecParserError

decodeQueryString = _url.decodeQueryString
encodeQueryString = _url.encodeQueryString
