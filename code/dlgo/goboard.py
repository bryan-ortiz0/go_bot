import copy
from dlgo.gotypes import Player, Point
from dlgo import zobrist

__all__ = [
    'Board',
    'GameState',
    'Move',
]

class IllegalMoveError(Exception):
    pass

# Create GoString Class

# This class represents a chain of connected stones of the same color
class GoString:
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = frozenset(stones)
        # Stones and liberties are now immutable frozenset instances
        self.liberties = frozenset(liberties) 

    # Replaced the previous remove_liberty method
    def without_liberty(self, point): 
        new_liberties = self.liberties - set([point])
        return GoString(self.color, self.stones, new_liberties)

    # Replaced the previous add_liberty method
    def with_liberty(self, point): 
        new_liberties = self.liberties | set([point])
        return GoString(self.color, self.stones, new_liberties)

    # Returns a new Go string containing all stones in both strings
    def merged_with(self, string): 
        assert string.color == self.color
        combined_stones = self.stones | string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | string.liberties) - combined_stones)

    @property
    def num_liberties(self):
        return len(self.liberties)

    def __eq__(self, other):
        return isinstance(other, GoString) and \
            self.color == other.color and \
            self.stones == other.stones and \
            self.liberties == other.liberties

    def __deepcopy__(self, memodict={}):
        return GoString(self.color, self.stones, copy.deepcopy(self.liberties))

# Create Board Class

# This class represents a Go Board Instance as an empty grid with the specified number of rows and columns
class Board:
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}
        self._hash = zobrist.EMPTY_BOARD
    
    # Checking neighboring points for liberties
    def place_stone(self, player, point): 
        assert self.is_on_grid(point)
        if self._grid.get(point) is not None:
            print('Illegal play on %s' % str(point))
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        # Examine direct neighbors of this point
        for neighbor in point.neighbors(): 
            if not self.is_on_grid(neighbor):
                continue
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)
        new_string = GoString(player, [point], liberties)
        
        # Until this line, place_stone remains the same
        new_string = GoString(player, [point], liberties) 
        
        # You merge any adjacent strings of the same color
        for same_color_string in adjacent_same_color: 
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        
        # Apply the hash code for this point and player
        self._hash ^= zobrist.HASH_CODE[point, player] 

        for other_color_string in adjacent_opposite_color:
            # Reduce liberties of any adjacent strings of the opposite color
            replacement = other_color_string.without_liberty(point) 
            if replacement.num_liberties:
                self._replace_string(other_color_string.without_liberty(point))
            else:
                # If any opposite-color strings now have zero liberties, remove them
                self._remove_string(other_color_string) 
    
    # New helper method updates your Go board grid
    def _replace_string(self, new_string): 
        for point in new_string.stones:
            self._grid[point] = new_string

    def _remove_string(self, string):
        for point in string.stones:
            # Removing a string can create liberties for other strings
            for neighbor in point.neighbors(): 
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    self._replace_string(neighbor_string.with_liberty(point))
            self._grid[point] = None
            # With Zobrist hashing, you need to unapply the hash for this move
            self._hash ^= zobrist.HASH_CODE[point, string.color] 

    def is_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and \
            1 <= point.col <= self.num_cols
    
    # Returns the content of a point on the board: a Player if 
    # a stone is on that point, else, None
    def get(self, point): 
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color
    
    # Returns the entire string of stones at a point: 
    # a GoString if a stone is on that point, else, None
    def get_go_string(self, point): 
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def __eq__(self, other):
        return isinstance(other, Board) and \
            self.num_rows == other.num_rows and \
            self.num_cols == other.num_cols and \
            self._hash() == other._hash()

    def __deepcopy__(self, memodict={}):
        copied = Board(self.num_rows, self.num_cols)
        copied._grid = copy.copy(self._grid)
        copied._hash = self._hash
        return copied

    def zobrist_hash(self):
        return self._hash

# Create Move Class

# This class represents any action a player can play on a turn (play, pass, resign)
class Move:
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    # Move places a stone on the board
    def play(cls, point): 
        return Move(point=point)

    @classmethod
    # Move passes
    def pass_turn(cls): 
        return Move(is_pass=True)

    @classmethod
    # Move resigns the current game
    def resign(cls): 
        return Move(is_resign=True)

    def __str__(self):
        if self.is_pass:
            return 'pass'
        if self.is_resign:
            return 'resign'
        return '(r %d, c %d)' % (self.point.row, self.point.col)

# Create Game State Class

# This class represents the encoding game state for a game of Go
class GameState:
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        if self.previous_state is None:
            self.previous_states = frozenset()
        else:
            self.previous_states = frozenset(
                previous.previous_states |
                {(previous.next_player, previous.board.zobrist_hash())})
        self.last_move = move
    # Returns the new Game State after applying the move
    def apply_move(self, move): 
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    @property
    def situation(self):
        return (self.next_player, self.board)

    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        # Incorporates zobrist hash
        next_situation = (player.other, next_board.zobrist_hash()) 
        return next_situation in self.previous_states

    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get(move.point) is None and
            not self.is_move_self_capture(self.next_player, move) and
            not self.does_move_violate_ko(self.next_player, move))

    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    def legal_moves(self):
        moves = []
        for row in range(1, self.board.num_rows + 1):
            for col in range(1, self.board.num_cols + 1):
                move = Move.play(Point(row, col))
                if self.is_valid_move(move):
                    moves.append(move)
        moves.append(Move.pass_turn())
        moves.append(Move.resign())
        return moves

    def winner(self):
        if not self.is_over():
            return None
        if self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner