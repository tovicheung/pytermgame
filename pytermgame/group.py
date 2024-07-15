from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Iterable

from . import terminal

if TYPE_CHECKING:
    from .sprite import Sprite

def _ensure_not_frozen(method):
    @wraps(method)
    def replacement(self, *args, **kwargs):
        if self.frozen:
            raise Exception(f"Cannot call {method.__qualname__}() on frozen group")
        return method(self, *args, **kwargs)
    return replacement

class Group:
    frozen = False
    # note: Group.update() clashes with set.update(), so cannot subclass set[Sprite]

    def __init__(self, sprites: Iterable[Sprite] = (), frozen=False):
        # frozen: for internal use, marks frozen groups
        self.sprites = set(sprites)
        self.frozen = frozen
        if not frozen:
            for sprite in sprites:
                sprite._groups.append(self)

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
        """Calls .update() on sprites and kills zombies

        Therefore, there are two situations to call Group.update() in every game loop:
        1. your implement Sprite.update() in your sprites
        2. you kill your sprites
        """
        kills: list[Sprite] = []
        for sprite in self:
            sprite.update()
            if sprite.zombie:
                kills.append(sprite)
        while len(kills):
            # avoid making unnecessary references
            kills.pop()._kill()

    @_ensure_not_frozen
    def render(self, flush=True, erase=False):
        for sprite in self:
            sprite.render(flush=False, erase=erase)
        
        # slight optimization
        if flush:
            terminal.flush()

class SpriteList(Group):
    """List of sprites
    
    Differences from Group:
    - sprites are not aware of being in a SpriteList
        - therefore, spritelists must be destructed as soon as possible
    - order is preserved
    """

    def __init__(self, sprites: Iterable[Sprite]):
        self.sprites = list(sprites)

    # Group operations

    def add(self, *sprites: Sprite):
        self.sprites.extend(sprites)

    def extend(self, sprites: Iterable[Sprite]):
        self.sprites.extend(sprites)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            self.sprites.remove(sprite)
