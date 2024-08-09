from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from . import terminal

if TYPE_CHECKING:
    from .sprite import Sprite

class Group:
    # note: Group.update() clashes with set.update(), so cannot subclass set[Sprite]
    
    def __init__(self, sprites: Iterable[Sprite] = (), name: str | None = None):
        # name: used in __repr__ in errors
        self.sprites = set(sprites)
        self.name = name
        for sprite in sprites:
            sprite._groups.append(self)
    
    def __repr__(self):
        if self.name is None:
            return f"Group({repr(self.sprites)})"
        return f"<Group {self.name}>"

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
            sprite._groups.remove(self)

    def has(self, sprite: Sprite):
        return sprite in self.sprites
    
    __contains__ = has

    def __iter__(self):
        return iter(self.sprites)
    
    def __len__(self):
        return len(self.sprites)
    
    # Sprite operations

    def update(self):
        """Calls .update() on sprites"""
        for sprite in self:
            sprite.update()

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
