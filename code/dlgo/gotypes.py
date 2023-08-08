import enum
from collections import namedtuple

__all__ = [
    'Player',
    'Point',
]

# Create Player Class

# This class creates a player that is either black or white (enum). 
# Once player places stone, you can switch the color by calling the other method on a Player instance
class Player(enum.Enum):
    black = 1
    white = 2
    
    @property
    def other(self):
        return Player.black if self == Player.white else Player.white
    
# Create Point Class

# This class represent coordinates on the Go board
class Point(namedtuple('Point', 'row col')):
    def neighbors(self):
        return [
            Point(self.row - 1, self.col),
            Point(self.row + 1, self.col),
            Point(self.row, self.col - 1),
            Point(self.row, self.col + 1),
        ]
    
    # Immutable
    def __deepcopy__(self, memodict={}): 
        return self