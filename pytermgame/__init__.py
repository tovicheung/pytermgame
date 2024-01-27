# commonly used names

# class-based
from .coords import Coords
from .game import Game
from .group import Group
from .scene import Scene
from .sprite import Sprite
from .sprites import Text, FText, Value, Counter
from .surface import Surface

# function-based
from . import clock, event, key, terminal

# terminal test

try:
    terminal.width()
except OSError as e:
    if terminal.WINDOWS and e.winerror == 6:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    elif e.errno == 25:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    raise
