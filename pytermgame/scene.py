from __future__ import annotations

from .coords import Coords, XY
from . import cursor, terminal
from .group import SpriteList

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .surface import Surface
    from .sprite import Sprite

def _iter_coords(coords: Coords, surf: Surface):
    for y in range(int(coords.y), int(coords.y)+surf.height):
        for x in range(int(coords.x), int(coords.x)+surf.width):
            yield (x, y)

# [future: collision]
if False:
    class OccupancyMatrix(defaultdict[tuple[int, int], set[Sprite]]):
        def __init__(self):
            super().__init__(lambda: set())

        def get_collisions(self, coords: Coords, surf: Surface):
            for (x, y) in _iter_coords(coords, surf):
                yield from filter(lambda x: not x.hidden, self[(x, y)])
        
        def add(self, sprite: Sprite):
            # add sprite and return collisions as byproduct
            collisions = set()
            for (x, y) in _iter_coords(sprite._coords, sprite.surf):
                collisions.update(self[(x, y)])
                self[(x, y)].add(sprite)
            return collisions
        
        def remove(self, sprite: Sprite):
            for (x, y) in _iter_coords(sprite._rendered.coords, sprite._rendered.surf):
                if sprite in self[(x, y)]:
                    self[(x, y)].remove(sprite)

class Scene(SpriteList):
    """A scene is essentially a list of sprites ordered by z-coordinate. (and also a cursor)"""

    # IMPORTANT: +Z is top, -Z is bottom

    _active_context: Scene | None = None

    def __init__(self):
        super().__init__((), name = "Scene")

        self.offset = Coords.ORIGIN

        # [future: collision]
        # self.mat = OccupancyMatrix()
    
    def get_dirty(self):
        """Get the SpriteList sorted by z-coordinate (bottom to top)"""
        yield from filter(lambda sp: sp._rendered.dirty, self.sprites)
    
    def rerender(self):
        """Erases and re-renders dirty sprites.
        Not to be confused with Scene.render(), it only calls .render() on all sprites.
        """
        dirty = tuple(self.get_dirty())

        if len(dirty) == 0: # prevents rapid cursor blinks
            if cursor.state.dirty:
                cursor.write_ansi()
                terminal.flush()
            return
        
        terminal.hide_cursor(flush=True)
        for dirty_sprite in dirty:
            dirty_sprite.render(flush=False, erase=True)
        for dirty_sprite in dirty:
            dirty_sprite.render(flush=False, erase=False)
        # flush once after all the rendering
        cursor.write_ansi()
        terminal.flush()
    
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

    def _next_z(self):
        """called by sprites to get the next available z-coordinate"""
        return len(self.sprites)
    
    # Context manager for easy sprite creation and placement

    def __enter__(self):
        if Scene._active_context is not None:
            raise Exception("Cannot enter more than one scene")
        Scene._active_context = self
        return self
    
    def __exit__(self, typ, val, tb):
        Scene._active_context = None

    def apply_scroll(self, coords: Coords):
        return coords.d(-self.offset)
    
    def scroll(self, dx: int = 0, dy: int = 0):
        self.offset = self.offset.d((dx, dy))
        if dx != 0 or dy != 0:
            for sprite in self:
                # no need to propagate since we are setting for all sprites
                sprite.set_dirty(propagate=False)
    
    def set_scroll(self, offset: XY):
        self.offset = Coords.coerce(offset)
    
    # Sprite ordering

    def move_sprite_to_below(self, sprite_to_move: Sprite, reference_sprite: Sprite):
        if sprite_to_move not in self.sprites:
            raise ValueError("sprite to move is not in sprites")
        if reference_sprite not in self.sprites:
            raise ValueError("reference sprite is not in sprites")
        
        old_index = self.sprites.index(sprite_to_move)
        new_index = self.sprites.index(reference_sprite)
        
        # self.sprites.insert(self.sprites.index(reference_sprite), self.sprites.pop(self.sprites.index(sprite_to_move)))
        self.sprites.insert(new_index, self.sprites.pop(old_index))

        for i in range(old_index, new_index+1):
            self.sprites[i]._z = i


