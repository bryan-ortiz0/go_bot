from __future__ import absolute_import
import codecs
from math import isinf, isnan

import six

from dlgo.gosgf import sgf_grammar
from six.moves import range

# In python 2, indexing a str gives one-character strings.
# In python 3, indexing a bytes gives ints.
if six.PY2:
    _bytestring_ord = ord
else:
    def identity(x):
        return x
    _bytestring_ord = identity

# Convert an encoding name to the form implied in the SGF spec
def normalise_charset_name(s):
    if not isinstance(s, six.text_type):
        s = s.decode('ascii')
    return (codecs.lookup(s).name.replace("_", "-").upper()
            .replace("ISO8859", "ISO-8859"))

# Convert a raw SGF Go Point, Move, or Stone value to coordinates
def interpret_go_point(s, size):
    if s == b"" or (s == b"tt" and size <= 19):
        return None
    # May propagate ValueError
    col_s, row_s = s
    col = _bytestring_ord(col_s) - 97  # 97 == ord("a")
    row = size - _bytestring_ord(row_s) + 96
    if not ((0 <= col < size) and (0 <= row < size)):
        raise ValueError
    return row, col

# Seralize a Go Point, Move, or Stone value
def serialise_go_point(move, size):
    if not 1 <= size <= 26:
        raise ValueError
    if move is None:
        # Prefer 'tt' where possible, for the sake of older code
        if size <= 19:
            return b"tt"
        else:
            return b""
    row, col = move
    if not ((0 <= col < size) and (0 <= row < size)):
        raise ValueError
    col_s = "abcdefghijklmnopqrstuvwxy"[col].encode('ascii')
    row_s = "abcdefghijklmnopqrstuvwxy"[size - row - 1].encode('ascii')
    return col_s + row_s


class _Context:
    def __init__(self, size, encoding):
        self.size = size
        self.encoding = encoding

# Convert a raw None value to a boolean
def interpret_none(s, context=None):
    return True

# Serialize a None value
def serialise_none(b, context=None):
    return b""

# Convert a raw Number value to the integer it represents
def interpret_number(s, context=None):
    return int(s, 10)

# Serialize a Number value
def serialise_number(i, context=None):
    return ("%d" % i).encode('ascii')

# Convert a raw Real value to the float it represents
def interpret_real(s, context=None):
    result = float(s)
    if isinf(result):
        raise ValueError("infinite")
    if isnan(result):
        raise ValueError("not a number")
    return result

# Serialize a Real value
def serialise_real(f, context=None):
    f = float(f)
    try:
        i = int(f)
    except OverflowError:
        # infinity
        raise ValueError
    if f == i:
        # avoid trailing '.0'; also avoid scientific notation for large numbers
        return str(i).encode('ascii')
    s = repr(f)
    if 'e-' in s:
        return "0".encode('ascii')
    return s.encode('ascii')

# Convert a raw Double value to an integer
def interpret_double(s, context=None):
    if s.strip() == b"2":
        return 2
    else:
        return 1

# Serialize a Double value
def serialise_double(i, context=None):
    if i == 2:
        return "2"
    return "1"

# Convert a raw Color value to a gomill color
def interpret_colour(s, context=None):
    colour = s.decode('ascii').lower()
    if colour not in ('b', 'w'):
        raise ValueError
    return colour

# Serialize a color value
def serialise_colour(colour, context=None):
    if colour not in ('b', 'w'):
        raise ValueError
    return colour.upper().encode('ascii')

# Common implementation for interpret_text and interpret_simpletext
def _transcode(s, encoding):
    # If encoding is UTF-8, we don't need to transcode, but still want to
    # report an error if it's not properly encoded.
    u = s.decode(encoding)
    if encoding == "UTF-8":
        return s
    else:
        return u.encode("utf-8")

# Convert a raw SimpleText value to a string
def interpret_simpletext(s, context):
    return _transcode(sgf_grammar.simpletext_value(s), context.encoding)

# Serialize a SimpleText value
def serialise_simpletext(s, context):
    if context.encoding != "UTF-8":
        s = s.decode("utf-8").encode(context.encoding)
    return sgf_grammar.escape_text(s)

# Convert a raw Text value to a string
def interpret_text(s, context):
    return _transcode(sgf_grammar.text_value(s), context.encoding)

# Serialize a Text value
def serialise_text(s, context):
    if context.encoding != "UTF-8":
        s = s.decode("utf-8").encode(context.encoding)
    return sgf_grammar.escape_text(s)

# Convert a raw SGF Point or Stone value to coordinates
def interpret_point(s, context):
    result = interpret_go_point(s, context.size)
    if result is None:
        raise ValueError
    return result

# Serialize a Point or Stone value
def serialise_point(point, context):
    if point is None:
        raise ValueError
    return serialise_go_point(point, context.size)

# Convert a raw SGF Move value to coordinates
def interpret_move(s, context):
    return interpret_go_point(s, context.size)

# Serialize a Move value
def serialise_move(move, context):
    return serialise_go_point(move, context.size)

# Convert a raw SGF list of Points to a set of coordinates
def interpret_point_list(values, context):
    result = set()
    for s in values:
        # No need to use parse_compose(), as \: would always be an error.
        p1, is_rectangle, p2 = s.partition(b":")
        if is_rectangle:
            top, left = interpret_point(p1, context)
            bottom, right = interpret_point(p2, context)
            if not (bottom <= top and left <= right):
                raise ValueError
            for row in range(bottom, top + 1):
                for col in range(left, right + 1):
                    result.add((row, col))
        else:
            pt = interpret_point(p1, context)
            result.add(pt)
    return result

# Serialize a list of Points, Moves, or Stones
def serialise_point_list(points, context):
    result = [serialise_point(point, context) for point in points]
    result.sort()
    return result

# Interpret an application (AP) property value
def interpret_AP(s, context):
    application, version = sgf_grammar.parse_compose(s)
    if version is None:
        version = b""
    return (interpret_simpletext(application, context),
            interpret_simpletext(version, context))

# Serialize an application (AP) property value
def serialise_AP(value, context):
    application, version = value
    return sgf_grammar.compose(serialise_simpletext(application, context),
                               serialise_simpletext(version, context))

# Interpert an arrow (AR) or line (LN) property value
def interpret_ARLN_list(values, context):
    result = []
    for s in values:
        p1, p2 = sgf_grammar.parse_compose(s)
        result.append((interpret_point(p1, context),
                       interpret_point(p2, context)))
    return result

# Serialize an arrow (AR) or line (LN) property value
def serialise_ARLN_list(values, context):
    return [b":".join((serialise_point(p1, context), serialise_point(p2, context)))
            for p1, p2 in values]

# Interpret a figure (FG) property value
def interpret_FG(s, context):
    if s == b"":
        return None
    flags, name = sgf_grammar.parse_compose(s)
    return int(flags), interpret_simpletext(name, context)

# Serialize a figure (FG) property value
def serialise_FG(value, context):
    if value is None:
        return b""
    flags, name = value
    return str(flags).encode('ascii') + b":" + serialise_simpletext(name, context)

# Interpret a label (LB) property value
def interpret_LB_list(values, context):
    result = []
    for s in values:
        point, label = sgf_grammar.parse_compose(s)
        result.append((interpret_point(point, context),
                       interpret_simpletext(label, context)))
    return result

# Serialize a label (LB) property value
def serialise_LB_list(values, context):
    return [b":".join((serialise_point(point, context), serialise_simpletext(text, context)))
            for point, text in values]

# Description of a property type
class Property_type:
    def __init__(self, interpreter, serialiser, uses_list,
                 allows_empty_list=False):
        self.interpreter = interpreter
        self.serialiser = serialiser
        self.uses_list = bool(uses_list)
        self.allows_empty_list = bool(allows_empty_list)


def _make_property_type(type_name, allows_empty_list=False):
    return Property_type(
        globals()["interpret_" + type_name],
        globals()["serialise_" + type_name],
        uses_list=(type_name.endswith("_list")),
        allows_empty_list=allows_empty_list)


_property_types_by_name = {
    'none': _make_property_type('none'),
    'number': _make_property_type('number'),
    'real': _make_property_type('real'),
    'double': _make_property_type('double'),
    'colour': _make_property_type('colour'),
    'simpletext': _make_property_type('simpletext'),
    'text': _make_property_type('text'),
    'point': _make_property_type('point'),
    'move': _make_property_type('move'),
    'point_list': _make_property_type('point_list'),
    'point_elist': _make_property_type('point_list', allows_empty_list=True),
    'stone_list': _make_property_type('point_list'),
    'AP': _make_property_type('AP'),
    'ARLN_list': _make_property_type('ARLN_list'),
    'FG': _make_property_type('FG'),
    'LB_list': _make_property_type('LB_list'),
}

P = _property_types_by_name

_property_types_by_ident = {
    b'AB': P['stone_list'],                 # setup         Add Black
    b'AE': P['point_list'],                 # setup         Add Empty
    b'AN': P['simpletext'],                 # game-info     Annotation
    b'AP': P['AP'],                         # root          Application
    b'AR': P['ARLN_list'],                  # -             Arrow
    b'AW': P['stone_list'],                 # setup         Add White
    b'B': P['move'],                        # move          Black
    b'BL': P['real'],                       # move          Black time left
    b'BM': P['double'],                     # move          Bad move
    b'BR': P['simpletext'],                 # game-info     Black rank
    b'BT': P['simpletext'],                 # game-info     Black team
    b'C': P['text'],                        # -             Comment
    b'CA': P['simpletext'],                 # root          Charset
    b'CP': P['simpletext'],                 # game-info     Copyright
    b'CR': P['point_list'],                 # -             Circle
    b'DD': P['point_elist'],                # - [inherit]   Dim points
    b'DM': P['double'],                     # -             Even position
    b'DO': P['none'],                       # move          Doubtful
    b'DT': P['simpletext'],                 # game-info     Date
    b'EV': P['simpletext'],                 # game-info     Event
    b'FF': P['number'],                     # root          Fileformat
    b'FG': P['FG'],                         # -             Figure
    b'GB': P['double'],                     # -             Good for Black
    b'GC': P['text'],                       # game-info     Game comment
    b'GM': P['number'],                     # root          Game
    b'GN': P['simpletext'],                 # game-info     Game name
    b'GW': P['double'],                     # -             Good for White
    b'HA': P['number'],                     # game-info     Handicap
    b'HO': P['double'],                     # -             Hotspot
    b'IT': P['none'],                       # move          Interesting
    b'KM': P['real'],                       # game-info     Komi
    b'KO': P['none'],                       # move          Ko
    b'LB': P['LB_list'],                    # -             Label
    b'LN': P['ARLN_list'],                  # -             Line
    b'MA': P['point_list'],                 # -             Mark
    b'MN': P['number'],                     # move          set move number
    b'N': P['simpletext'],                  # -             Nodename
    b'OB': P['number'],                     # move          OtStones Black
    b'ON': P['simpletext'],                 # game-info     Opening
    b'OT': P['simpletext'],                 # game-info     Overtime
    b'OW': P['number'],                     # move          OtStones White
    b'PB': P['simpletext'],                 # game-info     Player Black
    b'PC': P['simpletext'],                 # game-info     Place
    b'PL': P['colour'],                     # setup         Player to play
    b'PM': P['number'],                     # - [inherit]   Print move mode
    b'PW': P['simpletext'],                 # game-info     Player White
    b'RE': P['simpletext'],                 # game-info     Result
    b'RO': P['simpletext'],                 # game-info     Round
    b'RU': P['simpletext'],                 # game-info     Rules
    b'SL': P['point_list'],                 # -             Selected
    b'SO': P['simpletext'],                 # game-info     Source
    b'SQ': P['point_list'],                 # -             Square
    b'ST': P['number'],                     # root          Style
    b'SZ': P['number'],                     # root          Size
    b'TB': P['point_elist'],                # -             Territory Black
    b'TE': P['double'],                     # move          Tesuji
    b'TM': P['real'],                       # game-info     Timelimit
    b'TR': P['point_list'],                 # -             Triangle
    b'TW': P['point_elist'],                # -             Territory White
    b'UC': P['double'],                     # -             Unclear pos
    b'US': P['simpletext'],                 # game-info     User
    b'V': P['real'],                        # -             Value
    b'VW': P['point_elist'],                # - [inherit]   View
    b'W': P['move'],                        # move          White
    b'WL': P['real'],                       # move          White time left
    b'WR': P['simpletext'],                 # game-info     White rank
    b'WT': P['simpletext'],                 # game-info     White team
}
_text_property_type = P['text']

del P

# Convert property values between Python and SGF-string representations
class Presenter(_Context):
    def __init__(self, size, encoding):
        try:
            encoding = normalise_charset_name(encoding)
        except LookupError:
            raise ValueError("unknown encoding: %s" % encoding)
        _Context.__init__(self, size, encoding)
        self.property_types_by_ident = _property_types_by_ident.copy()
        self.default_property_type = _text_property_type

    # Return the Property_type for the specified PropIdent
    def get_property_type(self, identifier):
        return self.property_types_by_ident[identifier]

    # Specify the Property_type for a PropIdent
    def register_property(self, identifier, property_type):
        self.property_types_by_ident[identifier] = property_type

    # Forget the type for the specified PropIdent
    def deregister_property(self, identifier):
        del self.property_types_by_ident[identifier]

    # Specify the Property_type to use for unknown properties
    def set_private_property_type(self, property_type):
        self.default_property_type = property_type

    def _get_effective_property_type(self, identifier):
        try:
            return self.property_types_by_ident[identifier]
        except KeyError:
            result = self.default_property_type
            if result is None:
                raise ValueError("unknown property")
            return result

    # Variant of interpret() for explicitly specified type
    def interpret_as_type(self, property_type, raw_values):
        if not raw_values:
            raise ValueError("no raw values")
        if property_type.uses_list:
            if raw_values == [b""]:
                raw = []
            else:
                raw = raw_values
        else:
            if len(raw_values) > 1:
                raise ValueError("multiple values")
            raw = raw_values[0]
        return property_type.interpreter(raw, self)

    # Return a Python representation of a property value
    def interpret(self, identifier, raw_values):
        return self.interpret_as_type(
            self._get_effective_property_type(identifier), raw_values)

    # Variant of serialise() for explicitly specified type
    def serialise_as_type(self, property_type, value):
        serialised = property_type.serialiser(value, self)
        if property_type.uses_list:
            if serialised == []:
                if property_type.allows_empty_list:
                    return [b""]
                else:
                    raise ValueError("empty list")
            return serialised
        else:
            return [serialised]

    # Serialize a Python representation of a property value
    def serialise(self, identifier, value):
        return self.serialise_as_type(
            self._get_effective_property_type(identifier), value)