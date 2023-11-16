from __future__ import annotations

from .surface import Surface
from . import terminal
from .game import Game

DEBUG = False

def ensure_game(f):
    def _new(*args, **kwargs):
        if Game._active is None:
            raise RuntimeError("Invalid call, no active game")
        return f(*args, **kwargs)
    return _new

class Sprite:
    surf: Surface
    group: Group | None = None

    def __init__(self, x: int = 0, y: int = 0):
        self._x = x
        self._y = y
        self._lx = x
        self._ly = y
        self._dirty = 0
        self.placed = False
        self.hidden = False
        self._ansi = "\033[m"
        self._groups: list[Group] = []
        self.init()

    def place(self, x: int | None = None, y: int | None = None):
        if x is not None:
            self._x = x
        if y is not None:
            self._y = y
        self._z = Game.get_active().nextz

        # add to groups
        Game.get_active().register(self)
        if self.group is not None:
            self.group.add(self)

        self._lx = self.x
        self._ly = self.y
        self._dirty = 1 # initial render
        self.placed = True
        return self # for convenient assignment: name = Sprite(...).place(...)

    def init(self):
        """called after __init__, can be customized"""

    def update(self):
        """can be customized"""

    def set_dirty(self):
        if self._dirty == 1:
            return
        self._dirty = 1
        for sprite in self.collisions:
            sprite.set_dirty()

    @property
    def collisions(self) -> list[Sprite]:
        c = []
        for sprite in Game.get_active().sprites:
            if self.touching(sprite) and sprite is not self:
                c.append(sprite)
        return c
    
    def _reveal_behind(self):
        if not self.placed:
            return
        for sprite in self.collisions:
            sprite._dirty = 1

    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y
    
    @property
    def z(self):
        return self._z
    
    @property
    def width(self):
        return self.surf.width
    
    @property
    def height(self):
        return self.surf.height
    
    def color_all(self, ansi: str):
        self._ansi = ansi

    def render(self, flush=True, erase=False):
        self._dirty = 0
        if self.hidden:
            erase = True
        if erase:
            surf = self.surf.to_blank()
            tx, ty = terminal.transform_coords(self._lx, self._ly)
        else:
            surf = self.surf
            tx, ty = terminal.transform_coords(self.x, self.y)
        for i, line in enumerate(surf.lines()):
            terminal.goto(tx, ty + i)
            terminal.write(self._ansi + line)
        terminal.write("\033[m")
        if flush:
            terminal.flush() # flush at once, not every line
        self._lx = self.x
        self._ly = self.y

    def goto(self, x, y):
        self._x = x
        self._y = y
        self.set_dirty()

    def move(self, dx, dy):
        self._x += dx
        self._y += dy
        self.set_dirty()

    def set_x(self, x):
        self._x = x
        self.set_dirty()

    def set_y(self, y):
        self._y = y
        self.set_dirty()

    def hide(self):
        self.hidden = True
        self.set_dirty()

    def show(self):
        self.hidden = False
        self.set_dirty()

    def kill(self):
        self.render(flush=False, erase=True)
        # frees all references and destroyed by garbage collector
        # tested with gc.get_referrers()
        Game.get_active().sprites.remove(self)
        for group in self._groups:
            group.remove(self)
        
        if DEBUG: # important for performance control
            import gc
            assert gc.get_referrers() == []

    def touching(self, other: Sprite):
        if other.hidden:
            return False
        if self.x >= other.x + other.width: # self at right
            return False
        if self.y >= other.y + other.height: # self at down
            return False
        if self.x + self.width <= other.x: # self at left
            return False
        if self.y + self.height <= other.y: # self at up
            return False
        return True # TODO: more precise checking (by space chars)

class Group:
    def __init__(self, *sprites: Sprite):
        self.sprites = list(sprites)

    # Group operations

    def add(self, *sprites: Sprite):
        self.sprites.extend(sprites)
        for sprite in sprites:
            sprite._groups.append(self)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            self.sprites.remove(sprite)

    def has(self, sprite: Sprite):
        return sprite in self.sprites
    
    __contains__ = has

    def __iter__(self):
        return iter(self.sprites)
    
    # Sprite operations
    
    def update(self):
        for sprite in self:
            sprite.update()

    def render(self):
        for sprite in self:
            sprite.render()
