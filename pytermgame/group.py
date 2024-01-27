from __future__ import annotations
from typing import TYPE_CHECKING, Iterable

from . import terminal

if TYPE_CHECKING:
    from .sprite import Sprite

class Group:
    # note: Group.update() clashes with set.update(), so cannot subclass set[Sprite]

    def __init__(self, sprites: Iterable[Sprite] = ()):
        self.sprites = set(sprites)
        for sprite in sprites:
            sprite._groups.append(self)

    # Group operations

    def add(self, *sprites: Sprite):
        self.sprites.update(sprites)
        for sprite in sprites:
            sprite._groups.append(self)

    def extend(self, sprites: Iterable[Sprite]):
        self.sprites.update(sprites)

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
    
    def update(self):
        kills: list[Sprite] = []
        for sprite in self:
            sprite.update()
            if sprite.zombie:
                kills.append(sprite)
        while len(kills):
            # avoid making unnecessary references
            kills.pop()._kill()

    def render(self, flush=True, erase=False):
        for sprite in self:
            sprite.render(flush=False, erase=erase)
        
        # slight optimization
        if flush:
            terminal.flush()

class SpriteList(Group):
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
