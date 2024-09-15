# commonly used names

# put at top to prevent circular imports
from . import clock

# class-based
from .collidable import viewport
from .coords import Coords
from .debugger import Debugger
from .game import Game
from .group import Group
from .profiler import Profiler
from .scene import Scene
from .sprite import Sprite, KinematicSprite, Object
from .sprites import *
from .style import Style, Dir, Colors
from .surface import Surface
from .ui import *

# function-based
from . import cursor, event, key, terminal

# terminal test

try:
    terminal.width()
except OSError as e:
    import sys
    if sys.platform == "win32" and e.winerror == 6:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    elif e.errno == 25:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    raise
