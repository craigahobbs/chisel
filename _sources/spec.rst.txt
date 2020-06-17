.. _spec:

Chisel Specification Language
=============================

The Chisel specification language is a schema definition language for JSON APIs (see :func:`~chisel.action`). It is used
to define actions (JSON APIs), structure types, enumeration types, and typedef types. Specification parsing is done by
the :class:`~chisel.SpecParser` class. For example:

>>> parser = chisel.SpecParser('''
... # Sum a list of number pairs
... action sum_number_pairs
...     urls
...         GET
...     query
...         # The list of number pairs to sum
...         NumberPairList pairs
...     output
...         # The sum of the number pairs
...         NumberPair sum
...
...         # The size of the numbers in the number pair list
...         NumberSize size
...     errors
...         # The number pair list contains a negative number
...         NegativeNumber
...
... # Number range enumeration type
... enum NumberSize
...     # All numbers in the number pair list are small
...     Small
...
...     # Big numbers are present in the number pair list
...
... # A number pair structure
... struct NumberPair
...     # The first number of the pair
...     float first
...
...     # The second number of the pair
...     float second
...
... # A number pair list type
... typedef NumberPair[len > 0] NumberPairList
... ''')

User type objects are referenced by name in the parser's :attr:`~chisel.SpecParser.types` dictionary.

>>> sorted(parser.types.keys())
['NumberPair', 'NumberPairList', 'NumberSize', 'sum_number_pairs', 'sum_number_pairs_errors', 'sum_number_pairs_output', 'sum_number_pairs_query']


Comments
--------

Chisel specification language comments are lines beginning with the "#" character preceded only by whitespace. Comments
are interpreted as documentation markdown text lines to be applied to the next specification definition. If you want a
non-documentation comment use the "#-" form of commment.


Actions
-------

Actions are defined using the "action" keyword as shown above. Actions can contain any the following sections:

- "urls" - Contains a list of URL status/path specifications. By default actions are hosted as "POST" at the default URL
  path ("/my_action" if the action is named "my_action). URL specifications can have the follow forms:

  - ``GET`` - Match the HTTP request method with the default path
  - ``GET /path/`` - Match the HTTP request method and the exact path
  - ``* /path/`` - Match any HTTP request method and the exact path
  - ``GET /path/{name}`` - A URL path with a **path parameter** called "name". Path parameters should have a
    corresponding member in the "path" section.

- "path" - The path parameters structure type - see `Structure Types`_ below

- "query" - The query string parameters structure type - see `Structure Types`_ below

- "input" - The request JSON content parameters structure type - see `Structure Types`_ below

- "output" - The response JSON content parameters structure type - see `Structure Types`_ below

- "errors" - The action's custom error code enumeration type - see `Enumeration Types`_ below


Built-in Types
--------------

Chisel contains the following built-in types:

- ``bool`` - a boolean

- ``date`` - a :class:`~datetime.date`

- ``datetime`` - a :class:`~datetime.datetime`

- ``float`` - a floating point number

- ``int`` - an integer number

- ``object`` - a generic, unvalidated object (use sparingly)

- ``string`` - a string

- ``uuid`` - a :class:`~uuid.UUID`


Structure Types
----------------

Structure definitions contain zero or more member definitions. Member definitions may take the following forms:

>>> parser = chisel.SpecParser('''
... # My test struct
... struct MyStruct
...     # A required member
...     int a
...
...     # A member with type attributes
...     int(> 0) b
...
...     # An optional member
...     optional float c
...
...     # An optional, nullable member - value may be null
...     optional nullable string d
...
...     # An array member
...     bool[] e
...
...     # An array member with type attributes
...     string(len > 0)[len > 0] f
...
...     # A dictionary member
...     date{} g
...
...     # A dictionary member with attributes
...     date{len > 0} h
...
...     # A dictionary member with key type
...     MyEnum : uuid{} i
...
... enum MyEnum
...     A
...     B
... ''')
>>> [m['name'] for m in parser.types['MyStruct']['struct']['members']]
['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']


Typedefs
--------

Typedefs are a type definition and its associated attributes. For example:

>>> parser = chisel.SpecParser('''
... typedef int(> 0) PositiveInt
... ''')
>>> sorted(parser.types.keys())
['PositiveInt']


Type Attributes
---------------

Type attributes are used to add validation constraints to struct members and typedefs.

The following type attributes are available for ``int`` and ``float`` types:

- "< ``number``" - the value is less than a number

- "<= ``number``" - the value is less than or equal to a number

- "> ``number``" - the value is greater than a number

- ">= ``number``" - the value is less greater or equal to a number

- "== ``number``" - the value is equal to a number

The following type attributes are available for ``string``, array, and dictionary types:

- "len < ``integer``" - the length is less than an integer

- "len <= ``integer``" - the length is less than or equal to an integer

- "len > ``integer``" - the length is greater than an integer

- "len >= ``integer``" - the length is greater than or equal to an integer

- "len == ``integer``" - the length is equal to an integer


Enumeration Types
-----------------

An enumeration is a set of enumeration value strings. An enumeration member will validate only strings in the
enumeration value set.  For example:

>>> parser = chisel.SpecParser('''
... # My test enumeration
... enum TestEnum
...     # An enumeration value
...     Value1
...
...     # Another enumeration value
...     Value2
...
...     # A quoted enumeration value
...     "Value 3"
... ''')
>>> [v['name'] for v in parser.types['TestEnum']['enum']['values']]
['Value1', 'Value2', 'Value 3']


Inheritance
-----------

Structure types can multiple-inherit members from other structure types. For example:

>>> parser = chisel.SpecParser('''
... struct s1
...     int a
...
... struct s2
...     string b
...
... struct s3 (s1, s2)
...     datetime c
... ''')
>>> [m['name'] for m in parser.types['s3']['struct']['members']]
['a', 'b', 'c']

Structure inheritance also works for the ``path``, ``query``, ``input``, and ``output`` action structure sections.


>>> parser = chisel.SpecParser('''
... struct s1
...     int a
...
... struct s2
...     string b
...
... action my_action
...     query (s1, s2)
...         datetime c
... ''')
>>> [m['name'] for m in parser.types[parser.types['my_action']['action']['query']]['struct']['members']]
['a', 'b', 'c']


Likewise, enumeration types can inerit values from other enumeration types:

>>> parser = chisel.SpecParser('''
... enum e1
...     A
...
... enum e2
...     B
...
... enum e3 (e1, e2)
...     C
... ''')
>>> [v['name'] for v in parser.types['e3']['enum']['values']]
['A', 'B', 'C']


Type Validation
---------------

Chisel type model objects can be used to validate objects. For example:

>>> import uuid
>>> parser = chisel.SpecParser('''
... struct MyStruct
...     int a
...     uuid b
... ''')
>>> chisel.validate_type(parser.types, 'MyStruct', {'a': 5, 'b': uuid.UUID('8252121c-7f4f-4b6d-a7e5-f42ca6fdb64c')})
{'a': 5, 'b': UUID('8252121c-7f4f-4b6d-a7e5-f42ca6fdb64c')}

>>> try:
...     chisel.validate_type(parser.types, 'MyStruct', {'a': 5, 'b': 7})
... except chisel.ValidationError as exc:
...     str(exc)
"Invalid value 7 (type 'int') for member 'b', expected type 'uuid'"


Utilities
---------

.. autoclass:: chisel.SpecParser
   :members:

.. autofunction:: chisel.validate_type

.. autofunction:: chisel.validate_types

.. autofunction:: chisel.get_referenced_types

.. autofunction:: chisel.get_type_model

.. autoexception:: chisel.SpecParserError
   :members:

.. autoexception:: chisel.ValidationError
   :members:
