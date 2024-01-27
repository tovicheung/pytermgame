from __future__ import annotations

from typing import TYPE_CHECKING, Iterable
from functools import wraps

from .surface import Surface
from . import terminal
from .coords import Coords, XY

if TYPE_CHECKING:
    from .scene import Scene
    from .group import Group

DEBUG = True

def active(f):
    @wraps(f)
    def _new(self: Sprite, *args, **kwargs):
        if not self.placed:
            raise RuntimeError(f"Sprite.{f.__name__}() should be called after placing it (by calling Sprite.placed())")
        if self.zombie:
            raise RuntimeError(f"this sprite is dead (zombie, waiting to be garbage collected)")
        return f(self, *args, **kwargs)
    return _new

class Sprite:
    surf: Surface
    group: Group | None = None

    def __init__(self):
        self._coords = Coords.ORIGIN
        self._oldcoords = self._coords
        self._dirty = 0
        self._ansi = "\033[m"
        self._groups: list[Group] = []
        self._scene: Scene

        # user-accessible attributes
        self.placed = False
        self.hidden = False
        self.zombie = False

        self.init()

    def place(self, scene: Scene, coords: XY = Coords.ORIGIN):
        self._scene = scene
        self._coords = Coords.make(coords)

        self._z = scene._next_z()
        scene.add(self)

        # add to groups
        if self.group is not None:
            self.group.add(self)
        self.placed = True

        self.on_placed()

        # set later so that coords can be customized at on_placed()
        self._oldcoords = self._coords
        self._dirty = 1 # initial render

        return self # for convenient assignment: name = Sprite(...).place(...)

    # Overridable hooks, these can be overridden without super()

    def init(self):
        """called AUTOMATICALLY after __init__"""

    def on_placed(self):
        """called AUTOMATICALLY after place()
        Uses: customize initial coordinates / styles
        """

    def update(self):
        """called MANUALLY, likely from group.update()"""

    @active
    def set_dirty(self):
        if self._dirty == 1:
            return
        self._dirty = 1
        for sprite in self.get_movement_collisions():
            sprite.set_dirty()

    @active
    def get_collisions(self) -> list[Sprite]:
        c = []
        for sprite in self._scene.sprites:
            if self.touching(sprite) and sprite is not self:
                c.append(sprite)
        return c

    @active
    def get_old_collisions(self) -> list[Sprite]:
        c = []
        for sprite in self._scene.sprites:
            if self.was_touching(sprite) and sprite is not self:
                c.append(sprite)
        return c
    
    @active
    def get_movement_collisions(self) -> list[Sprite]:
        """Get collisions of BOTH old and new coords"""
        c = []
        for sprite in self._scene.sprites:
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

        if tcoords.x + self.width < 1 or \
            tcoords.y + self.height < 1 or \
            tcoords.x > terminal.width() or \
            tcoords.y > terminal.height():
            return # out of screen, do nothing!

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

    @active
    def kill(self):
        self.zombie = True
        self.render(flush=False, erase=True)

    def _kill(self):
        """The only method that should be called as a zombie
        Called when it is safe to be removed from groups (not iterating)
        """
        # frees all references and destroyed by garbage collector
        # tested with gc.get_referrers()
        for group in self._groups:
            group.remove(self)
        
        # prevent sprites from not being destroyed
        if DEBUG: # important for performance control
            import gc
            assert gc.get_referrers() == []

    @active
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

    @active
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
