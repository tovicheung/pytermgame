from __future__ import annotations

from typing import TypeAlias

class Surface:
    """Represents a 2D string surface"""

    def __init__(self, string: str | Surface):
        self.data = string.splitlines()

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
        return len(max(self.lines(), key=len))
    
    @property
    def height(self):
        return len(self.data)
    
    def __getitem__(self, args):
        if not isinstance(args, tuple):
            return self.data[args]
        if len(args) != 2:
            raise ValueError("Invalid arguments")
        return self.data[args[1]][args[0]]
    
    def is_blank(self, x, y):
        return self[x, y] == " "
    
    def lines(self):
        for line in self.data:
            yield line

    def to_blank(self):
        # Transform to whitespaces for erasing
        string = ""
        for line in self.lines():
            string += " " * len(line) + "\n"
        return type(self).strip(string)

SurfaceLike: TypeAlias = Surface | str
