from __future__ import annotations

from enum import Enum
from fractions import Fraction
from typing import TypeAlias, Sequence, ClassVar
import sys

if sys.version_info >= (3, 11):
    from typing import Self

class CoordsType(Enum):
    float = "float"
    fraction = "fraction"

COORDS_TYPE = CoordsType.float

class Coords:
    ORIGIN: ClassVar[Coords] = None # type: ignore

    def __new__(cls, x: int | float | Fraction, y: int | float | Fraction):
        if COORDS_TYPE == CoordsType.float:
            return FloatCoords(x, y)
        elif COORDS_TYPE == CoordsType.fraction:
            inst = object.__new__(FracCoords)
            inst.__init__(x, y)
            return inst
        raise ValueError(f"Unknown COORDS_TYPE {COORDS_TYPE}")
    
    x: int | float | Fraction
    y: int | float | Fraction
    
    def __neg__(self) -> Self:
        return type(self)(-self.x, -self.y)

    @classmethod
    def coerce(cls, obj: XY) -> Self:
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, Sequence):
            assert len(obj) == 2, "Coordinate should be sequence with 2 numbers"            
            return cls(obj[0], obj[1])
        raise ValueError("Invalid coordinate")
    
    # Generic methods, subclasses may have more efficient implementation

    def to_term(self):
        """0-based to 1-based"""
        return type(self)(self.x + 1, self.y + 1)
    
    def d(self, other: XY):
        other = Coords.coerce(other)
        return self.dx(other.x).dy(other.y)
    
    def dx(self, dx: int | float | Fraction):
        return type(self)(self.x + dx, self.y)
    
    def dy(self, dy: int | float | Fraction):
        return type(self)(self.x, self.y + dy)
    
    def with_x(self, x):
        return type(self)(x, self.y)
    
    def with_y(self, y):
        return type(self)(self.x, y)
    
    def __iter__(self):
        return (self.x, self.y).__iter__()
    
    def __str__(self):
        return str(tuple(self))

XY: TypeAlias = tuple[int | float | Fraction, int | float | Fraction] | Coords

class FloatCoords(complex, Coords):
    # complex is put first so that its C methods get inherited
    @property
    def x(self):
        return self.real
    
    @property
    def y(self):
        return self.imag
    
    def __neg__(self):
        return type(self)(super().__neg__())
    
    def to_term(self):
        return type(self)(self + 1 + 1j)
    
    def d(self, other: XY):
        coords = type(self).coerce(other)
        return type(self)(self + coords)
    
    def dx(self, dx: int | float | Fraction):
        return type(self)(self + dx)
    
    def dy(self, dy: int | float | Fraction):
        return type(self)(self + dy * 1j)

class FracCoords(Coords):
    def __init__(self, x: int | float | Fraction, y: int | float | Fraction):
        self.x = x
        self.y = y

Coords.ORIGIN = Coords(0, 0) # type: ignore
