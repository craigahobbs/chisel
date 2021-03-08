chisel
======

.. |badge-status| image:: https://img.shields.io/pypi/status/chisel
   :alt: PyPI - Status
   :target: https://pypi.python.org/pypi/chisel/

.. |badge-version| image:: https://img.shields.io/pypi/v/chisel
   :alt: PyPI
   :target: https://pypi.python.org/pypi/chisel/

.. |badge-license| image:: https://img.shields.io/github/license/craigahobbs/chisel
   :alt: GitHub
   :target: https://github.com/craigahobbs/chisel/blob/master/LICENSE

.. |badge-python| image:: https://img.shields.io/pypi/pyversions/chisel
   :alt: PyPI - Python Version
   :target: https://www.python.org/downloads/

|badge-status| |badge-version| |badge-license| |badge-python|

Chisel is a light-weight Python WSGI application framework with tools for building well-documented,
schema-validated JSON web APIs. Here are Chisel's features at a glance:

- Light-weight `WSGI <https://www.python.org/dev/peps/pep-3333/>`__ application framework
- Schema-validated `JSON <https://en.wikipedia.org/wiki/JSON>`__ web APIs
- Schema-accurate API documentation
- Written in pure `Python <https://python.org>`__
- Zero dependencies
- Python 3.7+


Links
-----

- `Documentation on GitHub Pages <https://craigahobbs.github.io/chisel/>`__
- `Package on pypi <https://pypi.org/project/chisel/>`__
- `Source code on GitHub <https://github.com/craigahobbs/chisel>`__


Overview
--------

To create a Chisel application, first create an
`Application <https://craigahobbs.github.io/chisel/app.html#chisel.Application>`__
object. Add functionality to your application by adding
`request <https://craigahobbs.github.io/chisel/app.html#chisel.request>`__
objects using the application's
`add_request <https://craigahobbs.github.io/chisel/app.html#chisel.Application.add_request>`__
method.

>>> from http import HTTPStatus
...
>>> @chisel.request(urls=[('GET', None)])
... def hello_world(environ, start_response):
...     ctx = environ[chisel.Context.ENVIRON_CTX]
...     return ctx.response_text(HTTPStatus.OK, 'Hello, World!')
...
>>> application = chisel.Application()
>>> application.add_request(hello_world)
>>> application.request('GET', '/hello_world')
('200 OK', [('Content-Type', 'text/plain')], b'Hello, World!')


Schema-Validated JSON APIs
--------------------------

Chisel provides the `action <https://craigahobbs.github.io/chisel/action.html#chisel.action>`__
decorator for easily implementing schema-validated JSON APIs.

>>> @chisel.action(spec='''
... # Sum a list of numbers
... action sum_numbers
...     urls
...        GET
...
...     query
...         # The list of numbers
...         float[len > 0] numbers
...
...     output
...         # The sum of the numbers
...         float sum
... ''')
... def sum_numbers(ctx, req):
...     return {'sum': sum(req['numbers'])}
...
>>> application = chisel.Application()
>>> application.add_request(sum_numbers)
>>> application.request('GET', '/sum_numbers', query_string='numbers.0=1&numbers.1=2&numbers.2=4')
('200 OK', [('Content-Type', 'application/json')], b'{"sum":7.0}')

Each action defines an action specification using the
`Chisel Specification Language <https://craigahobbs.github.io/chisel/spec.html>`__.
The action callback is passed two arguments, a request
`Context <https://craigahobbs.github.io/chisel/app.html#chisel.Context>`__
and the schema-validated request input dictionary. The input request dictionary is created by
combining the request's URL path parameters, query string parameters, and input JSON content
parameters.

If there is a schema validation error the appropriate error code is automatically returned.

>>> status, _, content_bytes = application.request('GET', '/sum_numbers')
>>> status
'400 Bad Request'

>>> content_bytes
b'{"error":"InvalidInput","message":"Required member \'numbers\' missing (query string)"}'


API Documentation
-----------------

You can add API documentation to your application by adding the Chisel documentation application
requests from
`create_doc_requests <https://craigahobbs.github.io/chisel/request.html#chisel.create_doc_requests>`__.

>>> application = chisel.Application()
>>> application.add_requests(chisel.create_doc_requests())

By default the documentation application is hosted at "/doc/". An example of of Chisel's documentation output is
available `here <https://craigahobbs.github.io/chisel/doc/#name=chisel_doc_request>`__.


Development
-----------

This project is developed using `Python Build <https://github.com/craigahobbs/python-build#readme>`__.
Refer to the Python Build `documentation <https://github.com/craigahobbs/python-build#make-targets>`__
for development instructions.
