"""ptg.ui: build UI using sprites

Principle: build everything on top of ptg.sprite, avoid coupling normal non-UI sprites with UI attributes/methods

Container
* must have zero or one child
* has well-defined inner dimensions

Collection
* must have one or more children
* defines how their children are arranged
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Iterable, ParamSpec, Self, TypeVar, Generic, TYPE_CHECKING, NamedTuple, overload

# some methods of Sprite are overriden and it is best to mark them
if sys.version_info >= (3, 12):
    from typing import override
else:
    def override(f):
        return f

from . import key
from .coords import Coords
from .event import Event
from .sprite import Sprite
from .surface import Surface

_P = ParamSpec("_P")
_S = TypeVar("_S", bound=Sprite)
_S2 = TypeVar("_S2", bound=Sprite)
_T = TypeVar("_T")

# only export stable sprites
__all__ = ["Container", "MinSize", "MaxSize", "Padding", "Border"]

# Helpers

# for type checking only
def _copy_signature(f: _T) -> Callable[..., _T]:
    return lambda x: x

# for type checking only
def _set_return_type(typ: type[_T]) -> Callable[[Callable[_P, Any]], Callable[_P, _T]]:
    return lambda x: x

def _place_or_set_coords(sprite: Sprite, coords: Coords):
    if sprite.placed:
        sprite.goto(*coords)
    else:
        sprite.place(coords)

# unused for now
class Dimensions(NamedTuple):
    width: int
    height: int
    
    @classmethod
    def from_surf(cls, surf: Surface):
        return cls(surf.width, surf.height)
    
    @classmethod
    def from_sprite(cls, sprite: Sprite):
        return cls(sprite.surf.width, sprite.surf.height)
    
    def to_surf(self):
        return Surface.blank(self.width, self.height)

class Container(Sprite, Generic[_S]):
    """Unlocks .child, .wrap() and .get_inner_dimensions()"""
    
    def __init__(self, child: _S | None = None):
        super().__init__()
        self.child = child
        if child is not None:
            child._parent = self
            if child.placed:
                self.place(child._coords - self.get_child_offset())
                self._scene.move_sprite_to_below(self, child)
    
    # issue: https://github.com/python/mypy/issues/9201
    # cls is typed as type[Self[_S]] instead of type[Self]
    def wrap(self, child: _S):
        self.child = child
        child._parent = self
        if child.placed:
            self.place(child._coords - self.get_child_offset())
            self._scene.move_sprite_to_below(self, child)
        return self
    
    # Border() > Text()  is equivalent to  Border().wrap(Text()) or Border(child = Text())
    __gt__ = wrap
    
    @overload
    def get_innermost_child(self: Container[Container[Container[Container[_S2]]]]) -> _S2: ...
    @overload
    def get_innermost_child(self: Container[Container[Container[_S2]]]) -> _S2: ...
    @overload
    def get_innermost_child(self: Container[Container[_S2]]) -> _S2: ...
    @overload
    def get_innermost_child(self: Container[_S2]) -> _S2: ...
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
    
    @overload
    def flatten(self: Container[Container[Container[Container[_S2]]]]) -> tuple[Container[Container[Container[Container[_S2]]]], Container[Container[Container[_S2]]], Container[Container[_S2]], Container[_S2], _S2]: ...
    @overload
    def flatten(self: Container[Container[Container[_S2]]]) -> tuple[Container[Container[Container[_S2]]], Container[Container[_S2]], Container[_S2], _S2]: ...
    @overload
    def flatten(self: Container[Container[_S2]]) -> tuple[Container[Container[_S2]], Container[_S2], _S2]: ...
    @overload
    def flatten(self: Container[_S2]) -> tuple[Container[_S2], _S2]: ...
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
    
    @override
    def apply_style(self, *args, **kwargs):
        super().apply_style(*args, **kwargs)
        if self.child is not None:
            self.child._resolved_style = None
        return self
    
    @override
    def set_dirty(self, propagate=True):
        if self.child is not None and self.placed and self._rendered.coords != self._coords:
            # this is here because
            # 1. coords may be modified in .set_surf() eg align right
            # 2. child needs to move when (a) parent moves and (b) parent surf changes (eg padding change)
            self.child.goto(*(self._coords + self.get_child_offset()))
        super().set_dirty(propagate)
    
    def get_inner_dimensions(self) -> tuple[int, int]:
        if self.child is None:
            return 0, 0
        return self.child.width, self.child.height
    
    @override
    def update_surf(self):
        if self.child is not None:
            # this is currently the reason why coords is set before surf
            # should only be called in self.place()
            _place_or_set_coords(self.child, self._coords + self.get_child_offset())
        super().update_surf()
    
    # Subclasses of Container may override:

    def get_child_offset(self) -> Coords:
        return Coords(0, 0)
    
    # Subclasses of Container must override:
    
    def new_surf_factory(self) -> Surface:
        """When implementing:
        * use .get_inner_dimensions() to get inner width and height
        * does NOT have to place child
        """
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
        inner_width, inner_height = self.get_inner_dimensions()
        min_width = max(self.min_width or inner_width, inner_width)
        min_height = max(self.min_height or inner_height, inner_height)
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
        inner_width, inner_height = self.get_inner_dimensions()
        max_width = min(self.max_width or inner_width, inner_width)
        max_height = min(self.max_height or inner_height, inner_height)
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
    
    def get_child_offset(self) -> Coords:
        return Coords(self.left, self.top)
    
    def new_surf_factory(self) -> Surface:
        inner_width, inner_height = self.get_inner_dimensions()
        width = inner_width + self.left + self.right
        height = inner_height + self.top + self.bottom
        return Surface.blank(width, height)

class Border(Container[_S]):
    def __init__(self, inner_width: int | None = None, inner_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.inner_width: int | None = inner_width
        self.inner_height: int | None = inner_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> Border[_S2]: ...
    
    def get_child_offset(self) -> Coords:
        return Coords(1, 1)
    
    def new_surf_factory(self) -> Surface:
        inner_width, inner_height = self.get_inner_dimensions()
        inner_width = self.inner_width or inner_width
        inner_height = self.inner_height or inner_height
        return Surface(
            "┌" + "─" * inner_width + "┐" + "\n"
            + ("│" + " " * inner_width + "│" + "\n") * inner_height
            + "└" + "─" * inner_width + "┘"
        )
    
    def resize(self, inner_width: int, inner_height: int):
        self.inner_width = inner_width
        self.inner_height = inner_height
        self.update_surf()

class Collection(Sprite):
    """Unlocks .wrap() and .children
    
    A collection must be occupied."""

    children: tuple[Sprite, ...] | None
    
    def __init__(self, children: Iterable[Sprite] | None = None):
        super().__init__()
        self.children = None
        if children is not None:
            self.children = tuple(children)
            for child in children:
                child._parent = self
    
    def wrap(self, *children: Sprite):
        self.children = children
        for child in children:
            child._parent = self
            if self.placed:
                self._scene.move_sprite_to_below(self, child)
        return self
    
    def get_children(self):
        if self.children is None:
            raise ValueError("Invalid call, children are not supplied")
        return self.children
    
    def insert_child(self, child: Sprite, position: int = -1):
        if self.children is None:
            raise ValueError("Invalid call, children are not supplied")
        if child._parent is not None:
            raise ValueError(f"Child already has parent: {child._parent}")
        child._parent = self
        self.children = self.children[:position] + (child,) + self.children[position:]
        self.update_surf()
    
    @override
    def apply_style(self, *args, **kwargs):
        super().apply_style(*args, **kwargs)
        for child in self.get_children():
            child._resolved_style = None
    
    @override
    def set_dirty(self, propagate=True):
        if self.children is not None and self.placed and self._rendered.coords != self._coords:
            delta = self._coords - self._rendered.coords
            for child in self.children:
                child.goto(*(child._rendered.coords + delta))
        super().set_dirty(propagate)
    
    # Subclasses of Collection must override:

    def new_surf_factory(self) -> Surface:
        """When implementing:
        * use _place_or_set_coords(x) on children
        * determine dimensions
        * create surf, usually from Surface.blank(width, height)
        """
        raise NotImplementedError("Subclasses of Collection must implement .new_surf_factory()")
    
    # Unused:
    
    def build(self) -> Dimensions:
        # might be used when constraints are implemented
        raise Exception("Method is unused")
        raise NotImplementedError("Subclasses of Collection must implement .build()")

class Column(Collection):    
    def new_surf_factory(self):
        width = height = 0

        for child in self.get_children():
            _place_or_set_coords(child, self._coords.dy(height))
            height += child.height
            width = max(width, child.width)
        
        return Surface.phantom(width, height)

class Row(Collection):
    def new_surf_factory(self):
        width = height = 0

        for child in self.get_children():
            _place_or_set_coords(child, self._coords.dx(width))
            width += child.width
            height = max(height, child.height)
        
        return Surface.phantom(width, height)

class SelectionMenu(Column):
    def on_placed(self):
        self.selected_index = 0
        self.selected.apply_style(inverted=True)

    @property
    def selected(self):
        assert self.children is not None, "SelectionMenu must have children"
        assert len(self.children) > 0, "SelectionMenu must have at least one child"
        return self.children[self.selected_index]

    def process(self, event: Event) -> bool:
        assert self.children is not None, "SelectionMenu must have children"
        assert len(self.children) > 0, "SelectionMenu must have at least one child"
        if event.is_key(key.UP):
            if self.selected_index > 0:
                self.selected.apply_style(inverted=False)
                self.selected_index -= 1
                self.selected.apply_style(inverted=True)
            return True
        elif event.is_key(key.DOWN):
            if self.selected_index < len(self.children) - 1:
                self.selected.apply_style(inverted=False)
                self.selected_index += 1
                self.selected.apply_style(inverted=True)
            return True
        return False
