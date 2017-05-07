# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from io import BytesIO

from .url import encode_query_string


class Environ(object):
    """WSGI environment variables"""

    __slots__ = ()

    CTX = 'chisel.ctx'

    @staticmethod
    def create(request_method, path_info, query_string='', wsgi_input=b'', environ=None):
        if environ is None:
            environ = {}
        environ.setdefault('REQUEST_METHOD', request_method)
        environ.setdefault('PATH_INFO', path_info)
        environ.setdefault('QUERY_STRING', query_string if isinstance(query_string, str) else encode_query_string(query_string))
        environ.setdefault('SCRIPT_NAME', '')
        environ.setdefault('SERVER_NAME', 'localhost')
        environ.setdefault('SERVER_PORT', '80')
        environ.setdefault('wsgi.input', BytesIO(wsgi_input))
        environ.setdefault('wsgi.url_scheme', 'http')
        return environ


class StartResponse(object):
    __slots__ = ('status', 'headers')

    def __init__(self):
        self.status = None
        self.headers = None

    def __call__(self, status, headers):
        assert self.status is None and self.headers is None
        self.status = status
        self.headers = headers
