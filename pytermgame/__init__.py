# commonly used names

# class-based
from .collidable import ScreenEdge, screen
from .coords import Coords
from .debugger import Debugger
from .game import Game
from .group import Group
from .modifier import Modifier, Dir, Color
from .profiler import Profiler
from .scene import Scene
from .sprite import Sprite, KinematicSprite, Object, UP, DOWN, LEFT, RIGHT, TOP, BOTTOM
from .sprites import Text, FText, Value, Counter, Gauge
from .surface import Surface

# function-based
from . import clock, event, key, terminal, transition

# terminal test

try:
    terminal.width()
except OSError as e:
    if terminal.WINDOWS and e.winerror == 6:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    elif e.errno == 25:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    raise
