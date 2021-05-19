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
   :target: https://github.com/craigahobbs/chisel/blob/main/LICENSE

.. |badge-python| image:: https://img.shields.io/pypi/pyversions/chisel
   :alt: PyPI - Python Version
   :target: https://www.python.org/downloads/

|badge-status| |badge-version| |badge-license| |badge-python|

**Chisel** is a light-weight Python WSGI application framework built for creating
well-documented, schema-validated JSON web APIs. Here are its features at a glance:

- Light-weight WSGI application framework
- Schema-validated JSON APIs
- API documentation with Markdown support
- Written in pure Python
- Zero dependencies


Links
-----

- `Documentation on GitHub Pages <https://craigahobbs.github.io/chisel/>`__
- `Package on pypi <https://pypi.org/project/chisel/>`__
- `Source code on GitHub <https://github.com/craigahobbs/chisel>`__


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

Each action defines an ``action`` definition using
`Schema Markdown <https://craigahobbs.github.io/schema-markdown/schema-markdown.html>`__.
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
available `here <https://craigahobbs.github.io/schema-markdown-js/doc/>`__.


Development
-----------

This project is developed using `Python Build <https://github.com/craigahobbs/python-build#readme>`__.
