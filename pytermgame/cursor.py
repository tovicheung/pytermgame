"""ptg.cursor
No matter how many scenes you have in a game, or how many games you are running in parallel,
there can only be one cursor.

Therefore the cursor object and operations belongs in global scope and not game/scene.
(this module functionally behaves like an object)
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from .coords import Coords
from . import terminal

@dataclass
class CursorState:
    # Screen coordinates instead of scene coordinates
    coords: Coords = Coords.ORIGIN
    visible: bool = False
    dirty: bool = True

state = CursorState()

def get_coords():
    return state.coords

def show():
    state.visible = True
    state.dirty = True

def hide():
    state.visible = False
    state.dirty = True

def set_x(x: int):
    state.coords = state.coords.with_x(x)
    state.dirty = True

def set_y(y: int):
    state.coords = state.coords.with_y(y)
    state.dirty = True

def goto(x: int, y: int):
    state.coords = Coords(x, y) # type: ignore
    state.dirty = True

def move(dx: int = 0, dy: int = 0):
    state.coords = state.coords.dx(dx).dy(dy)
    state.dirty = True

_buffer = ""

def write_ansi():
    if state.visible and terminal.is_valid_term_coords(*state.coords.to_term()):
        terminal.show_cursor()
        terminal.goto(*state.coords.to_term())
        global _buffer
        if _buffer:
            terminal.write(_buffer)
            _buffer = ""
    else:
        terminal.hide_cursor()
        
    state.dirty = False

class CursorShape(StrEnum):
    block = "block"
    underscore = "underscore"
    verticle = "verticle"

def set_style(shape: CursorShape | Literal["block", "underscore", "verticle"], blink: bool):
    match shape:
        case CursorShape.block:
            n = 1
        case CursorShape.underscore:
            n = 3
        case CursorShape.verticle:
            n = 5
    
    n += not blink

    global _buffer
    _buffer += f"\033[{n} q"

    state.dirty = True
