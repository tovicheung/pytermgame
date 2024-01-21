from __future__ import annotations

from typing import TypeAlias, TYPE_CHECKING

# if TYPE_CHECKING:
#     from .sprite import Sprite
# from .game import Game

class Coords:
    # should be immutable

    ORIGIN: Coords

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    @classmethod
    def make(cls, obj: XY) -> Coords:
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, tuple):
            assert len(obj) == 2, "Coordinate should be tuple with 2 integers"
            try:
                x = int(obj[0])
            except ValueError:
                raise ValueError("x coordinate cannot be converted into an integer") from None
            
            try:
                y = int(obj[1])
            except ValueError:
                raise ValueError("y coordinate cannot be converted into an integer") from None
            
            return cls(x, y)
        raise ValueError("Invalid coordinate")

    def to_term(self):
        """Converts 0-based coordinates to 1-based terminal coordinates"""
        return type(self)(self.x + 1, self.y + 1)
    
    def dx(self, dx):
        return type(self)(self.x + dx, self.y)
    
    def dy(self, dy):
        return type(self)(self.x, self.y + dy)
    
    def setx(self, x):
        return type(self)(x, self.y)
    
    def sety(self, y):
        return type(self)(self.x, y)
    
    def __iter__(self):
        return (self.x, self.y).__iter__()

XY: TypeAlias = tuple[int, int] | Coords

Coords.ORIGIN = Coords(0, 0)
