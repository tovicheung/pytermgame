from __future__ import annotations
from math import floor
import string
from typing import TYPE_CHECKING, Any, Self, TypeVar, Generic, overload

from pytermgame.coords import Coords

from .event import Event
from . import cursor, key
from .sprite import NestedCollidables, Sprite, KinematicSprite
from .surface import Surface

_T = TypeVar("_T")

class Text(Sprite):
    """Text display
    
    Note: ptg.Text(x) is functionally the same as ptg.Object(x)
    but users can subclass ptg.Text to create text displays with custom behaviour
    """

    def __init__(self, text: str):
        super().__init__()
        self.surf = Surface(text)

class FText(Sprite):
    """Formatted text display
    
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
        self.set_surf(Surface(self.string.format(*args, **kwargs)))

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
    
    def new_surf_factory(self) -> Surface:
        return Surface(str(self.value))

    def update_value(self, value: _T):
        self.value = value
        self.update_surf()

    def __str__(self):
        return str(self.value)

class Counter(Value[int]):
    def increment(self, by: int = 1):
        self.update_value(self.value + by)

    def decrement(self, by: int = 1):
        self.increment(-by)

class Gauge(Sprite):
    def __init__(self, full, length, value=0):
        super().__init__()
        self.full = full
        self.value = value
        self.length = length
    
    def new_surf_factory(self) -> Surface:
        n = floor(self.value / self.full * self.length)
        return Surface("[" + "#" * n + " " * (self.length - n) + "]")

    def update_value(self, value):
        self.value = value
        self.update_surf()

_S = TypeVar("_S", bound=Sprite)
_S2 = TypeVar("_S2", bound=Sprite)

class Container(Sprite, Generic[_S]):
    def __init__(self, child: _S | None = None):
        super().__init__()
        self.child = child
    
    # issue: https://github.com/python/mypy/issues/9201
    # cls is typed as type[Self[_S]] instead of type[Self]
    def wrap(self, child: _S):
        self.child = child
        child._parent = self
        if child.placed:
            self.place(self.get_self_coords())
            self._scene.move_sprite_to_below(self, child)
        return self
    
    def get_child(self) -> _S:
        if self.child is None:
            raise ValueError("Invalid call, child is not supplied")
        return self.child
    
    # @overload
    # def get_innermost_child(self: Container[Container[Container[Container[_S2]]]]) -> _S2: ...
    # @overload
    # def get_innermost_child(self: Container[Container[Container[_S2]]]) -> _S2: ...
    # @overload
    # def get_innermost_child(self: Container[Container[_S2]]) -> _S2: ...
    # @overload
    # def get_innermost_child(self: Container[_S2]) -> _S2: ...
    
    def get_innermost_child(self):
        if isinstance(self.child, Container):
            return self.child.get_innermost_child()
        return self.child
    
    def _flatten(self):
        yield self
        if isinstance(self.child, Container):
            yield from self.child._flatten()
        else:
            yield self.child
    
    # @overload
    # def flatten(self: Container[Container[Container[Container[_S2]]]]) -> tuple[Container[Container[Container[Container[_S2]]]], Container[Container[Container[_S2]]], Container[Container[_S2]], Container[_S2], _S2]: ...
    # @overload
    # def flatten(self: Container[Container[Container[_S2]]]) -> tuple[Container[Container[Container[_S2]]], Container[Container[_S2]], Container[_S2], _S2]: ...
    # @overload
    # def flatten(self: Container[Container[_S2]]) -> tuple[Container[Container[_S2]], Container[_S2], _S2]: ...
    # @overload
    # def flatten(self: Container[_S2]) -> tuple[Container[_S2], _S2]: ...
    def flatten(self):
        """Returns tuple of the nested structure
        Example:
        ```python
        messy = Border(Border(Border(x)))
        outermost, middle, inner, x = messy.flatten()
        ```
        """
        # evaluate all at once, instead of creating a lot of temporary tuples
        return tuple(self._flatten())
    
    def set_dirty(self, propagate=True):
        if self.child is not None and self.placed and self._rendered.dirty:
            self.child.goto(*self.get_child_coords())
            # self.child.move(*(self._coords - self._rendered.coords))
        super().set_dirty(propagate)
    
    # Subclasses of Container must implement these:

    def get_child_coords(self) -> Coords:
        # self coords -> child coords
        return self._coords
        raise NotImplementedError("Subclasses of Container must implement .get_child_coords()")
    
    def get_self_coords(self) -> Coords:
        # child coords -> self coords
        return self.child._coords
        raise NotImplementedError("Subclasses of Container must implement .get_self_coords()")
    
    def new_surf_factory(self) -> Surface:
        raise NotImplementedError("Subclasses of Container must implement .new_surf_factory()")

class MinSize(Container[_S]):
    def __init__(self, min_width: int | None = None, min_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.min_width = min_width
        self.min_height = min_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> MinSize[_S2]: ...
    
    def get_child_coords(self) -> Coords:
        return self._coords
    
    def new_surf_factory(self) -> Surface:
        if self.child is None:
            raise ValueError("MinSize() must have a child")
        if not self.child.placed:
            self.child.place(self.get_child_coords())
        min_width = max(self.min_width or self.child.width, self.child.width)
        min_height = max(self.min_height or self.child.height, self.child.height)
        return Surface.blank(min_width, min_height)

class MaxSize(Container[_S]):
    def __init__(self, max_width: int | None = None, max_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.max_width = max_width
        self.max_height = max_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> MaxSize[_S2]: ...
    
    def get_child_coords(self) -> Coords:
        return self._coords
    
    def new_surf_factory(self) -> Surface:
        if self.child is None:
            raise ValueError("MinSize() must have a child")
        if not self.child.placed:
            self.child.place(self.get_child_coords())
        max_width = min(self.max_width or self.child.width, self.child.width)
        max_height = min(self.max_height or self.child.height, self.child.height)
        return Surface.blank(max_width, max_height)

class Padding(Container[_S]):
    def __init__(self, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0, child: _S | None = None):
        super().__init__(child)
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
    
    @classmethod
    def all(cls, padding: int = 0):
        return Padding(padding, padding, padding, padding)
    
    @classmethod
    def symmetric(cls, horizontal: int = 0, vertical: int = 0):
        return Padding(vertical, vertical, horizontal, horizontal)
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> Padding[_S2]: ...
    
    def get_child_coords(self) -> Coords:
        return self._coords.d((self.left, self.top))
    
    def get_self_coords(self) -> Coords:
        return self.child._coords.d((-self.left, -self.top))
    
    def new_surf_factory(self) -> Surface:
        if self.child is None:
            raise ValueError("Padding() must have a child")
        width = self.child.width + self.left + self.right
        height = self.child.height + self.top + self.bottom
        return Surface.blank(width, height)

class Border(Container[_S]):
    def __init__(self, inner_width: int | None = None, inner_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.inner_width: int | None = inner_width
        self.inner_height: int | None = inner_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> Border[_S2]: ...
    
    def get_child_coords(self) -> Coords:
        return self._coords.d((1, 1))
    
    def get_self_coords(self) -> Coords:
        return self.child._coords.d((-1, -1))
    
    def new_surf_factory(self) -> Surface:
        # self depends on child
        if self.child is not None:
            if not self.child.placed:
                self.child.place(self.get_child_coords())
            inner_width = self.child.width
            inner_height = self.child.height
        else:
            if self.inner_width is None:
                raise ValueError("Border.inner_width not supplied")
            if self.inner_height is None:
                raise ValueError("Border.inner_height not supplied")
            inner_width = self.inner_width
            inner_height = self.inner_height
        return Surface(
            "┌" + "─" * inner_width + "┐" + "\n"
            + ("│" + " " * inner_width + "│" + "\n") * inner_height
            + "└" + "─" * inner_width + "┘"
        )
    
    def resize(self, inner_width: int, inner_height: int):
        self.inner_width = inner_width
        self.inner_height = inner_height
        self.update_surf()

class TextInput(Sprite):
    """A simple text input interface.
    Note: requires .update()"""

    def __init__(self):
        super().__init__()
        self.value = ""
        self.cur = 0
    
    def new_surf_factory(self) -> Surface:
        return Surface(self.value)

    def update_value(self, value: str):
        self.value = value
        if len(value) < self.cur:
            self.cur = len(value)
        self.update_surf()
    
    def process(self, event: Event, allow_insert = string.digits + string.ascii_letters + string.punctuation + " "):
        """Tries to process the event and returns True if processed, else False.
        
        This method may be standardized in the future for more keyboard-based sprites.

        Example:
        ```python
        if sprite1.process(event):
            pass
        elif sprite2.process(event):
            pass
        ```
        """
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
        elif event.is_key() and event.value_passes(allow_insert.__contains__):
            # `event.value in allow_insert` is not used because value may not be str
            self.update_value(self.value[:self.cur] + str(event.value) + self.value[self.cur:])
            self.cur += 1
            return True
    
    def update(self):
        cursor.goto(self.x + self.cur, self.y)

class BouncingBall(KinematicSprite):
    surf = Surface("O")
    def __init__(self, vx: int, vy: int, bounce_on: NestedCollidables):
        super().__init__()
        self.vx = vx
        self.vy = vy
        self.bounce_on = bounce_on
    
    def update(self):
        self.bounce(self.bounce_on)
