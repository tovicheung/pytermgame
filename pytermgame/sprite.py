from __future__ import annotations

from typing import TYPE_CHECKING, Generator
from functools import wraps

from .surface import Surface, SurfaceLike
from . import terminal, _active
from .coords import Coords, XY
from .scene import Scene

if TYPE_CHECKING:
    from .group import Group

DEBUG = True

LEFT = 0
RIGHT = 1

def ensure_placed(f):
    """Ensures that the method is called only after placing the sprite
    
    Attributes only available after placing:
    * sprite._scene
    * sprite._z
    * sprite._coords (initially 0, 0)
    """
    @wraps(f)
    def _new(self: Sprite, *args, **kwargs):
        if not self.placed:
            raise RuntimeError(f"Sprite.{f.__name__}() should be called after placing it (by calling Sprite.place())")
        if self.zombie:
            raise RuntimeError(f"this sprite is dead (zombie, waiting to be garbage collected)")
        return f(self, *args, **kwargs)
    return _new

class Sprite:
    """
    States a sprite can be in
    - abstract: sprite is not attached to a scene
    - placed: sprite is attached to a scene
    - zombie: sprite is no longer on screen, but object still exists in memory

    The respective methods are .__init__(), .place(), and .kill().
    """

    surf: Surface # needs to be specified by subclasses
    group: Group | None = None

    def __init__(self):
        self._coords = Coords.ORIGIN
        self._dirty = 0 # object requires rerender?
        self._ansi = "\033[m"
        self._groups: list[Group] = []
        self._scene: Scene

        # old = last rendered
        self._oldcoords = self._coords
        self._oldsurf: Surface # set at .place()

        # user-accessible attributes
        self.placed = False
        self.hidden = False
        self.zombie = False

        # modifiers
        self.align_horizontal = LEFT

        self.init()

    def place(self, coords: XY = Coords.ORIGIN, scene: Scene | None = None):
        """After placing a sprite, it:
        - is attached to a scene
        - has XYZ coordinates on the scene
        - calls .on_placed(), which can be overriden by subclasses freely
        - unlocks methods such as .move()
        - can be killed via .kill()
        """

        if scene is None:
            if Scene._active_context is not None:
                scene = Scene._active_context
            else:
                scene = _active.get_scene()
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
        self._oldsurf = self.surf
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
        """called MANUALLY, often from group.update() or game.update()
        Users are free to customize the behaviour of .update() in their sprites.
        """

    @ensure_placed
    def set_dirty(self):
        if self._dirty == 1:
            return
        self._dirty = 1
        for sprite in self.get_movement_collisions():
            sprite.set_dirty()

    @ensure_placed
    def get_collisions(self) -> Generator[Sprite, None, None]:
        for sprite in self._scene.sprites:
            if self.touching(sprite) and sprite is not self:
                yield sprite

    @ensure_placed
    def get_old_collisions(self) -> Generator[Sprite, None, None]:
        for sprite in self._scene.sprites:
            if self.was_touching(sprite) and sprite is not self:
                yield sprite
    
    @ensure_placed
    def get_movement_collisions(self) -> Generator[Sprite, None, None]:
        """Get collisions of BOTH old and new coords"""
        for sprite in self._scene.sprites:
            if self.touching(sprite) or self.was_touching(sprite) and sprite is not self:
                yield sprite

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
        return self
    
    def apply_modifiers(self):
        """Modifies coords and surfs, returns whether an erase of the old surf is needed"""
        if self.align_horizontal == RIGHT and self.surf.width != self._oldsurf.width:
            self._coords = self._coords.dx(-(self.surf.width - self._oldsurf.width))
            self._render(flush=False, erase=True, _surf=self._oldsurf)
    
    def _render(self, flush=True, erase=False, _surf=None):

        if self.hidden:
            erase = True

        surf = self.surf
        if _surf is not None:
            surf = _surf

        if erase:
            surf = surf.to_blank()
            tcoords = self._oldcoords.to_term()
        else:
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


    def render(self, flush=True, erase=False, _surf=None):
        self._dirty = 0

        self.apply_modifiers()
        
        self._render(flush, erase, _surf)
        
        self._oldcoords = self._coords
        self._oldsurf = self.surf

    def goto(self, x, y):
        self._coords = Coords(x, y)
        self.set_dirty()

    def bound(self, x_min: int | None = None, x_max: int | None = None, y_min: int | None = None, y_max: int | None = None):
        if x_min is not None and self.x < x_min:
            self.set_x(x_min)
        if x_max is not None and self.x > x_max:
            self.set_x(x_max)
        if y_min is not None and self.y < y_min:
            self.set_y(y_min)
        if y_max is not None and self.y > y_max:
            self.set_y(y_max)

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

    @ensure_placed
    def kill(self):
        """Set the sprite as a zombie and erases it from the scene.
    
        Zombies are truly killed in Group.update() via Sprite._kill() (see below)
        Therefore, it is recommended to use Sprite.kill() in Sprite.update()
        """
        self.zombie = True
        self.render(flush=False, erase=True)

    def _kill(self):
        """Truly kills a sprite, should only call as zombie."""

        # frees all references and destroyed by garbage collector
        for group in self._groups:
            group.remove(self)
        
        # prevent sprites from not being destroyed (important for performance)
        if DEBUG:
            import gc
            assert gc.get_referrers() == []

    @ensure_placed
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

    @ensure_placed
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
    
    def align_right(self):
        self.align_horizontal = RIGHT
        return self

def Object(surf: SurfaceLike):
    """Short singular sprite creator
    
    usage:
    >>> myarrow = ptg.Object(ptg.Surface("--->"))
    >>> myarrow = ptg.Object("--->")
    """
    sprite = Sprite()
    sprite.surf = Surface.coerce(surf)
    return sprite
