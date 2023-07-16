# commonly used names

from .sprite import Sprite, Group
from .surface import Surface
from .game import Game
from . import terminal, event, key

# purely for convenience
from time import sleep
from random import randint

# TODO: refactor to modules
def randy():
    return randint(0, terminal.height - 1)
def randx():
    return randint(0, terminal.width - 1)
