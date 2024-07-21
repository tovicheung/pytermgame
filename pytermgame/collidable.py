from __future__ import annotations

from typing import TYPE_CHECKING

from . import terminal
from .group import Group

if TYPE_CHECKING:
    from .coords import Coords
    from .sprite import Sprite
    from .surface import Surface

class Collidable:
    # should not be called by user

    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        raise NotImplementedError("Subclasses of Collidable must implement ._is_colliding_raw()")

    def _is_colliding_sprite(self, other: Sprite, old=False):
        return self._is_colliding_raw(other._rendered.coords if old else other._coords, other.surf)

class _ScreenTop(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        return other_coords.y < 0

class _ScreenBottom(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        return other_coords.y + other_surf.height > terminal.height()

class _ScreenLeft(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        return other_coords.x < 0

class _ScreenRight(Collidable):
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        return other_coords.x + other_surf.width > terminal.width()

class ScreenEdge:
    top = _ScreenTop()
    bottom = _ScreenBottom()
    left = _ScreenLeft()
    right = _ScreenRight()

screen = Group((ScreenEdge.top, ScreenEdge.bottom, ScreenEdge.left, ScreenEdge.right), frozen=True)
