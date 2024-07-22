from __future__ import annotations

from typing import Iterable, TypeAlias

class Surface:
    """Represents an immutable 2D string surface"""

    def __init__(self, string: str | Iterable[str]):
        if isinstance(string, str):
            self._lines = string.splitlines()
        else:
            self._lines = list(string)
        self._width = len(max(self.lines(), key=len))
        self._height = len(self._lines)
    
    @classmethod
    def coerce(cls, obj: SurfaceLike) -> Surface:
        """Convert SurfaceLike to Surface"""
        if isinstance(obj, Surface):
            return obj
        if isinstance(obj, str):
            return cls(obj)
        if isinstance(obj, Iterable):
            return cls(obj)
        raise TypeError(f"Cannot convert {type(obj).__qualname__!r} object to Surface")

    @classmethod
    def blank(cls, width: int, height: int):
        """Generate a blank rectangular surface"""
        return cls((" " * width + "\n") * height)
    
    @classmethod
    def strip(cls, string: str):
        """For easy formatting"""
        return cls(string.strip("\n"))
    
    @property
    def width(self):
        return self._width
    
    @property
    def height(self):
        return self._height
    
    def __getitem__(self, args):
        """Element access
        
        surf[(x, y)] = character at (x, y)
        surf[n] = n-th line
        """
        if not isinstance(args, tuple):
            return self._lines[args]
        if len(args) != 2:
            raise ValueError("Invalid arguments")
        return self._lines[args[1]][args[0]]
    
    def lines(self):
        for line in self._lines:
            yield line

    def to_blank(self):
        # Transform to whitespaces for erasing
        string = ""
        for line in self.lines():
            string += " " * len(line) + "\n"
        return type(self).strip(string)

SurfaceLike: TypeAlias = Surface | str | list[str]
