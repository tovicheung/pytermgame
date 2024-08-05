# [future: cursor]

from dataclasses import dataclass

from .coords import Coords
from . import terminal

@dataclass
class Cursor:
    """Screen coordinates instead of scene coordinates"""
    coords: Coords = Coords.ORIGIN
    visible: bool = False

    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def goto(self, x: int, y: int):
        self.coords = Coords(x, y)
    
    def move(self, dx: int, dy: int):
        self.coords = self.coords.dx(dx).dy(dy)
    
    def write_ansi(self):
        if self.visible:
            terminal.show_cursor()
            terminal.goto(*self.coords.to_term())
        else:
            terminal.hide_cursor()
