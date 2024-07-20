from __future__ import annotations

from . import terminal
from .coords import Coords, XY
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

# for a future update
if False:
    class OccupancyMatrix(defaultdict[tuple[int, int], set]):
        def __init__(self):
            super().__init__(lambda: set())

        def get_collisions(self, coords: Coords, surf: Surface):
            for (x, y) in _iter_coords(coords, surf):
                yield from self[(x, y)]
        
        def add(self, sprite: Sprite):
            # add sprite and return collisions as byproduct
            collisions = set()
            for (x, y) in _iter_coords(sprite._coords, sprite.surf):
                collisions.update(self[(x, y)])
                self[(x, y)].add(sprite)
            return collisions
        
        def remove(self, sprite: Sprite):
            for (x, y) in _iter_coords(sprite._oldcoords, sprite._oldsurf):
                if sprite in self[(x, y)]:
                    self[(x, y)].remove(sprite)

class Scene(SpriteList):
    """A scene is essentially a list of sprites ordered by z-coordinate."""

    # IMPORTANT: +Z is top, -Z is bottom

    _active_context: Scene | None = None

    def __init__(self):
        super().__init__((), name = "Scene")

        # self.mat = OccupancyMatrix()

        # unused for now
        self.offset = Coords.ORIGIN
    
    def get_dirty(self):
        """Get the SpriteList sorted by z-coordinate (bottom to top)"""
        yield from filter(lambda sp: sp._dirty, self.sprites)
    
    def rerender(self):
        """Erases and re-renders dirty sprites.
        Not to be confused with Scene.render(), it only calls .render() on all sprites.
        """
        dirty = tuple(self.get_dirty())
        for dirty_sprite in dirty:
            dirty_sprite.render(flush=False, erase=True)
        for dirty_sprite in dirty:
            dirty_sprite.render(flush=False, erase=False)
        # flush once after all the rendering
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
    
    # Context manager for easy sprite creation amd placement

    def __enter__(self):
        if Scene._active_context is not None:
            raise Exception("Cannot enter more than one scene")
        Scene._active_context = self
        return self
    
    def __exit__(self, typ, val, tb):
        Scene._active_context = None

    # Testing: scrolling

    def absolute(self, coords: Coords):
        # unused for now
        return coords.d(self.offset)

    def scroll(self, dx: int = 0, dy: int = 0):
        self.offset = self.offset.d((dx, dy))

    def set_scroll(self, offset: XY):
        self.offset = Coords.coerce(offset)
