"""ptg.ui: build UI using sprites

Principle: build everything on top of ptg.sprite, avoid coupling normal non-UI sprites with UI attributes/methods
"""

from __future__ import annotations

from typing import Iterable, TypeVar, Generic, TYPE_CHECKING, TypeVarTuple, NamedTuple

from pytermgame import key
from pytermgame.event import Event

from .coords import Coords
from .sprite import Sprite
from .surface import Surface

_S = TypeVar("_S", bound=Sprite)
_S2 = TypeVar("_S2", bound=Sprite)

__all__ = ["Container", "OccupiedContainer", "MinSize", "MaxSize", "Padding", "Border"]

class Dimensions(NamedTuple):
    width: int | None
    height: int | None
    
    @classmethod
    def from_surf(cls, surf: Surface):
        return cls(surf.width, surf.height)
    
    @classmethod
    def from_sprite(cls, sprite: Sprite):
        return cls(sprite.surf.width, sprite.surf.height)
    
    def to_surf(self):
        assert self.width is not None
        assert self.height is not None
        return Surface.blank(self.width, self.height)

"""

Border(...).wrap(
    child
)

Column()
    .apply_style()
    .wrap(
        *children
    )

"""

class Container(Sprite, Generic[_S]):
    """Unlocks .wrap() and .child
    
    A container can be vacant or occupied."""
    
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
    
    __gt__ = wrap
    
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
        if self.child is not None and self.placed and (self._rendered.coords != self._coords or self._rendered.surf != self.surf):
            # this is here because
            # 1. coords may be modified in .set_surf() eg align right
            # 2. child needs to move with parent
            self.child.goto(*(self._coords + self.get_child_offset()))
        super().set_dirty(propagate)
    
    # Subclasses of Container must implement these:

    def new_vacant_surf(self) -> Surface:
        """Generate a new surface when self is vacant"""
        raise NotImplementedError("Subclasses of Container must implement .new_vacant_surf()")

    def new_occupied_surf(self) -> Surface:
        """Generate a new surface when self is occupied"""
        raise NotImplementedError("Subclasses of Container must implement .new_new_occupied_surf_surf()")

    def get_child_offset(self) -> Coords:
        return Coords(0, 0)
    
    def new_surf_factory(self) -> Surface:
        if self.child is None: # vacant
            return self.new_vacant_surf()
        if not self.child.placed:
            # this is currently the reason why coords is set before surf
            # should only be called in self.place()
            self.child.place(self._coords + self.get_child_offset())
        return self.new_occupied_surf()

class OccupiedContainer(Container[_S]):
    child: Sprite
    
    def new_vacant_surf(self) -> Surface:
        raise ValueError(f"{type(self).__qualname__} object must have a child")

class MinSize(OccupiedContainer[_S]):
    def __init__(self, min_width: int | None = None, min_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.min_width = min_width
        self.min_height = min_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> MinSize[_S2]: ...
    
    def get_child_coords(self) -> Coords:
        return self._coords
    
    def new_occupied_surf(self) -> Surface:
        min_width = max(self.min_width or self.child.width, self.child.width)
        min_height = max(self.min_height or self.child.height, self.child.height)
        return Surface.blank(min_width, min_height)

class MaxSize(OccupiedContainer[_S]):
    def __init__(self, max_width: int | None = None, max_height: int | None = None, child: _S | None = None):
        super().__init__(child)
        self.max_width = max_width
        self.max_height = max_height
    
    if TYPE_CHECKING:
        def wrap(self, child: _S2) -> MaxSize[_S2]: ...
    
    def get_child_coords(self) -> Coords:
        return self._coords
    
    def new_occupied_surf(self) -> Surface:
        max_width = min(self.max_width or self.child.width, self.child.width)
        max_height = min(self.max_height or self.child.height, self.child.height)
        return Surface.blank(max_width, max_height)

class Padding(OccupiedContainer[_S]):
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
    
    def new_occupied_surf(self) -> Surface:
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
    
    def get_child_offset(self) -> Coords:
        return Coords(1, 1)
    
    def new_occupied_surf(self) -> Surface:
        self.child: Sprite # for type checkers
        inner_width = self.child.width
        inner_height = self.child.height
        return Surface(
            "┌" + "─" * inner_width + "┐" + "\n"
            + ("│" + " " * inner_width + "│" + "\n") * inner_height
            + "└" + "─" * inner_width + "┘"
        )
    
    def new_vacant_surf(self) -> Surface:
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
    
    # def new_surf_factory(self) -> Surface:
    #     # self depends on child
    #     if self.child is not None:
    #     else:
    #         if self.inner_width is None:
    #             raise ValueError("Border.inner_width not supplied")
    #         if self.inner_height is None:
    #             raise ValueError("Border.inner_height not supplied")
    #         inner_width = self.inner_width
    #         inner_height = self.inner_height
    #     return Surface(
    #         "┌" + "─" * inner_width + "┐" + "\n"
    #         + ("│" + " " * inner_width + "│" + "\n") * inner_height
    #         + "└" + "─" * inner_width + "┘"
    #     )
    
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
            for child in children:
                child._parent = self
    
    def wrap(self, *children: Sprite):
        self.children = children
        for child in children:
            assert not child.placed, "children of collection should not be manually placed"
            child._parent = self
        return self
    
    def get_children(self):
        if self.children is None:
            raise ValueError("Invalid call, children are not supplied")
        return self.children
    
    def set_dirty(self, propagate=True):
        if self.children is not None and self.placed and self._rendered.dirty:
            self.build() # rebuild entire tree
        super().set_dirty(propagate)

    def get_child_offset(self) -> Coords:
        return Coords(0, 0)
    
    def build(self) -> Dimensions:
        """When this method is called, coords are guranteed to be concrete
        
        This method should:
        * receive a max_size dimensions
        * set children coords (with _set_coords(sprite, coords))
        * return self dimensions
        """
        raise NotImplementedError("Subclasses of UIElement must implement .build()")
    
    def new_surf_factory(self) -> Surface:
        return self.build().to_surf()

def _set_coords(sprite: Sprite, coords: Coords):
    if sprite.placed:
        sprite.goto(*coords)
    else:
        sprite.place(coords)

class Column(Collection):    
    def build(self) -> Dimensions:
        # this should be called in the surf stage of .place()
        # which means ._coords are present
        
        assert self.children is not None

        width = height = 0

        for child in self.children:
            _set_coords(child, self._coords.dy(height))
            height += child.height
            width = max(width, child.width)
        
        return Dimensions(width, height)

class Row(Collection):
    def build(self) -> Dimensions:
        assert self.children is not None

        width = height = 0

        for child in self.children:
            _set_coords(child, self._coords.dx(width))
            width += child.width
            height = max(height, child.height)
        
        return Dimensions(width, height)

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
