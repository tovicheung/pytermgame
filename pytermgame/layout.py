"""ptg.layout

This module provides helpful functions for placing sprites on screen.
"""

# CURRENTLY UNUSED, FOR FUTURE + TESTING

from typing import TypeAlias
from enum import Enum

from . import terminal

def centerx():
    return terminal.width() // 2

def centery():
    return terminal.height() // 2

def center():
    return centerx(), centery()

def left():
    return 0

def right():
    return terminal.width() - 1

def top():
    return 0

def bottom():
    return terminal.height() - 1

class origin(Enum):
    left = "left"
    right = "right"
    top = "top"
    bottom = "bottom"
    center = "center"

Origin: TypeAlias = tuple[origin, origin]
TOPLEFT: Origin = (origin.top, origin.left)
BOTTOMLEFT: Origin = (origin.bottom, origin.left)
TOPRIGHT: Origin = (origin.top, origin.right)
BOTTOMRIGHT: Origin = (origin.bottom, origin.right)
CENTER: Origin = (origin.center, origin.center)
