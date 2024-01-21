from __future__ import annotations

from .surface import Surface
from . import terminal
from .game import Game
from .coords import Coords, XY

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

    def __init__(self):
        self._coords = Coords.ORIGIN
        self._oldcoords = self._coords
        # self._x = x
        # self._y = y
        # self._lx = x
        # self._ly = y
        self._dirty = 0
        self._ansi = "\033[m"
        self._groups: list[Group] = []

        # user-accessible attributes
        self.placed = False
        self.hidden = False

        self.init()

    def place(self, coords: XY = Coords.ORIGIN):
        self._coords = Coords.make(coords)

        self._z = Game.get_active().nextz

        # add to groups
        Game.get_active().register(self)
        if self.group is not None:
            self.group.add(self)
        self.placed = True

        self.on_placed()

        # set later so that coords can be customized at on_placed()
        self._oldcoords = self._coords
        self._dirty = 1 # initial render

        return self # for convenient assignment: name = Sprite(...).place(...)

    def init(self):
        """called after __init__, can be customized"""

    def on_placed(self):
        """called after place, can be customized"""

    def update(self):
        """called manually from gruops, can be customized"""

    def set_dirty(self):
        if self._dirty == 1:
            return
        self._dirty = 1
        for sprite in self.get_movement_collisions():
            sprite.set_dirty()

    def get_collisions(self) -> list[Sprite]:
        c = []
        for sprite in Game.get_active().sprites:
            if self.touching(sprite) and sprite is not self:
                c.append(sprite)
        return c

    def get_old_collisions(self) -> list[Sprite]:
        c = []
        for sprite in Game.get_active().sprites:
            if self.was_touching(sprite) and sprite is not self:
                c.append(sprite)
        return c
    
    def get_movement_collisions(self) -> list[Sprite]:
        """Get collisions of BOTH old and new coords"""
        c = []
        for sprite in Game.get_active().sprites:
            if self.touching(sprite) or self.was_touching(sprite) and sprite is not self:
                c.append(sprite)
        return c

    @property
    def x(self):
        return self._coords.x
    
    @property
    def y(self):
        return self._coords.y
    
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
            tcoords = self._oldcoords.to_term()
        else:
            surf = self.surf
            tcoords = self._coords.to_term()

        for i, line in enumerate(surf.lines()):
            terminal.goto(*tcoords.dy(i))
            terminal.write(self._ansi + line)

        terminal.write("\033[m")

        if flush:
            terminal.flush() # flush at once, not every line
        
        self._oldcoords = self._coords

    def goto(self, x, y):
        self._coords = Coords(x, y)
        self.set_dirty()

    def move(self, dx, dy):
        self._coords = self._coords.dx(dx).dy(dy)
        self.set_dirty()

    def set_x(self, x):
        self._coords = self._coords.setx(x)
        self.set_dirty()

    def set_y(self, y):
        self._coords = self._coords.sety(y)
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
        
        # prevent sprites from not being destroyed
        if DEBUG: # important for performance control
            import gc
            assert gc.get_referrers() == []

    def was_touching(self, other: Sprite):
        if other.hidden:
            return False
        if self._oldcoords.x >= other.x + other.width: # self at right
            return False
        if self._oldcoords.y >= other.y + other.height: # self at down
            return False
        if self._oldcoords.x + self.width <= other.x: # self at left
            return False
        if self._oldcoords.y + self.height <= other.y: # self at up
            return False
        return True


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
        return True

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
