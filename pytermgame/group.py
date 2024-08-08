from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Iterable, Literal, overload

from . import terminal

if TYPE_CHECKING:
    from .collidable import Collidable
    from .sprite import Sprite

def _ensure_not_frozen(method):
    @wraps(method)
    def replacement(self: Group, *args, **kwargs):
        if self.frozen:
            raise Exception(f"Cannot call {method.__qualname__}() on frozen group")
        return method(self, *args, **kwargs)
    return replacement

class Group:
    # note: Group.update() clashes with set.update(), so cannot subclass set[Sprite]
    
    frozen = False

    @overload
    def __init__(self, sprites: Iterable[Collidable] = (), name: str | None = None, frozen: Literal[True] = True): ...
    @overload
    def __init__(self, sprites: Iterable[Sprite] = (), name: str | None = None, frozen: Literal[False] = False): ...
    def __init__(self, sprites = (), name = None, frozen = False):
        # name: used in __repr__ in errors
        # frozen: group contains Collidables that are not Sprites
        self.sprites = set(sprites)
        self.frozen = frozen
        self.name = name
        if not frozen:
            for sprite in sprites:
                sprite._groups.append(self)
    
    def __repr__(self):
        if self.name is None:
            return super().__repr__()
        return f"{type(self).__qualname__} object named '{self.name}'"

    # Group operations

    @_ensure_not_frozen
    def add(self, *sprites: Sprite):
        self.sprites.update(sprites)
        for sprite in sprites:
            sprite._groups.append(self)

    @_ensure_not_frozen
    def extend(self, sprites: Iterable[Sprite]):
        self.sprites.update(sprites)

    @_ensure_not_frozen
    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            self.sprites.remove(sprite)
            sprite._groups.remove(self)

    def has(self, sprite: Sprite):
        return sprite in self.sprites
    
    __contains__ = has

    def __iter__(self):
        return iter(self.sprites)
    
    def __len__(self):
        return len(self.sprites)
    
    # Sprite operations
    
    @_ensure_not_frozen
    def update(self):
        """Calls .update() on sprites"""
        for sprite in self:
            sprite.update()

    @_ensure_not_frozen
    def render(self, flush=True, erase=False):
        for sprite in self:
            sprite.render(flush=False, erase=erase)

        if flush:
            terminal.flush()

class SpriteList(Group):
    """Ordered group of sprites"""

    def __init__(self, sprites: Iterable[Sprite], name: str | None = None):
        self.sprites = list(sprites)
        self.name = name

    # Group operations

    def add(self, *sprites: Sprite):
        self.sprites.extend(sprites)
        for sprite in sprites:
            sprite._groups.append(self)

    def extend(self, sprites: Iterable[Sprite]):
        self.sprites.extend(sprites)
        for sprite in sprites:
            sprite._groups.append(self)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            self.sprites.remove(sprite)
            sprite._groups.remove(self)
