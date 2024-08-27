from __future__ import annotations

from typing import Generator, Iterable, TypeAlias, TYPE_CHECKING

from . import terminal

if TYPE_CHECKING:
    from .coords import Coords

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

        # pre-generate a blank version of self for erasing
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
        """Generate a blank rectangular surface filled with spaces"""
        return cls((" " * width + "\n") * height)
    
    @classmethod
    def phantom(cls, width: int, height: int):
        return PhantomSurface(width, height)
    
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
    
    def get_dimensions(self):
        return self.width, self.height
    
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
    
    def render(self, coords: Coords, ansi: str = "\033[m", flush: bool = True):
        if coords.x + self.width < 0 or \
            coords.y + self.height < 0 or \
            coords.x >= terminal.width() or \
            coords.y >= terminal.height():
            return # out of screen, do nothing!

        if coords.x < 0:
            # partially out of left bound
            slice_x = slice(int(abs(coords.x)), None, None)
        elif coords.x + self.width > terminal.width():
            # partially out of right bound
            # terminal.width() - int(coords.x) = how many chars to show
            slice_x = slice(None, terminal.width() - int(coords.x), None)
        else:
            slice_x = slice(None, None, None)
        
        line_coords_base = coords.with_x(0) if coords.x < 0 else coords.with_x(terminal.width() - 1) if coords.x >= terminal.width() else coords

        for i, line in enumerate(self.lines()):
            segment = line[slice_x]
            if len(segment) == 0:
                continue
            line_coords = line_coords_base.dy(i)
            if line_coords.y < 0 or line_coords.y >= terminal.height():
                continue # line is vertically out of screen
            terminal.goto(*line_coords.to_term())
            terminal.write(ansi + segment)

        terminal.write("\033[m")

        if flush:
            terminal.flush() # flush at once, not every line
    
    # may be useful in future

    def crop_to_left(self, max_width: int):
        return Surface(x[:max_width] for x in self.lines())
    
    def crop_to_right(self, max_width: int):
        return Surface(x[-max_width:] for x in self.lines())
    
    def crop_to_top(self, max_height: int):
        return Surface(self._lines[:max_height])
    
    def crop_to_bottom(self, max_height: int):
        return Surface(self._lines[-max_height:])

SurfaceLike: TypeAlias = Surface | str | list[str]

class PhantomSurface(Surface):
    """A PhantomSurface is simply empty. It only has a size."""

    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
    
    def lines(self) -> Generator[str, None, None]:
        return
        yield
    
    def to_blank(self):
        return self
    
    def render(self, coords: Coords, ansi: str = "\033[m", flush: bool = True):
        return
