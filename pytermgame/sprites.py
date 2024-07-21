from __future__ import annotations
from math import floor
from typing import TypeVar, Generic

from .sprite import Sprite
from .surface import Surface

_T = TypeVar("_T")

class Text(Sprite):
    """Text display"""

    def __init__(self, text: str):
        super().__init__()
        self.surf = Surface(text)

class FText(Sprite):
    """Fstring display
    
    Example
    >>> counter = FText("You have {} points", 0).place(5, 5)
    >>> # default: You have 0 points
    >>> counter.format(6) # -> You have 6 points
    >>> counter.format(7) # -> You have 7 points
    >>> counter.format(8) # -> You have 8 points

    """

    def __init__(self, string: str, *args, **kwargs):
        super().__init__()
        self.string = string
        self.format(*args, **kwargs)

    def format(self, *args, **kwargs):
        self.surf = Surface(self.string.format(*args, **kwargs))
        self._dirty = True

    def render(self, flush=True, erase=False):
        super().render(flush=flush, erase=True)
        super().render(flush=flush, erase=erase)

# currently unused, this descriptor may replace Value.value in the future
class _Value(Generic[_T]):
    def __init__(self, value: _T):
        raise Exception("unused")
        self.value = value

    def __get__(self, obj, objtype=None) -> _T:
        return self.value
    
    def __set__(self, obj: Value, value: _T):
        self.value = value
        obj.update_surf()

class Value(Sprite, Generic[_T]):
    "Value display"

    def __init__(self, value: _T):
        super().__init__()
        self.value = value
        self.update_surf()

    def update_surf(self):
        self.surf = Surface(str(self.value))
        self._dirty = True # cannot use set_dirty before place

    def update_value(self, value: _T):
        self.value = value
        self.update_surf()

    def __str__(self):
        return str(self.value)

class Counter(Value[int]):
    def increment(self, by: int = 1):
        self.value += by
        self.update_surf()

    def decrement(self, by: int = 1):
        self.increment(-by)

class Gauge(Sprite):
    def __init__(self, full, length, value=0):
        super().__init__()
        self.full = full
        self.value = value
        self.length = length
        self.update_surf()

    def update_surf(self):
        n = floor(self.value / self.full * self.length)
        self.surf = Surface("[" + "#" * n + " " * (self.length - n) + "]")
        self._dirty = True # cannot use set_dirty before place
    
    def update_value(self, value):
        self.value = value
        self.update_surf()

# class Margin(Sprite):
#     def __init__(self, inner_width: int, inner_height: int):
#         self.inner_width = inner_width
#         self.inner_height = inner_height
#         self.surf = Surface(
#             "┌" + "─" * inner_width + "┐" + "\n"
#             + ("│" + " " * inner_width + "│" + "\n") * inner_height
#             + "└" + "─" * inner_width + "┘"
#         )
#         super().__init__()
