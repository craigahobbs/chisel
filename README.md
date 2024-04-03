# chisel

[![PyPI - Status](https://img.shields.io/pypi/status/chisel)](https://pypi.org/project/chisel/)
[![PyPI](https://img.shields.io/pypi/v/chisel)](https://pypi.org/project/chisel/)
[![GitHub](https://img.shields.io/github/license/craigahobbs/chisel)](https://github.com/craigahobbs/chisel/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/chisel)](https://pypi.org/project/chisel/)

Chisel is a light-weight Python WSGI application framework built for creating well-documented,
schema-validated JSON web APIs.


## Links

- [API Documentation](https://craigahobbs.github.io/chisel/)
- [Source code](https://github.com/craigahobbs/chisel)


## JSON APIs

Chisel provides the [action](https://craigahobbs.github.io/chisel/action.html#chisel.action)
decorator for easily implementing schema-validated JSON APIs.

~~~ python
@chisel.action(spec='''
# Sum a list of numbers
action sum_numbers
    urls
       GET

    query
        # The list of numbers
        float[len > 0] numbers

    output
        # The sum of the numbers
        float sum
''')
def sum_numbers(ctx, req):
    return {'sum': sum(req['numbers'])}

application = chisel.Application()
application.add_request(sum_numbers)
application.request('GET', '/sum_numbers', query_string='numbers.0=1&numbers.1=2&numbers.2=4')

('200 OK', [('Content-Type', 'application/json')], b'{"sum":7.0}')
~~~

Each action defines an ``action`` definition using
[Schema Markdown](https://craigahobbs.github.io/schema-markdown-js/language/).
The action callback is passed two arguments, a request
[Context](https://craigahobbs.github.io/chisel/app.html#chisel.Context)
and the schema-validated request input dictionary. The input request dictionary is created by
combining the request's URL path parameters, query string parameters, and input JSON content
parameters.

If there is a schema validation error the appropriate error code is automatically returned.

~~~ python
status, _, content_bytes = application.request('GET', '/sum_numbers')

'400 Bad Request'
b'{"error":"InvalidInput","message":"Required member \'numbers\' missing (query string)"}'
~~~


## API Documentation

You can add API documentation to your application by adding the Chisel documentation application
requests from
[create_doc_requests](https://craigahobbs.github.io/chisel/request.html#chisel.create_doc_requests).

~~~ python
application = chisel.Application()
application.add_requests(chisel.create_doc_requests())
~~~

By default the documentation application is hosted at "/doc/". An example of of Chisel's documentation output is
available [here](https://craigahobbs.github.io/chisel/example/#var.vName='chisel_doc_request').


## Development

This package is developed using [python-build](https://github.com/craigahobbs/python-build#readme).
It was started using [python-template](https://github.com/craigahobbs/python-template#readme) as follows:

~~~ sh
template-specialize python-template/template/ chisel/ -k package chisel -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k nomain 1
~~~
