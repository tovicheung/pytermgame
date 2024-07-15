from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable, TYPE_CHECKING

from .group import Group
from . import terminal

if TYPE_CHECKING:
    from .sprite import Sprite

@runtime_checkable
class Collidable(Protocol):
    # should not be called by user
    def _is_colliding_base(self, other: Sprite): ...

class _ScreenTop(Collidable):
    def _is_colliding_base(self, other: Sprite):
        return other.y < 0

class _ScreenBottom(Collidable):
    def _is_colliding_base(self, other: Sprite):
        return other.y + other.height > terminal.height()

class _ScreenLeft(Collidable):
    def _is_colliding_base(self, other: Sprite):
        return other.x < 0

class _ScreenRight(Collidable):
    def _is_colliding_base(self, other: Sprite):
        return other.x + other.width > terminal.width()

class ScreenEdges:
    top = _ScreenTop()
    bottom = _ScreenBottom()
    left = _ScreenLeft()
    right = _ScreenRight()

screen = Group((ScreenEdges.top, ScreenEdges.bottom, ScreenEdges.left, ScreenEdges.right), frozen=True)
