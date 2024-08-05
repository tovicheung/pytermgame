# [future: cursor]

from dataclasses import dataclass

from .coords import Coords
from . import terminal

@dataclass
class CursorState:
    # Screen coordinates instead of scene coordinates
    coords: Coords = Coords.ORIGIN
    visible: bool = False

# No matter how many scenes you have in a game, or how many games you are running in parallel,
# there can only be one cursor

state = CursorState()

# Therefore the cursor object and operations belongs in global scope and not game/scene.
# (this module functionally behaves like an object)

def get_coords():
    return state.coords

def show():
    state.visible = True

def hide():
    state.visible = False

def goto(x: int, y: int):
    state.coords = Coords(x, y)

def move(dx: int, dy: int):
    state.coords = state.coords.dx(dx).dy(dy)

def write_ansi():
    """Note: flushes"""
    if state.visible:
        terminal.show_cursor()
        terminal.goto(*state.coords.to_term())
    else:
        terminal.hide_cursor()
    terminal.flush()