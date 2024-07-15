from __future__ import annotations

from fractions import Fraction
from functools import wraps
from math import floor
from typing import Iterable, Generator

from . import terminal, _active
from .collidable import Collidable
from .coords import Coords, XY
from .group import Group
from .scene import Scene
from .surface import Surface, SurfaceLike

DEBUG = False

UP = TOP = 1
DOWN = BOTTOM = 2
LEFT = 4
RIGHT = 8

def _ensure_placed(f):
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
            raise RuntimeError(f"Sprite.{f.__name__}() should not be called when the sprite is dead (zombie, waiting to be garbage collected)")
        return f(self, *args, **kwargs)
    return _new

def _iter_sprites(sprite_or_sprites: Sprite | Group | Iterable[Sprite | Group]):
    # technically Group is a subclass of Iterable[Sprite]
    if isinstance(sprite_or_sprites, Collidable):
        yield sprite_or_sprites
        return
    for x in sprite_or_sprites:
        yield from _iter_sprites(x)

class Sprite(Collidable):
    """
    A sprite must have a surface at all times.
    For special objects without a surface (eg screen edges) see `ptg.collidable`

    Functional states of a sprite:
    - abstract: sprite is not attached to a scene
    - placed: sprite is attached to a scene with coordinates
    - zombie: sprite is no longer on screen, but object still exists in memory

    The respective methods are `.__init__()`, `.place()`, and `.kill()`.

    Game states of a sprite:
    - hidden: sprite is not visible, no collisions
        - methods: `.hide()` and `.show()`
    - virtual: collisions do not affect other sprites
        - use case: test if a movement will cause collision
        - note: a sprite should not be kept virtual across ticks
        - method: `.virtual()`
    """

    # To be specified by subclasses
    surf: Surface

    # If set to a Group(), automatically add instances to the group
    group: Group | None = None

    def __init__(self):
        self._coords = Coords.ORIGIN
        self._dirty = False # object requires rerender?
        self._ansi = "\033[m"
        self._groups: list[Group] = []
        self._scene: Scene

        # old = last rendered
        self._oldcoords = self._coords
        self._oldsurf: Surface # set at .place()

        self._virtual = False

        # user-accessible attributes
        self.placed = False
        self.hidden = False
        self.zombie = False

        # modifiers
        self.align_horizontal = LEFT

        self.init()
    
    # State conversion methods

    def place(self, coords: XY = Coords.ORIGIN, scene: Scene | None = None):
        """After a sprite is being placed, it:
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
        scene.add(self)
    
        self._coords = Coords.coerce(coords)
        self._z = scene._next_z()

        # add to groups
        if isinstance(self.group, Group):
            self.group.add(self)

        self.placed = True

        self.on_placed()

        # set later so that coords can be customized at on_placed()
        self._oldcoords = self._coords
        self._oldsurf = self.surf
        self._dirty = True # initial render

        return self

    def kill(self):
        """Set the sprite as a zombie and erases it from the scene.
    
        Zombies are truly killed in Group.update() via Sprite._kill() (see below)
        Therefore, it is recommended to use Sprite.kill() in Sprite.update()
        """
        self.render(flush=False, erase=True)
        self.zombie = True

    def _kill(self):
        """Truly kills a sprite, should only call as zombie."""

        # frees all references and destroyed by garbage collector
        for group in self._groups:
            group.remove(self)
        
        # prevent sprites from not being destroyed (important for performance)
        if DEBUG:
            import gc
            assert gc.get_referrers() == []

    # Methods subclasses can override

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

    # Properties of a sprite

    @property
    def x(self):
        return floor(self._coords.x)
    
    @property
    def y(self):
        return floor(self._coords.y)
    
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
    
    # Rendering

    def _apply_modifiers(self):
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
        if self.zombie:
            return
        self._dirty = False

        self._apply_modifiers()
        
        self._render(flush, erase, _surf)
        
        self._oldcoords = self._coords
        self._oldsurf = self.surf

    # Movement

    @_ensure_placed
    def set_dirty(self):
        if self._virtual:
            return
        if self._dirty:
            return
        self._dirty = True
        for sprite in self.get_movement_collisions():
            if not sprite.zombie:
                sprite.set_dirty()

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

    def bound_on_screen(self):
        if self.x < 0:
            self.set_x(0)
        if self.y < 0:
            self.set_y(0)
        if self.x + self.width > terminal.width():
            self.set_x(terminal.width() - self.width)
        if self.y + self.height > terminal.height():
            self.set_y(terminal.height() - self.height)

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
    
    def virtual(self):
        """Usage:
        
        >>> with sprite.virtual():
        >>>     # sprite is virtual in this scope
        
        When a sprite is virtual:
        - it does not trigger re-rendering of other sprites
        """
        return _Virtual(self)
    
    # Collisions
    
    @_ensure_placed
    def get_movement_collisions(self) -> Generator[Sprite, None, None]:
        """Get collisions of BOTH old and new coords"""
        for sprite in self._scene.sprites:
            if sprite is not self and sprite._is_colliding_sprite(self) or sprite._is_colliding_sprite(self, old=True):
                yield sprite
    
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        """Usage: Collidable._is_colliding_base(Sprite)"""
        return (not self.hidden) \
            and (self.x - other_surf.width < other_coords.x < self.x + self.width) \
            and (self.y - other_surf.height < other_coords.y < self.y + self.height) \

    @_ensure_placed
    def was_colliding(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
        if self.hidden:
            return False
        for sp in _iter_sprites(sprite_or_sprites):
            if sp._is_colliding_sprite(self, old=True):
                return True
        return False

    @_ensure_placed
    def is_colliding(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
        if self.hidden:
            return False
        for sp in _iter_sprites(sprite_or_sprites):
            if sp._is_colliding_sprite(self):
                return True
        return False
    
    @_ensure_placed
    def get_colliding(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
        if self.hidden:
            return False
        for sp in _iter_sprites(sprite_or_sprites):
            if sp._is_colliding_sprite(self):
                yield sp

    # Styling, more methods are to be added

    def align_right(self):
        self.align_horizontal = RIGHT
        return self

class _Virtual:
    def __init__(self, owner: Sprite):
        self.owner = owner
    
    def __enter__(self):
        self.owner._virtual = True
        return self
    
    def __exit__(self, typ, val, tb):
        self.owner._virtual = False

def Object(surf: SurfaceLike):
    """Short singular sprite creator
    
    usage:
    >>> myarrow = ptg.Object(ptg.Surface("--->"))
    >>> myarrow = ptg.Object("--->")
    """
    sprite = Sprite()
    sprite.surf = Surface.coerce(surf)
    return sprite

class KinematicSprite(Sprite):
    """KinematicSprites handle also velocity, unlocking more complex interactions
    
    When to use KinematicSprite:
    - collisions
    - bouncing
    - acceleration of sprites
    """
    def __init__(self):
        super().__init__()

        # TODO: use vectors
        self.vx = 0
        self.vy = 0
        
    def move(self, dx=None, dy=None):
        super().move(self.vx if dx is None else dx, self.vy if dy is None else dy)
    
    def bounce(self, sprite_or_sprites: Sprite | Group | Iterable[Sprite | Group]) -> list[Sprite]:
        """Bouncing is complex and the sprite needs to simulate sub-tick movement
        """
        # how many intervals to divide the motion to?
        # such that for each interval the maximum delta in each axis is 1
        intervals = max(abs(self.vx), abs(self.vy))
        ix = Fraction(self.vx) / intervals
        iy = Fraction(self.vy) / intervals

        collided = set()

        with self.virtual():
            for _ in range(intervals):

                # upward collision
                self.move(0, -1)
                collisions = set(self.get_colliding(sprite_or_sprites))
                collided.update(collisions)
                if collisions:
                    self.vy = -self.vy
                    iy = -iy
                self.move(0, 1)

                # downward collision
                self.move(0, 1)
                collisions = set(self.get_colliding(sprite_or_sprites))
                collided.update(collisions)
                if collisions:
                    self.vy = -self.vy
                    iy = -iy
                self.move(0, -1)

                # leftward collision
                self.move(-1, 0)
                collisions = set(self.get_colliding(sprite_or_sprites))
                collided.update(collisions)
                if collisions:
                    self.vx = -self.vx
                    ix = -ix
                self.move(1, 0)

                # rightward collision
                self.move(1, 0)
                collisions = set(self.get_colliding(sprite_or_sprites))
                collided.update(collisions)
                if collisions:
                    self.vx = -self.vx
                    ix = -ix
                self.move(-1, 0)
                
                self.move(ix, iy)
        
        self.set_dirty()

        return collided
