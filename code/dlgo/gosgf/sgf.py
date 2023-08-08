from __future__ import absolute_import
import datetime

import six

from dlgo.gosgf import sgf_grammar
from dlgo.gosgf import sgf_properties

__all__ = [
    'Node',
    'Sgf_game',
    'Tree_node',
]

# SGF node
class Node:
    def __init__(self, property_map, presenter):
        # Map identifier (PropIdent) -> nonempty list of raw values
        self._property_map = property_map
        self._presenter = presenter

    # Return the board size used to interpret property values
    def get_size(self):
        return self._presenter.size

    # Return the encoding used for raw property values
    def get_encoding(self):
        return self._presenter.encoding

    # Return the node's sgf_properties.Presenter
    def get_presenter(self):
        return self._presenter

    # Check whether the node has the specified property
    def has_property(self, identifier):
        return identifier in self._property_map

    # Find the properties defined for the node
    def properties(self):
        return list(self._property_map.keys())

    # Return the raw values of the specified property
    def get_raw_list(self, identifier):
        return self._property_map[identifier]

    # Return a single raw value of the specified property
    def get_raw(self, identifier):
        return self._property_map[identifier][0]

    # Return the raw values of all properties as a dictionary
    def get_raw_property_map(self):
        return self._property_map

    def _set_raw_list(self, identifier, values):
        if identifier == b"SZ" and \
                values != [str(self._presenter.size).encode(self._presenter.encoding)]:
            raise ValueError("changing size is not permitted")
        self._property_map[identifier] = values

    # Remove the specified property
    def unset(self, identifier):
        if identifier == b"SZ" and self._presenter.size != 19:
            raise ValueError("changing size is not permitted")
        del self._property_map[identifier]

    # Set the raw values of the specified property
    def set_raw_list(self, identifier, values):
        if not sgf_grammar.is_valid_property_identifier(identifier):
            raise ValueError("ill-formed property identifier")
        values = list(values)
        if not values:
            raise ValueError("empty property list")
        for value in values:
            if not sgf_grammar.is_valid_property_value(value):
                raise ValueError("ill-formed raw property value")
        self._set_raw_list(identifier, values)

    # Set the specified property to a single raw value
    def set_raw(self, identifier, value):
        if not sgf_grammar.is_valid_property_identifier(identifier):
            raise ValueError("ill-formed property identifier")
        if not sgf_grammar.is_valid_property_value(value):
            raise ValueError("ill-formed raw property value")
        self._set_raw_list(identifier, [value])

    # Return the interpreted value of the specified property
    def get(self, identifier):
        return self._presenter.interpret(
            identifier, self._property_map[identifier])

    # Set the value of the specified property
    def set(self, identifier, value):
        self._set_raw_list(
            identifier, self._presenter.serialise(identifier, value))

    # Return the raw value of the move from a node
    def get_raw_move(self):
        values = self._property_map.get(b"B")
        if values is not None:
            colour = "b"
        else:
            values = self._property_map.get(b"W")
            if values is not None:
                colour = "w"
            else:
                return None, None
        return colour, values[0]

    # Retrieve the move from a node
    def get_move(self):
        colour, raw = self.get_raw_move()
        if colour is None:
            return None, None
        return (colour,
                sgf_properties.interpret_go_point(raw, self._presenter.size))

    # Retrieve Add Black / Add White / Add Empty properties from a node
    def get_setup_stones(self):
        try:
            bp = self.get(b"AB")
        except KeyError:
            bp = set()
        try:
            wp = self.get(b"AW")
        except KeyError:
            wp = set()
        try:
            ep = self.get(b"AE")
        except KeyError:
            ep = set()
        return bp, wp, ep

    # Check whether the node has any AB/AW/AE properties
    def has_setup_stones(self):
        d = self._property_map
        return (b"AB" in d or b"AW" in d or b"AE" in d)

    # Set the B or W property
    def set_move(self, colour, move):
        if colour not in ('b', 'w'):
            raise ValueError
        if b'B' in self._property_map:
            del self._property_map[b'B']
        if b'W' in self._property_map:
            del self._property_map[b'W']
        self.set(colour.upper().encode('ascii'), move)

    # Set Add Black / Add White / Add Empty properties
    def set_setup_stones(self, black, white, empty=None):
        if b'AB' in self._property_map:
            del self._property_map[b'AB']
        if b'AW' in self._property_map:
            del self._property_map[b'AW']
        if b'AE' in self._property_map:
            del self._property_map[b'AE']
        if black:
            self.set(b'AB', black)
        if white:
            self.set(b'AW', white)
        if empty:
            self.set(b'AE', empty)

    # Add or extend the node's comment
    def add_comment_text(self, text):
        if self.has_property(b'C'):
            self.set(b'C', self.get(b'C') + b"\n\n" + text)
        else:
            self.set(b'C', text)

    def __str__(self):
        encoding = self.get_encoding()

        def format_property(ident, values):
            return ident.decode(encoding) + "".join(
                "[%s]" % s.decode(encoding) for s in values)
        return "\n".join(
            format_property(ident, values)
            for (ident, values) in sorted(self._property_map.items())) \
            + "\n"

# A node embedded in an SGF game
class Tree_node(Node):
    def __init__(self, parent, properties):
        self.owner = parent.owner
        self.parent = parent
        self._children = []
        Node.__init__(self, properties, parent._presenter)

    def _add_child(self, node):
        self._children.append(node)

    def __len__(self):
        return len(self._children)

    def __getitem__(self, key):
        return self._children[key]

    def index(self, child):
        return self._children.index(child)

    # Create a new Tree_node and add it as this node's last child
    def new_child(self, index=None):
        child = Tree_node(self, {})
        if index is None:
            self._children.append(child)
        else:
            self._children.insert(index, child)
        return child

    # Remove this node from its parent
    def delete(self):
        if self.parent is None:
            raise ValueError("can't remove the root node")
        self.parent._children.remove(self)

    # Mov ethis node to a new place in the tree
    def reparent(self, new_parent, index=None):
        if new_parent.owner != self.owner:
            raise ValueError("new parent doesn't belong to the same game")
        n = new_parent
        while True:
            if n == self:
                raise ValueError("would create a loop")
            n = n.parent
            if n is None:
                break
        # self.parent is not None because moving the root would create a loop.
        self.parent._children.remove(self)
        self.parent = new_parent
        if index is None:
            new_parent._children.append(self)
        else:
            new_parent._children.insert(index, self)

    # Find the nearest ancesor-or-self containing the specified property
    def find(self, identifier):
        node = self
        while node is not None:
            if node.has_property(identifier):
                return node
            node = node.parent
        return None

    # Return the value of a property, defined at this node or an ancestor
    def find_property(self, identifier):
        node = self.find(identifier)
        if node is None:
            raise KeyError
        return node.get(identifier)

# Variant of Tree_node used for a game root
class _Root_tree_node(Tree_node):
    def __init__(self, property_map, owner):
        self.owner = owner
        self.parent = None
        self._children = []
        Node.__init__(self, property_map, owner.presenter)

# Variant of _Root_tree_node used with 'loaded' Sgf_games
class _Unexpanded_root_tree_node(_Root_tree_node):
    def __init__(self, owner, coarse_tree):
        _Root_tree_node.__init__(self, coarse_tree.sequence[0], owner)
        self._coarse_tree = coarse_tree

    def _expand(self):
        sgf_grammar.make_tree(
            self._coarse_tree, self, Tree_node, Tree_node._add_child)
        delattr(self, '_coarse_tree')
        self.__class__ = _Root_tree_node

    def __len__(self):
        self._expand()
        return self.__len__()

    def __getitem__(self, key):
        self._expand()
        return self.__getitem__(key)

    def index(self, child):
        self._expand()
        return self.index(child)

    def new_child(self, index=None):
        self._expand()
        return self.new_child(index)

    def _main_sequence_iter(self):
        presenter = self._presenter
        for properties in sgf_grammar.main_sequence_iter(self._coarse_tree):
            yield Node(properties, presenter)

# SGF game tree
class Sgf_game:
    def __new__(cls, size, encoding="UTF-8", *args, **kwargs):
        # To complete initialisation after this, you need to set 'root'.
        if not 1 <= size <= 26:
            raise ValueError("size out of range: %s" % size)
        game = super(Sgf_game, cls).__new__(cls)
        game.size = size
        game.presenter = sgf_properties.Presenter(size, encoding)
        return game

    def __init__(self, *args, **kwargs):
        self.root = _Root_tree_node({}, self)
        self.root.set_raw(b'FF', b"4")
        self.root.set_raw(b'GM', b"1")
        self.root.set_raw(b'SZ', str(self.size).encode(self.presenter.encoding))
        # Read the encoding back so we get the normalised form
        self.root.set_raw(b'CA', self.presenter.encoding.encode('ascii'))

    # Alternative constructor: create an Sgf_game from the parser outpu
    @classmethod
    def from_coarse_game_tree(cls, coarse_game, override_encoding=None):
        try:
            size_s = coarse_game.sequence[0][b'SZ'][0]
        except KeyError:
            size = 19
        else:
            try:
                size = int(size_s)
            except ValueError:
                raise ValueError("bad SZ property: %s" % size_s)
        if override_encoding is None:
            try:
                encoding = coarse_game.sequence[0][b'CA'][0]
            except KeyError:
                encoding = b"ISO-8859-1"
        else:
            encoding = override_encoding
        game = cls.__new__(cls, size, encoding)
        game.root = _Unexpanded_root_tree_node(game, coarse_game)
        if override_encoding is not None:
            game.root.set_raw(b"CA", game.presenter.encoding.encode('ascii'))
        return game

    # Alternative constructor: read a single Sgf_game from a string
    @classmethod
    def from_string(cls, s, override_encoding=None):
        if not isinstance(s, six.binary_type):
            s = s.encode('ascii')
        coarse_game = sgf_grammar.parse_sgf_game(s)
        return cls.from_coarse_game_tree(coarse_game, override_encoding)

    # Serialise the SGF data as a string
    def serialise(self, wrap=79):
        try:
            encoding = self.get_charset()
        except ValueError:
            raise ValueError("unsupported charset: %r" %
                             self.root.get_raw_list(b"CA"))
        coarse_tree = sgf_grammar.make_coarse_game_tree(
            self.root, lambda node: node, Node.get_raw_property_map)
        serialised = sgf_grammar.serialise_game_tree(coarse_tree, wrap)
        if encoding == self.root.get_encoding():
            return serialised
        else:
            return serialised.decode(self.root.get_encoding()).encode(encoding)

    # Return the property presenter
    def get_property_presenter(self):
        return self.presenter

    # Return the root node (as a Tree_node)
    def get_root(self):
        return self.root

    # Return the last node in the 'leftmost' variation (as a Tree_node)
    def get_last_node(self):
        node = self.root
        while node:
            node = node[0]
        return node

    # Return the 'leftmost' variation
    def get_main_sequence(self):
        node = self.root
        result = [node]
        while node:
            node = node[0]
            result.append(node)
        return result

    # Return the 'leftmost' variation below the specified node
    def get_main_sequence_below(self, node):
        if node.owner is not self:
            raise ValueError("node doesn't belong to this game")
        result = []
        while node:
            node = node[0]
            result.append(node)
        return result

    # Return the partial variation leading to the specified node
    def get_sequence_above(self, node):
        if node.owner is not self:
            raise ValueError("node doesn't belong to this game")
        result = []
        while node.parent is not None:
            node = node.parent
            result.append(node)
        result.reverse()
        return result

    # Provide the 'leftmost' variation as an iterator
    def main_sequence_iter(self):
        if isinstance(self.root, _Unexpanded_root_tree_node):
            return self.root._main_sequence_iter()
        return iter(self.get_main_sequence())

    # Create a new Tree_node and add to the 'leftmost' variation
    def extend_main_sequence(self):
        return self.get_last_node().new_child()

    # Return the board_size as an integer
    def get_size(self):
        return self.size

    # Return the effective value of the CA root property
    def get_charset(self):
        try:
            s = self.root.get(b"CA")
        except KeyError:
            return "ISO-8859-1"
        try:
            return sgf_properties.normalise_charset_name(s)
        except LookupError:
            raise ValueError("no codec available for CA %s" % s)

    # Return the komi as a float
    def get_komi(self):
        try:
            return self.root.get(b"KM")
        except KeyError:
            return 0.0

    # Return the number of handicap stones as a small integer
    def get_handicap(self):
        try:
            handicap = self.root.get(b"HA")
        except KeyError:
            return None
        if handicap == 0:
            handicap = None
        elif handicap == 1:
            raise ValueError
        return handicap

    # Return the name of the specified player
    def get_player_name(self, colour):
        try:
            return self.root.get(
                {'b': b'PB', 'w': b'PW'}[colour]).decode(self.presenter.encoding)
        except KeyError:
            return None

    # Return the color of the winning player
    def get_winner(self):
        try:
            colour = self.root.get(b"RE").decode(self.presenter.encoding)[0].lower()
        except LookupError:
            return None
        if colour not in ("b", "w"):
            return None
        return colour

    # Set the DT property to a single date
    def set_date(self, date=None):
        if date is None:
            date = datetime.date.today()
        self.root.set('DT', date.strftime("%Y-%m-%d"))