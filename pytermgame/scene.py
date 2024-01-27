from .coords import Coords, XY
from .group import Group, SpriteList
from . import terminal

class Scene(Group):
    def __init__(self):
        super().__init__()

        self.offset = Coords.ORIGIN

    def scroll(self, dx: int = 0, dy: int = 0):
        self.offset = self.offset.d((dx, dy))

    def set_scroll(self, offset: XY):
        self.offset = Coords.make(offset)

    def absolute(self, coords: Coords):
        return coords.d(self.offset)
    
    def get_dirty(self) -> Group:
        return SpriteList(sorted(filter(lambda sprite: sprite._dirty, self.sprites), key=lambda sprite: sprite.z))
    
    def rerender(self):
        dirty = self.get_dirty()
        dirty.render(flush=False, erase=True)
        dirty.render(flush=False)
        # flush once after all the rendering
        terminal.flush()

    def _next_z(self):
        return len(self.sprites)
