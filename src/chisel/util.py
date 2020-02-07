# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from html import escape
import json
import re
from urllib.parse import quote, unquote
from uuid import UUID
from xml.sax.saxutils import quoteattr


class JSONEncoder(json.JSONEncoder):
    """
    A :class:`~json.JSONEncoder` sub-class with support for :class:`~datetime.datetime`, :class:`~datetime.date`, :class:`~decimal.Decimal`,
    and :class:`~uuid.UUID` objects.
    """

    __slots__ = ()

    def default(self, o): # pylint: disable=method-hidden
        """
        The override of the :meth:`~json.JSONEncoder.default` method to add support for :class:`~datetime.datetime`,
        :class:`~datetime.date`, :class:`~decimal.Decimal`, and :class:`~uuid.UUID` objects.
        """

        if isinstance(o, datetime):
            return (o if o.tzinfo else o.replace(tzinfo=timezone.utc)).isoformat()
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


class Element:
    """
    A structured markup language document model element.

    :param str name: The element name.
    :param bool text: If ``True``, the element :attr:`name` is the text of a text element.
    :param bool text_raw: If ``True``, the element :attr:`name` is the raw text of a text element.
    :param bool closed: If ``True``, the element is "closed".
    :param bool inline: If ``True``, the element and its children serialized in-line.
    :param children: A list of child :class:`Element` objects (or list objects or ``None``),
                     or :class:`Element` objects, or ``None``.
    :type children: list or Element
    :param dict attrs: The element's attributes. For built-ins (e.g. ``'class'``), prefix the attribute name with an
                       underscore (e.g. ``'_class'``). Key/value pairs with a value of ``None`` are ignored.
    """

    __slots__ = ('name', 'text', 'text_raw', 'closed', 'inline', 'children', 'attrs')

    def __init__(self, name, text=False, text_raw=False, closed=True, inline=False, children=None, **attrs):

        #: :class:`str` - The element name.
        self.name = name

        #: :class:`bool` - If ``True``, the element :attr:`name` is the text of a text element.
        self.text = text

        #: :class:`bool` - If ``True``, the element :attr:`name` is the raw text of a text element.
        self.text_raw = text_raw

        #: :class:`bool` - If ``True``, the element is "closed".
        self.closed = closed

        #: :class:`bool` - If ``True``, the element and its children serialized in-line.
        self.inline = inline

        #: :class:`list` or :class:`Element` - A list of child :class:`Element` objects (or list objects or ``None``),
        #: or :class:`Element` objects, or ``None``.
        self.children = children

        #: :class:`dict` - The element's attributes. For built-ins (e.g. ``'class'``), prefix the attribute name with an
        #: underscore (e.g. ``'_class'``). Key/value pairs with a value of ``None`` are ignored.
        self.attrs = attrs

    def serialize(self, indent='  ', html=True):
        """
        Serialize an element and its children.

        :param str indent: The indent string, or ``None``.
        :param bool html: If ``True``, include the `HTML5 <https://en.wikipedia.org/wiki/HTML5>`_ doctype in the serialized element.
        :rtype: str
        """

        return ''.join(self._serialize_chunks(indent, html, 0, False))

    def _serialize_chunks(self, indent, html, indent_index, inline):

        # HTML5 doctype, if requested
        if html and indent_index == 0:
            yield '<!doctype html>\n'

        # Initial newline and indent as necessary...
        if indent is not None and not inline and indent_index != 0:
            yield '\n'
            if indent and not self.text and not self.text_raw:
                yield indent * indent_index

        # Text element?
        if self.text:
            yield escape(self.name)
            return
        if self.text_raw:
            yield self.name
            return

        # Element open
        yield '<' + self.name
        for attr_key, attr_value in sorted((key_value[0].lstrip('_'), key_value[1]) for key_value in self.attrs.items()):
            if attr_value is not None:
                yield ' ' + attr_key + '=' + quoteattr(attr_value)

        # Child elements
        has_children = False
        for child in self._iterate_children_helper(self.children):
            if not has_children:
                has_children = True
                yield '>'
            yield from child._serialize_chunks(indent, html, indent_index + 1, inline or self.inline) # pylint: disable=protected-access

        # Element close
        if not has_children:
            yield ' />' if self.closed else '>'
            return
        if indent is not None and not inline and not self.inline:
            yield '\n' + indent * indent_index
        yield '</' + self.name + '>'

    @classmethod
    def _iterate_children_helper(cls, children):
        if isinstance(children, Element):
            yield children
        elif children is not None:
            for child in children:
                if isinstance(child, Element):
                    yield child
                elif child is not None:
                    yield from cls._iterate_children_helper(child)


# ISO 8601 regexes
RE_ISO8601_DATE = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s*$')
RE_ISO8601_DATETIME = re.compile(r'^\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
                                 r'(T(?P<hour>\d{2})(:(?P<min>\d{2})(:(?P<sec>\d{2})([.,](?P<fracsec>\d{1,7}))?)?)?'
                                 r'(Z|(?P<offsign>[+-])(?P<offhour>\d{2})(:?(?P<offmin>\d{2}))?))?\s*$')


def parse_iso8601_date(string):
    """
    Parse an `ISO-8601 <https://en.wikipedia.org/wiki/ISO_8601>`_ date string.

    :param str string: The `ISO-8601`_ date string.
    :rtype: ~datetime.date

    >>> import chisel
    >>> chisel.parse_iso8601_date('2020-02-04')
    datetime.date(2020, 2, 4)
    """

    # Match ISO 8601?
    match = RE_ISO8601_DATE.search(string)
    if not match:
        raise ValueError('Expected ISO 8601 date')

    # Extract ISO 8601 components
    year = int(match.group('year'))
    month = int(match.group('month'))
    day = int(match.group('day'))

    return date(year, month, day)


def parse_iso8601_datetime(string):
    """
    Parse an `ISO-8601 <https://en.wikipedia.org/wiki/ISO_8601>`_ date/time string.

    :param str string: The `ISO-8601`_ date/time string.
    :rtype: ~datetime.datetime

    >>> import chisel
    >>> chisel.parse_iso8601_datetime('2020-02-04T07:41:00+07:00')
    datetime.datetime(2020, 2, 4, 0, 41, tzinfo=datetime.timezone.utc)
    """

    # Match ISO 8601?
    match = RE_ISO8601_DATETIME.search(string)
    if not match:
        raise ValueError('Expected ISO 8601 date/time')

    # Extract ISO 8601 components
    year = int(match.group('year'))
    month = int(match.group('month'))
    day = int(match.group('day'))
    hour = int(match.group('hour')) if match.group('hour') else 0
    minute = int(match.group('min')) if match.group('min') else 0
    sec = int(match.group('sec')) if match.group('sec') else 0
    microsec = int(float('.' + match.group('fracsec')) * 1000000) if match.group('fracsec') else 0
    offhour = int(match.group('offsign') + match.group('offhour')) if match.group('offhour') else 0
    offmin = int(match.group('offsign') + match.group('offmin')) if match.group('offmin') else 0

    return datetime(year, month, day, hour, minute, sec, microsec, timezone.utc) - timedelta(hours=offhour, minutes=offmin)


def encode_query_string(obj, encoding='utf-8'):
    """
    TODO
    """

    return '&'.join(k + '=' + v for k, v in _encode_query_string_items(obj, None, encoding))

def _encode_query_string_items(obj, parent, encoding):
    if isinstance(obj, dict):
        if obj:
            for member, value in sorted(obj.items()):
                member_quoted = quote(str(member), encoding=encoding) if encoding else str(member)
                parent_member = parent + '.' + member_quoted if parent else member_quoted
                yield from _encode_query_string_items(value, parent_member, encoding)
        elif parent:
            yield parent, ''
    elif isinstance(obj, (list, tuple)):
        if obj:
            for idx, value in enumerate(obj):
                parent_member = parent + '.' + str(idx) if parent else str(idx)
                yield from _encode_query_string_items(value, parent_member, encoding)
        elif parent:
            yield parent, ''
    else:
        if isinstance(obj, bool):
            yield parent, 'true' if obj else 'false' # quote safe
        elif isinstance(obj, int):
            yield parent, str(obj) # quote safe
        elif isinstance(obj, datetime):
            if not obj.tzinfo:
                obj = obj.replace(tzinfo=timezone.utc)
            yield parent, quote(obj.isoformat(), encoding=encoding) if encoding else obj.isoformat()
        elif isinstance(obj, date):
            yield parent, obj.isoformat() # quote safe
        elif isinstance(obj, UUID):
            yield parent, str(obj) # quote safe
        elif obj is None:
            yield parent, 'null' # quote safe
        else: # str, float
            yield parent, quote(str(obj), encoding=encoding) if encoding else str(obj)


def decode_query_string(query_string, encoding='utf-8'):
    """
    TODO
    """

    return _decode_query_string_items(
        (key_value_str.split('=') for key_value_str in query_string.split('&') if key_value_str),
        encoding
    )

def _decode_query_string_items(query_string_items, encoding):

    # Build the object
    result = [None]
    for key_value in query_string_items:

        # Split the key/value string
        try:
            key_str, value_str = key_value
            value = unquote(value_str, encoding=encoding) if encoding else value_str
        except ValueError:
            raise ValueError(f"Invalid key/value pair {'='.join(key_value)!r:.1000s}")

        # Find/create the object on which to set the value
        parent = result
        key_parent = 0
        for key in (unquote(key, encoding=encoding) if encoding else key for key in key_str.split('.')):
            obj = parent[key_parent]

            # Array key?  First "key" of an array must start with "0".
            if isinstance(obj, list) or (obj is None and key == '0'):

                # Create this key's container, if necessary
                if obj is None:
                    obj = parent[key_parent] = []

                # Create the index for this key
                try:
                    key = int(key)
                except:
                    raise ValueError(f"Invalid key/value pair {'='.join(key_value)!r:.1000s}")
                if key == len(obj):
                    obj.append(None)
                elif key < 0 or key > len(obj):
                    raise ValueError(f"Invalid key/value pair {'='.join(key_value)!r:.1000s}")

            # Dictionary key
            else:

                # Create this key's container, if necessary
                if obj is None:
                    obj = parent[key_parent] = {}

                # Create the index for this key
                if obj.get(key) is None:
                    obj[key] = None

            # Update the parent object and key
            parent = obj
            key_parent = key

        # Set the value
        if parent[key_parent] is not None:
            raise ValueError(f"Duplicate key {'='.join(key_value)!r:.1000s}")
        parent[key_parent] = value

    return result[0] if (result[0] is not None) else {}
