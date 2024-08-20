from __future__ import annotations

from typing import Generator, Iterable, TypeAlias

class Surface:
    """2D immutable string surface"""

    def __init__(self, string: str | Iterable[str], _blank: bool = False):
        if isinstance(string, str):
            self._lines = string.splitlines()
            if len(self._lines) == 0:
                self._lines = [""]
        else:
            self._lines = list(string)
        self._width = len(max(self.lines(), key=len))
        self._height = len(self._lines)

        if not _blank:
            string = ""
            for line in self.lines():
                string += " " * len(line) + "\n"
            self._blank = type(self)(string.strip("\n"), _blank=True)
        else:
            self._blank = self
    
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
    
    def __getitem__(self, args: int | tuple[int, int]):
        """Element access
        
        surf[(x, y)] = character at (x, y)
        surf[n] = n-th line
        """
        if not isinstance(args, tuple):
            return self._lines[args]
        if len(args) != 2:
            raise ValueError("Invalid arguments")
        return self._lines[args[1]][args[0]]
    
    def lines(self) -> Generator[str, None, None]:
        yield from self._lines

    def to_blank(self):
        return self._blank
        # Transform to whitespaces for erasing
        string = ""
        for line in self.lines():
            string += " " * len(line) + "\n"
        return type(self).strip(string)
    
    def crop_to_left(self, max_width: int):
        return Surface(x[:max_width] for x in self.lines())
    
    def crop_to_right(self, max_width: int):
        return Surface(x[-max_width:] for x in self.lines())
    
    def crop_to_top(self, max_height: int):
        return Surface(self._lines[:max_height])
    
    def crop_to_bottom(self, max_height: int):
        return Surface(self._lines[-max_height:])

SurfaceLike: TypeAlias = Surface | str | list[str]
