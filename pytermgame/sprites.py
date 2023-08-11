from __future__ import annotations
from typing import TypeVar, Generic

from .sprite import Sprite
from .surface import Surface

_T = TypeVar("_T")

class Text(Sprite):
    def __init__(self, text: str, x: int = 0, y: int = 0):
        super().__init__(x, y)
        self.surf = Surface(text)

class FText(Sprite):
    # Formatted text
    def __init__(self, string: str, x: int = 0, y: int = 0):
        super().__init__(x, y)
        self.string = string
        self.surf = None
        self.oldsurf = None

    def format(self, *args, **kwargs):
        self.oldsurf = self.surf
        self.surf = Surface(self.string.format(*args, **kwargs))
        self._dirty = 1

# currently unused, this descriptor may replace Value.value in the future
class _Value:
    def __init__(self, value: _T):
        self.value = value

    def __get__(self, obj, objtype=None) -> _T:
        return self.value
    
    def __set__(self, obj: Value, value: _T):
        self.value = value
        obj.update_surf()

class Value(Sprite, Generic[_T]):
    def __init__(self, value: _T, x: int = 0, y: int = 0):
        super().__init__(x, y)
        self.value = value
        self.update_surf()

    def update_surf(self):
        self.surf = Surface(str(self.value))
        self._dirty = 1

    def update_value(self, value: _T):
        self.value = value
        self.update_surf()

class Counter(Value[int]):
    def increment(self, by: int = 1):
        self.value += by
        self.update_surf()

    def decrement(self, by: int = 1):
        self.increment(-by)

# __all__ = ["Text", "Value", "Counter"]
