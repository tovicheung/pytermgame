"""ptg.cursor
No matter how many scenes you have in a game, or how many games you are running in parallel,
there can only be one cursor.

Therefore the cursor object and operations belongs in global scope and not game/scene.
(this module functionally behaves like an object)
"""

from dataclasses import dataclass

from .coords import Coords
from . import terminal

@dataclass
class CursorState:
    # Screen coordinates instead of scene coordinates
    coords: Coords = Coords.ORIGIN
    visible: bool = False

state = CursorState()

def get_coords():
    return state.coords

def show():
    state.visible = True

def hide():
    state.visible = False

def set_x(x: int):
    state.coords = state.coords.with_x(x)

def set_y(y: int):
    state.coords = state.coords.with_y(y)

def goto(x: int, y: int):
    state.coords = Coords(x, y) # type: ignore

def move(dx: int = 0, dy: int = 0):
    state.coords = state.coords.dx(dx).dy(dy)

def write_ansi():
    """Note: flushes"""
    if state.visible:
        terminal.show_cursor()
        terminal.goto(*state.coords.to_term())
    else:
        terminal.hide_cursor()
    terminal.flush()
