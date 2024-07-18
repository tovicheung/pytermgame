from __future__ import annotations

from fractions import Fraction
from typing import TypeAlias, Sequence

class Coords:
    # should be immutable

    ORIGIN: Coords

    def __init__(self, x: int | float | Fraction, y: int | float | Fraction):
        self.x = Fraction(x)
        self.y = Fraction(y)

    @classmethod
    def coerce(cls, obj: XY) -> Coords:
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, Sequence):
            assert len(obj) == 2, "Coordinate should be sequence with 2 numbers"
            try:
                x = Fraction(obj[0])
            except ValueError:
                raise ValueError("x coordinate cannot be converted into a fraction") from None
            
            try:
                y = Fraction(obj[1])
            except ValueError:
                raise ValueError("y coordinate cannot be converted into a fraction") from None
            
            return cls(x, y)
        raise ValueError("Invalid coordinate")

    def to_term(self):
        """Converts 0-based fractional coordinates to 1-based terminal coordinates"""
        return type(self)(max(0, self.x + 1), max(0, self.y + 1))
    
    def d(self, other: XY):
        other = Coords.coerce(other)
        return self.dx(other.x).dy(other.y)
    
    def dx(self, dx: int | float | Fraction):
        return type(self)(self.x + dx, self.y)
    
    def dy(self, dy: int | float | Fraction):
        return type(self)(self.x, self.y + dy)
    
    def setx(self, x):
        return type(self)(x, self.y)
    
    def sety(self, y):
        return type(self)(self.x, y)
    
    def __iter__(self):
        return (self.x, self.y).__iter__()
    
    def __str__(self):
        return str(tuple(self))

XY: TypeAlias = tuple[int | float | Fraction, int | float | Fraction] | Coords

Coords.ORIGIN = Coords(0, 0)
