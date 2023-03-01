# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring

from http import HTTPStatus
from io import StringIO
from unittest import TestCase

from schema_markdown import SchemaMarkdownParserError, parse_schema_markdown

from chisel import action, Action, ActionError, Application, Request


class TestAction(TestCase):

    # Default action decorator
    def test_decorator(self):

        @action(spec='''\
action my_action_default
''')
        def my_action_default(unused_app, unused_req):
            pass # pragma: no cover

        self.assertTrue(isinstance(my_action_default, Action))
        self.assertTrue(isinstance(my_action_default, Request))

        app = Application()
        app.add_request(my_action_default)
        self.assertEqual(my_action_default.name, 'my_action_default')
        self.assertEqual(my_action_default.urls, (('POST', '/my_action_default'),))
        self.assertTrue(isinstance(my_action_default.model, dict))
        self.assertEqual(my_action_default.model['name'], 'my_action_default')
        self.assertEqual(my_action_default.wsgi_response, False)

    # Default action decorator with missing spec
    def test_decorator_unknown_action(self):

        with self.assertRaises(AssertionError) as cm_exc:
            @action
            def unused_my_action(unused_app, unused_req): # pragma: no cover
                pass
        self.assertEqual(str(cm_exc.exception), 'Unknown action "unused_my_action"')

    # Action decorator with spec
    def test_decorator_spec(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        self.assertTrue(isinstance(my_action, Action))
        self.assertTrue(isinstance(my_action, Request))

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'my_action')
        self.assertEqual(my_action.urls, (('POST', '/my_action'),))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'my_action')
        self.assertEqual(my_action.wsgi_response, False)

    # Action decorator with spec parser
    def test_decorator_types(self):

        types = parse_schema_markdown('''\
action my_action
''')
        @action(types=types)
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        self.assertTrue(isinstance(my_action, Action))
        self.assertTrue(isinstance(my_action, Request))

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'my_action')
        self.assertEqual(my_action.urls, (('POST', '/my_action'),))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'my_action')
        self.assertEqual(my_action.wsgi_response, False)

    # Action decorator with spec parser and a spec
    def test_decorator_types_and_spec(self):

        types = parse_schema_markdown('''\
typedef int(> 0) PositiveInteger
''')
        @action(types=types, spec='''\
action my_action
    input
        PositiveInteger value
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        self.assertTrue(isinstance(my_action, Action))
        self.assertTrue(isinstance(my_action, Request))

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'my_action')
        self.assertEqual(my_action.urls, (('POST', '/my_action'),))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'my_action')
        self.assertEqual(my_action.wsgi_response, False)

    # Action decorator with parser
    def test_decorator_parser(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        self.assertTrue(isinstance(my_action, Action))
        self.assertTrue(isinstance(my_action, Request))

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'my_action')
        self.assertEqual(my_action.urls, (('POST', '/my_action'),))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'my_action')
        self.assertEqual(my_action.wsgi_response, False)

    # Action decorator with spec with unknown action
    def test_decorator_spec_no_actions(self):

        with self.assertRaises(AssertionError) as cm_exc:
            @action(spec='''\
action my_action
''')
            def unused_my_action(unused_app, unused_req): # pragma: no cover
                pass
        self.assertEqual(str(cm_exc.exception), 'Unknown action "unused_my_action"')

    # Action decorator with spec with syntax errors
    def test_decorator_spec_error(self):
        with self.assertRaises(SchemaMarkdownParserError) as cm_exc:
            @action(spec='''\
asdfasdf
''')
            def unused_my_action(unused_app, unused_req): # pragma: no cover
                pass
        self.assertEqual(str(cm_exc.exception), ':1: error: Syntax error')

    # Action decorator with name and spec
    def test_decorator_named_spec(self):

        @action(name='theAction', spec='''\
action theActionOther
action theAction
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        self.assertTrue(isinstance(my_action, Action))
        self.assertTrue(isinstance(my_action, Request))

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'theAction')
        self.assertEqual(my_action.urls, (('POST', '/theAction'),))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'theAction')
        self.assertEqual(my_action.wsgi_response, False)

    def test_decorator_url_spec(self):

        # Action decorator with urls, custom response callback, and validate response bool
        @action(spec='''\
action my_action
    urls
        GET
        GET /
        *
        * /star
''')
        def my_action(unused_ctx, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'my_action')
        self.assertTupleEqual(my_action.urls, (('GET', '/my_action'), ('GET', '/'), (None, '/my_action'), (None, '/star')))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'my_action')
        self.assertFalse(my_action.wsgi_response)

    def test_decorator_url_spec_default(self):

        # Action decorator with urls, custom response callback, and validate response bool
        @action(spec='''\
action my_action
    urls
''')
        def my_action(unused_ctx, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)
        self.assertEqual(my_action.name, 'my_action')
        self.assertEqual(my_action.urls, (('POST', '/my_action'),))
        self.assertTrue(isinstance(my_action.model, dict))
        self.assertEqual(my_action.model['name'], 'my_action')
        self.assertFalse(my_action.wsgi_response)

    # Test successful action get
    def test_get(self):

        @action(spec='''\
action my_action
    urls
        GET
    query
        int a
        int b
    output
        int c
''')
        def my_action(unused_app, req):
            return {'c': req['a'] + req['b']}

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('GET', '/my_action', query_string='a=7&b=8')
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"c":15}')

    # Test successful action get
    def test_get_no_validate_output(self):

        @action(spec='''\
action my_action
    urls
        GET
    query
        int a
        int b
    output
        int c
''')
        def my_action(unused_app, req):
            return {'c': req['a'] + req['b']}

        app = Application()
        app.add_request(my_action)
        app.validate_output = False

        status, headers, response = app.request('GET', '/my_action', query_string='a=7&b=8')
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"c":15}')

    # Test successful action get with JSONP
    def test_get_jsonp(self):

        @action(jsonp='jsonp', spec='''\
action my_action
    urls
        GET
    query
        int a
        int b
    output
        int c
''')
        def my_action(unused_app, req):
            return {'c': req['a'] + req['b']}

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('GET', '/my_action', query_string='a=7&b=8&jsonp=foo')
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), 'foo({"c":15});')

    # Test successful action post
    def test_post(self):

        @action(spec='''\
action my_action
    urls
        *
        * /my/{a}
    path
        int a
    query
        int b
    input
        int c
    output
        int d
''')
        def my_action(unused_app, req):
            return {'d': req['a'] + req['b'] + req['c']}

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my/5', query_string='b=7', wsgi_input=b'{"c": 8}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"d":20}')

        # Mixed content and query string
        status, headers, response = app.request('POST', '/my_action', query_string='a=7', wsgi_input=b'{"b": 8}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Required member \'c\' missing (content)"}')

        # Mixed content and query string #2
        status, headers, response = app.request('POST', '/my_action', query_string='b=8', wsgi_input=b'{"c": 8}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Required member \'a\' missing (path)"}')

        # Mixed content and query string #3
        status, headers, response = app.request('POST', '/my/5', wsgi_input=b'{"c": 8}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Required member \'b\' missing (query string)"}')

    # Test successful action get with headers
    def test_headers(self):

        @action(spec='''\
action my_action
''')
        def my_action(ctx, unused_req):
            ctx.add_header('MyHeader', 'MyInitialValue')
            ctx.add_header('MyHeader', 'MyValue')
            return {}

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action')
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers, [('Content-Type', 'application/json'), ('MyHeader', 'MyValue')])
        self.assertEqual(response.decode('utf-8'), '{}')

    # Test successful action with custom response
    def test_custom_response(self):

        @action(wsgi_response=True, spec='''\
action my_action
    input
        string a
    output
        string b
''')
        def my_action(ctx, req):
            return ctx.response_text(HTTPStatus.OK, 'Hello ' + str(req['a'].upper()))

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{"a": "world"}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'text/plain')])
        self.assertEqual(response.decode('utf-8'), 'Hello WORLD')

    # Test action error response (invalid)
    def test_error_response(self):

        @action(spec='''\
action my_action
  errors
    MyError
''')
        def my_action(unused_app, unused_req):
            return {'error': 'MyError'}

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidOutput","message":"Unknown member \'error\'"}')

    # Test action error response with message
    def test_error_message(self):

        @action(spec='''\
action my_action
  errors
    MyError
''')
        def my_action(unused_app, unused_req):
            raise ActionError('MyError', message='My message')

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"MyError","message":"My message"}')

    # Test action raised-error response
    def test_error_raised(self):

        @action(spec='''\
action my_action
  errors
    MyError
''')
        def my_action(unused_app, unused_req):
            raise ActionError('MyError')

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"MyError"}')

    # Test action raised-error response with message
    def test_error_raised_message(self):

        @action(spec='''\
action my_action
  errors
    MyError
''')
        def my_action(unused_app, unused_req):
            raise ActionError('MyError', 'My message')

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"MyError","message":"My message"}')

    # Test action raised-error response with status
    def test_error_raised_status(self):

        @action(spec='''\
action my_action
  errors
    MyError
''')
        def my_action(unused_app, unused_req):
            raise ActionError('MyError', message='My message', status=HTTPStatus.NOT_FOUND)

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '404 Not Found')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"MyError","message":"My message"}')

    # Test action raising builtin error enum value
    def test_error_raise_builtin(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            raise ActionError('UnexpectedError', status=HTTPStatus.INTERNAL_SERVER_ERROR)

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}', environ=environ)
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"UnexpectedError"}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

    # Test action raising an unknown error enum value
    def test_error_unknown_error(self):

        @action(spec='''\
action my_action
  errors
    MyError
''')
        def my_action(unused_app, unused_req):
            raise ActionError('MyBadError')

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'),
                         '{"error":"InvalidOutput","member":"error","message":"Invalid value \'MyBadError\' (type \'str\') '
                         'for member \'error\', expected type \'my_action_errors\'"}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

        app.validate_output = False
        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"MyBadError"}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

    # Test action raising an undefined error enum value (no errors type)
    def test_error_undefined_error(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            raise ActionError('MyBadError')

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'),
                         '{"error":"InvalidOutput","member":"error","message":"Invalid value \'MyBadError\' (type \'str\') '
                         'for member \'error\', expected type \'my_action_errors\'"}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

        app.validate_output = False
        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"MyBadError"}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

    def test_error_inherited_error(self):

        @action(spec='''\
enum MyErrors
    Invalid

action my_action
    urls
        GET
    errors (MyErrors)
''')
        def my_action(unused_app, unused_req):
            raise ActionError('Invalid')

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_action')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"Invalid"}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

    # Test action query string decode error
    def test_error_invalid_query_string(self):

        @action(spec='''\
action my_action
    urls
        GET
    query
        int a
        int b
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('GET', '/my_action', query_string='a&b=1')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Invalid key/value pair \'a\'"}')

    # Test action long query string decode error
    def test_error_invalid_query_string_long(self):

        @action(spec='''\
action my_action
    urls
        GET
    query
        int a
        int b
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_action', query_string='a' * 2000 + '&b=1', environ=environ)
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Invalid key/value pair \'' + 'a' * 99 + '"}')
        self.assertRegex(
            environ['wsgi.errors'].getvalue(),
            r"^WARNING \[\d+ / \d+\] Error decoding query string for action 'my_action': 'a{999}$"
        )

    # Test action url arg
    def test_url_arg(self):

        @action(spec='''\
action my_action
    urls
        GET /my_action/{a}
    path
        int a
    query
        int b
    output
        int sum
''')
        def my_action(unused_app, req):
            self.assertEqual(req['a'], 5)
            return {'sum': req['a'] + req['b']}

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_action/5', query_string='b=7', environ=environ)
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"sum":12}')
        self.assertEqual(environ['wsgi.errors'].getvalue(), '')

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('GET', '/my_action/5', query_string='a=3&b=7', environ=environ)
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"InvalidInput","message":"Unknown member \'a\' (query string)"}')
        self.assertRegex(
            environ['wsgi.errors'].getvalue(),
            r"WARNING \[\d+ / \d+\] Invalid query string for action 'my_action': Unknown member 'a'"
        )

    # Test action with invalid json content
    def test_error_invalid_json(self):

        @action(spec='''\
action my_action
    input
        int a
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{a: 7}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(headers, [('Content-Type', 'application/json')])
        self.assertRegex(
            response.decode('utf-8'),
            '{"error":"InvalidInput","message":"Invalid request JSON:'
        )

    # Test action with invalid HTTP method
    def test_error_invalid_method(self):

        @action(spec='''\
action my_action
    input
        int a
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('FOO', '/my_action', wsgi_input=b'{"a": 7}')
        self.assertEqual(status, '405 Method Not Allowed')
        self.assertEqual(sorted(headers), [('Content-Type', 'text/plain')])
        self.assertEqual(response.decode('utf-8'), 'Method Not Allowed')

    # Test action with invalid input
    def test_error_invalid_input(self):

        @action(spec='''\
action my_action
    input
        string a
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{"a": 7}')
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'),
                         '{"error":"InvalidInput","member":"a","message":"Invalid value 7 (type \'int\') '
                         'for member \'a\', expected type \'string\' (content)"}')

    # Test action with invalid array input
    def test_error_invalid_input_array_query_string(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        environ = {'wsgi.errors': StringIO()}
        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'[]', query_string='foo=bar', environ=environ)
        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(
            response.decode('utf-8'),
            '{"error":"InvalidInput","message":"Invalid value [] (type \'list\'), expected type \'my_action_input\' (content)"}'
        )
        self.assertRegex(
            environ['wsgi.errors'].getvalue(),
            r"WARNING \[\d+ / \d+\] Invalid content for action 'my_action': "
            r"Invalid value \[\] \(type 'list'\), expected type 'my_action_input'"
        )

    # Test action with invalid output
    def test_error_invalid_output(self):

        @action(spec='''\
action my_action
  output
    int a
''')
        def my_action(unused_app, unused_req):
            return {'a': 'asdf'}

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'),
                         '{"error":"InvalidOutput","member":"a","message":"Invalid value \'asdf\' (type \'str\') '
                         'for member \'a\', expected type \'int\'"}')

    # Test action with invalid None output
    def test_error_none_output(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            pass

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '200 OK')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{}')

    # Test action with invalid array output
    def test_error_array_output(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            return []

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'),
                         '{"error":"InvalidOutput","message":"Invalid value [] (type \'list\'), '
                         'expected type \'my_action_output\'"}')

    # Test action with unexpected error
    def test_error_unexpected(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            # pylint: disable=broad-exception-raised
            raise Exception('My unexpected error')

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"UnexpectedError"}')

    # Test action HTTP post IO error handling
    def test_error_io(self):

        @action(spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            pass # pragma: no cover

        app = Application()
        app.add_request(my_action)

        class MyStream:
            @staticmethod
            def read():
                raise IOError('FAIL')

        status, headers, response = app.request('POST', '/my_action', environ={'wsgi.input': MyStream()},)
        self.assertEqual(status, '408 Request Timeout')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"IOError","message":"Error reading request content"}')

    # Test action JSON serialization error handling
    def test_error_json(self):

        class MyClass:
            pass

        @action(spec='''\
action my_action
  output
    float a
''')
        def my_action(unused_app, unused_req):
            return {'a': MyClass()}

        app = Application()
        app.add_request(my_action)
        app.validate_output = False

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'text/plain')])
        self.assertEqual(response, b'Internal Server Error')

    # Test action unexpected error response with custom response
    def test_error_unexpected_custom(self):

        @action(wsgi_response=True, spec='''\
action my_action
''')
        def my_action(unused_app, unused_req):
            # pylint: disable=broad-exception-raised
            raise Exception('FAIL')

        app = Application()
        app.add_request(my_action)

        status, headers, response = app.request('POST', '/my_action', wsgi_input=b'{}')
        self.assertEqual(status, '500 Internal Server Error')
        self.assertEqual(sorted(headers), [('Content-Type', 'application/json')])
        self.assertEqual(response.decode('utf-8'), '{"error":"UnexpectedError"}')
