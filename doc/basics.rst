.. _Getting Started:

Getting Started
===============

Here's an example of a simple Chisel application:

>>> import chisel
...
>>> # Define your action
... @chisel.action(spec='''\
...
... # Sum a list of numbers.
... action sum_numbers
...     url
...         GET /sum
...
...     query
...         # The list of numbers.
...         float[len > 0] numbers
...
...     output
...         # The sum of the numbers.
...         float sum
... ''')
... def sum_numbers(ctx, req):
...    return {'sum': sum(req['numbers'])}
...
>>> # Create the chisel application
... application = chisel.Application()
...
>>> # Add API documentation
... application.add_requests(chisel.get_doc_requests())
...
>>> # Add our requests / actions
... application.add_request(sum_numbers)

Let's try a request:

>>> print(application.request(
...     'GET',
...     '/sum',
...     query_string='numbers.0=1&numbers.1=2&numbers.2=2.5'
... ))
('200 OK', [('Content-Type', 'application/json')], b'{"sum":5.5}')

Let's some bad requests:

>>> print(application.request(
...     'GET',
...     '/sum'
... ))
('400 Bad Request', [('Content-Type', 'application/json')], b'{"error":"InvalidInput","message":"Required member \'numbers\' missing (query string)"}')

>>> print(application.request(
...     'GET',
...     '/sum',
...     query_string='numbers.0=1&numbers.1=2&numbers.2=asdf'
... ))
('400 Bad Request', [('Content-Type', 'application/json')], b'{"error":"InvalidInput","member":"numbers[2]","message":"Invalid value \'asdf\' (type \'str\') for member \'numbers[2]\', expected type \'float\' (query string)"}')

Notice that chisel does all of the input validation for you based on the
:class:`~chisel.Action` specification's schema.
