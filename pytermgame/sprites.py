from __future__ import annotations

from math import floor
import string
from typing import Callable, TypeVar, Generic

from . import cursor, key
from .event import Event
from .sprite import NestedCollidables, Sprite, KinematicSprite
from .surface import Surface

_T = TypeVar("_T")

__all__ = [
    "Text", "FText", "Value", "Counter", "Gauge", "TextInput", "BouncingBall"
]


class Text(Sprite):
    """Text display
    
    Note: ptg.Text(x) is functionally the same as ptg.Object(x)
    but this can be subclassed to create text displays with custom behaviour
    """

    def __init__(self, text: str):
        super().__init__()
        self.surf = Surface(text)


class FText(Sprite):
    """Text display with format options
    
    Example:
    ```python
    counter = FText("You have {} points", 0).place(5, 5)
    # default: You have 0 points
    counter.format(6) # You have 6 points
    counter.format(7) # You have 7 points
    counter.format(8) # You have 8 points
    ```
    """

    def __init__(self, string: str, *args, **kwargs):
        super().__init__()
        self.string = string
        self.args = args
        self.kwargs = kwargs
    
    def new_surf_factory(self) -> Surface:
        return Surface(self.string.format(*self.args, **self.kwargs))

    def format(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.update_surf()


class Value(Sprite, Generic[_T]):
    """Generic value display"""

    def __init__(self, value: _T, to_string: Callable[[_T], str] = str):
        super().__init__()
        self.value = value
        self.to_string = to_string
    
    def new_surf_factory(self) -> Surface:
        return Surface(self.to_string(self.value))
    
    def set(self, value: _T):
        self.value = value
        self.update_surf()
    
    update_value = set

    def __str__(self):
        return str(self.value)


class Counter(Value[int]):
    def increment(self, by: int = 1):
        self.set(self.value + by)

    def decrement(self, by: int = 1):
        self.increment(-by)


class Gauge(Sprite):
    def __init__(self, full: int, length: int, value: int | float = 0):
        super().__init__()
        self.full = full
        self.value = value
        self.length = length
    
    def new_surf_factory(self) -> Surface:
        n = floor(self.value / self.full * self.length)
        return Surface("[" + "#" * n + " " * (self.length - n) + "]")

    def update_value(self, value: int | float):
        self.value = value
        self.update_surf()


class TextInput(Sprite):
    """A simple text input box
    Note: requires .update()
    """

    def __init__(self, allow_insert: str = string.digits + string.ascii_letters + string.punctuation + " "):
        super().__init__()
        self.value = ""
        self.allow_insert = allow_insert
        self.cur = 0
    
    def new_surf_factory(self) -> Surface:
        return Surface(self.value)

    def update_value(self, value: str):
        self.value = value
        if len(value) < self.cur:
            self.cur = len(value)
        self.update_surf()
    
    def process(self, event: Event):
        if event.is_key(key.LEFT):
            self.cur = max(0, self.cur - 1)
            return True
        elif event.is_key(key.RIGHT):
            self.cur = min(len(self.value), self.cur + 1)
            return True
        elif event.is_key(key.BACKSPACE):
            if self.cur > 0:
                self.cur -= 1
                self.update_value(self.value[:self.cur] + self.value[self.cur+1:])
            return True
        elif event.is_key(key.DELETE):
            self.update_value(self.value[:self.cur] + self.value[self.cur+1:])
            return True
        elif event.is_key(key.HOME) or event.is_key(key.UP):
            self.cur = 0
            return True
        elif event.is_key(key.END) or event.is_key(key.DOWN):
            self.cur = len(self.value)
            return True
        elif event.is_key() and event.value_passes(self.allow_insert.__contains__):
            # `event.value in allow_insert` is not used because value may not be str
            self.update_value(self.value[:self.cur] + str(event.value) + self.value[self.cur:])
            self.cur += 1
            return True
        return False
    
    def update(self):
        cursor.goto(self.x + self.cur, self.y)


class BouncingBall(KinematicSprite):
    """A bouncing ball
    Note: requires .update()
    """

    surf = Surface("O")

    def __init__(self, vx: int, vy: int, bounce_on: NestedCollidables):
        super().__init__()
        self.vx = vx
        self.vy = vy
        self.bounce_on = bounce_on
    
    def update(self):
        self.bounce(self.bounce_on)
