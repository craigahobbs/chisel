Schemas
=======

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


Reference
---------

.. autofunction:: chisel.validate_type

.. autoexception:: chisel.ValidationError
   :members:

.. autofunction:: chisel.get_referenced_types

.. autofunction:: chisel.get_type_model

.. autofunction:: chisel.validate_types
