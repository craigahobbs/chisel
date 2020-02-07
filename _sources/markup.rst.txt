HTML & SVG
==========

>>> from chisel import Element
>>> root = Element('html', children=[
...     Element('head', children=[
...         Element('meta', closed=False, charset='UTF-8'),
...         Element('title', inline=True, children=Element('The Title', text=True)),
...         Element('style', _type='text/css', children=Element('a { color: #004B91; }', text_raw=True))
...     ]),
...     Element('body', _class='chsl-index-body', children=[
...         Element('h1', inline=True, children=Element('The Title', text=True))
...     ])
... ])
>>> print(root.serialize())
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>The Title</title>
    <style type="text/css">
a { color: #004B91; }
    </style>
  </head>
  <body class="chsl-index-body">
    <h1>The Title</h1>
  </body>
</html>

.. autoclass:: chisel.Element
   :members:
