# commonly used names

# class-based
from .sprite import Sprite, Group
from .sprites import Text, FText, Value, Counter
from .surface import Surface
from .game import Game

# function-based
from . import terminal, event, key, clock

try:
    terminal.width()
except OSError as e:
    if terminal.WINDOWS and e.winerror == 6:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    elif e.errno == 25:
        raise Exception("Terminal is not available (maybe you are piping it?)") from None
    raise
