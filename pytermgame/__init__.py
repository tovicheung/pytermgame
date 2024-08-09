# commonly used names

# class-based
from .collidable import ScreenEdge, screen
from .coords import Coords
from .debugger import Debugger
from .game import Game
from .group import Group
from .profiler import Profiler
from .scene import Scene
from .sprite import Sprite, KinematicSprite, Object
from .sprites import Text, FText, Value, Counter, Gauge, TextInput, Border
from .style import Style, Dir, Color
from .surface import Surface

# function-based
from . import clock, cursor, event, key, terminal

# terminal test

try:
    terminal.width()
except OSError as e:
    if terminal.WINDOWS and e.winerror == 6:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    elif e.errno == 25:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    raise
