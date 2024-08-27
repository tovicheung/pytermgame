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
from typing import Callable, Iterable, TypeVar, Generic, TYPE_CHECKING, NamedTuple, overload

if sys.version_info >= (3, 11):
    from typing import Self

# some methods of Sprite are overriden and it is best to mark them
if sys.version_info >= (3, 12):
    from typing import override
else:
    def override(f):
        return f

from . import key
from .coords import Coords
from .event import Event
from .sprite import Parent, Sprite
from .surface import Surface

_S = TypeVar("_S", bound=Sprite)
_S2 = TypeVar("_S2", bound=Sprite)

# only export stable sprites
__all__ = ["Container", "MinSize", "MaxSize", "Padding", "Border"]

# Helpers

def place_or_set_coords(sprite: Sprite, coords: Coords):
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

# Base classes

class Container(Parent, Generic[_S]):    
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
    
    def has_child(self, child: Sprite) -> bool:
        return child is self.child
    
    def remove_child(self, child: Sprite) -> None:
        if not self.has_child(child):
            raise ValueError(f"Parent {self} does not have child {child}")
        child._parent = None
        self.child = None
        self.update_surf()
    
    def get_inner_dimensions(self) -> tuple[int, int]:
        if self.child is None:
            return 0, 0
        return self.child.width, self.child.height
    
    @override # TODO: add type support
    def apply_style(self, *args, **kwargs):
        super().apply_style(*args, **kwargs)
        if self.child is not None:
            self.child._resolved_style = None
        return self
    
    @override
    def set_dirty(self):
        super().set_dirty()
        if self.child is not None and self.placed and self._rendered.coords != self._coords:
            # this is here because
            # 1. coords may be modified in .set_surf() eg align right
            # 2. child needs to move when (a) parent moves and (b) parent surf changes (eg padding change)
            self.child.goto(*(self._coords + self.get_child_offset()))
    
    @override
    def update_surf(self):
        if self.child is not None:
            # this is currently the reason why coords is set before surf
            # should only be called in self.place()
            place_or_set_coords(self.child, self._coords + self.get_child_offset())
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

class Collection(Parent):
    children: tuple[Sprite, ...] | None
    
    def __init__(self, children: Iterable[Sprite] | None = None):
        super().__init__()
        self.children = None
        if children is not None:
            self.children = tuple(children)
            for child in children:
                child._parent = self
    
    @overload
    def wrap(self, children: Iterable[Sprite]) -> Self: ...
    @overload
    def wrap(self, *children: Sprite) -> Self: ...
    def wrap(self, children: Iterable[Sprite] | Sprite, *other_args: Sprite):
        if isinstance(children, Iterable):
            children = tuple(children)
        else:
            children = (children,) + other_args
        self.children = children
        for child in children:
            child._parent = self
        return self
    
    def has_child(self, child: Sprite) -> bool:
        return self.children is not None and child is self.children
    
    def remove_child(self, child: Sprite) -> None:
        if not self.has_child(child):
            raise ValueError(f"Parent {self} does not have child {child}")
        child._parent = None
        assert self.children is not None # for typing
        index = self.children.index(child)

        self.children = self.children[:index] + self.children[index+1:]
        self.update_surf()

    def get_children(self):
        if self.children is None:
            raise ValueError("Invalid call, children are not supplied")
        return self.children
    
    def insert_child(self, child: Sprite, position: int | None = None):
        if self.children is None:
            raise ValueError("Invalid call, children are not supplied")
        if child._parent is not None:
            raise ValueError(f"Child already has parent: {child._parent}")
        child._parent = self

        if position is None:
            position = len(self.children)

        self.children = self.children[:position] + (child,) + self.children[position:]
        self.update_surf()
    
    @override # TODO: add type support
    def apply_style(self, *args, **kwargs):
        super().apply_style(*args, **kwargs)
        for child in self.get_children():
            child._resolved_style = None
        return self
    
    @override
    def set_dirty(self):
        super().set_dirty()
        if self.children is not None and self.placed and self._rendered.coords != self._coords:
            delta = self._coords - self._rendered.coords
            for child in self.children:
                child.goto(*(child._rendered.coords + delta))
    
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

# Containers

class MinSize(Container[_S]):
    def __init__(self, min_width: int | None = None, min_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.min_width = min_width
        self.min_height = min_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> MinSize[_S2]: ...

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

# Collections

class Column(Collection):    
    def new_surf_factory(self):
        width = height = 0

        for child in self.get_children():
            place_or_set_coords(child, self._coords.dy(height))
            height += child.height
            width = max(width, child.width)
        
        return Surface.phantom(width, height)

class Row(Collection):
    def new_surf_factory(self):
        width = height = 0

        for child in self.get_children():
            place_or_set_coords(child, self._coords.dx(width))
            width += child.width
            height = max(height, child.height)
        
        return Surface.phantom(width, height)

class SelectionMenu(Column):
    def on_placed(self):
        self.selected_index = 0
        self.selected.apply_style(inverted=True)

    @property
    def selected(self):
        return self.get_children()[self.selected_index]

    def process(self, event: Event) -> bool:
        if event.is_key(key.UP):
            if self.selected_index > 0:
                self.selected.apply_style(inverted=False)
                self.selected_index -= 1
                self.selected.apply_style(inverted=True)
            return True
        elif event.is_key(key.DOWN):
            if self.selected_index < len(self.get_children()) - 1:
                self.selected.apply_style(inverted=False)
                self.selected_index += 1
                self.selected.apply_style(inverted=True)
            return True
        return False

class TileMap(Collection, Generic[_S]):
    children: tuple[_S, ...]

    if TYPE_CHECKING:
        def get_children(self) -> tuple[_S, ...]: ...

    def __init__(self, cols: int, rows: int, children: Iterable[_S] | None = None):
        super().__init__(children)
        self.cols = cols
        self.rows = rows
        if children is not None:
            assert len(self.get_children()) == cols * rows, f"Size mismatch, expected {cols}x{rows}={cols * rows}, got {len(self.get_children())}"
    
    @classmethod
    def from_factory(cls, cols: int, rows: int, children_factory: Callable[[int, int], _S2]) -> TileMap[_S2]:
        children = [children_factory(x, y) for y in range(rows) for x in range(cols)]
        return cls(cols, rows, children) # type: ignore

    def on_placed(self):
        self.selected_index = 0
        self.selected.apply_style(inverted=True)
    
    def get(self, col: int, row: int):
        return self.get_children()[row * self.cols + col]
    
    def get_adjacent(self, col: int, row: int, edges: bool = True, corners: bool = True):
        if row > 0:
            if edges: yield self.get(col, row - 1)
            if col > 0:
                if corners: yield self.get(col - 1, row - 1)
            if col < self.cols - 1:
                if corners: yield self.get(col + 1, row - 1)

        if row < self.rows - 1:
            if edges: yield self.get(col, row + 1)
            if col > 0:
                if corners: yield self.get(col - 1, row + 1)
            if col < self.cols - 1:
                if corners: yield self.get(col + 1, row + 1)
        
        if col > 0:
            if edges: yield self.get(col - 1, row)
        if col < self.cols - 1:
            if edges: yield self.get(col + 1, row)

    @property
    def selected(self):
        return self.get_children()[self.selected_index]

    def process(self, event: Event) -> bool:
        if event.is_key(key.UP):
            if self.selected_index >= self.cols:
                self.selected.apply_style(inverted=False)
                self.selected_index -= self.cols
                self.selected.apply_style(inverted=True)
            return True
        elif event.is_key(key.DOWN):
            if self.selected_index < len(self.get_children()) - self.cols:
                self.selected.apply_style(inverted=False)
                self.selected_index += self.cols
                self.selected.apply_style(inverted=True)
            return True
        elif event.is_key(key.LEFT):
            if self.selected_index % self.cols != 0:
                self.selected.apply_style(inverted=False)
                self.selected_index -= 1
                self.selected.apply_style(inverted=True)
        elif event.is_key(key.RIGHT):
            if self.selected_index % self.cols != self.cols - 1:
                self.selected.apply_style(inverted=False)
                self.selected_index += 1
                self.selected.apply_style(inverted=True)
        return False
    
    def new_surf_factory(self) -> Surface:
        # child_width, child_height = self.get_children()[0].surf.get_dimensions()
        width = height = 0

        children = self.get_children()
        child_coords = self._coords

        for row in range(self.rows):
            max_height = 0
            total_width = 0

            for col in range(self.cols):
                child = children[row * self.cols + col]
                place_or_set_coords(child, child_coords)

                child_coords = child_coords.dx(child.width)
                total_width += child.width
                max_height = max(max_height, child.height)
            
            child_coords = child_coords.dy(max_height).with_x(self._coords.x)
            width = max(width, total_width)
            height += max_height
        
        return Surface.phantom(width, height)

