from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Generator, Iterable, NamedTuple, TypeAlias

from . import _active, terminal

if TYPE_CHECKING:
    from .coords import Coords
    from .sprite import Sprite
    from .surface import Surface

class Collidable:
    """Represents anything that can be collided by a sprite
    (or more precisely, collided by a set of coordinates and a surface)"""

    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface) -> bool:
        raise NotImplementedError("Subclasses of Collidable must implement ._is_colliding_raw()")

    def _is_colliding_sprite(self, other: Sprite, old: bool = False) -> bool:
        if (not old) and other.hidden:
            return False
        if old and (not other._rendered.on_screen):
            return False
        return self._is_colliding_raw(other._rendered.coords if old else other._coords, other._rendered.surf)

class _ScreenTop(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface) -> bool:
        return _active.get_scene().apply_scroll(other_coords).y < 0

class _ScreenBottom(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface) -> bool:
        return _active.get_scene().apply_scroll(other_coords).y + other_surf.height > terminal.height()

class _ScreenLeft(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface) -> bool:
        return _active.get_scene().apply_scroll(other_coords).x < 0

class _ScreenRight(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface) -> bool:
        return _active.get_scene().apply_scroll(other_coords).x + other_surf.width > terminal.width()

class _Viewport(NamedTuple):
    top: _ScreenTop = _ScreenTop()
    bottom: _ScreenBottom = _ScreenBottom()
    left: _ScreenLeft = _ScreenLeft()
    right: _ScreenRight = _ScreenRight()

viewport = _Viewport()

# Helpers

NestedCollidables: TypeAlias = "Collidable | Iterable[Collidable | NestedCollidables]"

def flatten_collidables(nested_collidables: NestedCollidables) -> Generator[Collidable]:
    if isinstance(nested_collidables, Collidable):
        yield nested_collidables
        return
    if isinstance(nested_collidables, Iterable):
        for x in nested_collidables:
            yield from flatten_collidables(x)
        return
    raise TypeError(f"Argument must be collidable or nested iterables of collidables, got {nested_collidables}")

_real_flatten_collidables = flatten_collidables

# set by Game
@lru_cache
def _flatten_collidables_cached(nested_collidables: NestedCollidables) -> list[Collidable]:
    return list(_real_flatten_collidables(nested_collidables))
