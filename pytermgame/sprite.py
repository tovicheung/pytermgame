from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import wraps
from math import floor
from typing import Iterable, Generator, overload
import sys

if sys.version_info >= (3, 11):
    from typing import Self

from . import terminal, _active
from .collidable import Collidable
from .coords import Coords, XY
from .group import Group
from .style import Style, Dir, Color
from .scene import Scene
from .surface import Surface, SurfaceLike

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
            raise RuntimeError(f"Sprite.{f.__name__}() should be called after placing it by calling Sprite.place() ({self._debug()})")
        if self.zombie:
            raise RuntimeError(f"Sprite.{f.__name__}() should not be called when the sprite is zombie and waiting to be garbage collected ({self._debug()})")
        return f(self, *args, **kwargs)
    return _new

def _iter_sprites(sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
    if isinstance(sprite_or_sprites, Collidable):
        yield sprite_or_sprites
        return
    for x in sprite_or_sprites:
        yield from _iter_sprites(x)

@dataclass
class RenderedState:
    """Sprite's coords and surface when it was last rendered on screen
    
    self.dirty == True:
    - sprite needs to be re-rendered (erase and paint)
    - does NOT guarantee self.coords != sprite.coords or self.surf != sprite.surf
        (since re-render can also be triggered by collisions)
    
    self.dirty == False:
    - sprite does not need to be re-rendered

    self.on_screen == False:
    - sprite was not on screen, no need to erase
    """
    dirty: bool
    on_screen: bool
    coords: Coords # note: screen coords not scene coords
    surf: Surface

class Sprite(Collidable):
    """
    For special objects without a surface (eg screen edges) see `ptg.collidable`

    Functional states of a sprite:
    - abstract: sprite is not attached to a scene
    - placed: sprite is attached to a scene with coordinates and a surface
    - zombie: sprite is no longer on screen, but object still exists in memory

    The respective methods are `.__init__()`, `.place()`, and `.kill()`.

    Game states of a sprite:
    - hidden: sprite is not visible, no collisions
        - methods: `.hide()` and `.show()`
    - virtual: collisions do not affect other sprites
        - use case: test for collisions without triggering them
        - note: a sprite should not be kept virtual across ticks
        - method: `.virtual()`
    """

    # There are 3 methods for a subclass to define surfaces
    # Method 1: using the .surf class attribute
    surf: Surface
    # Method 2: set in .__init__()
    # Method 3: see .new_surf_factory()

    # If set to a Group(), automatically add instances to the group
    group: Group | None = None

    def __init__(self):
        # sprite is now in abstract state

        # initialized in .place()
        self._scene: Scene
        self._coords: Coords
        self._rendered: RenderedState

        self._groups: list[Group] = []
        
        # styling
        self.style = Style.default()

        # user-accessible attributes
        self.placed = False
        self.hidden = False
        self.zombie = False

        self._virtual = False
        
        # [future: collision]
        # self._collisions: set[Sprite] = set()

    def _debug(self) -> str:
        # returns a debug info string
        debug = f"{type(self).__name__} sprite"
        if self.placed:
            debug += f" placed at {self._coords}"
        if self.zombie:
            debug += " which is a zombie"
        return debug
    
    def new_surf_factory(self) -> Surface:
        """A factory to dynamically generate a sprite's surface.
        Subclasses that use .update_surf() should implement this.

        Example:
        ```python
        class Line(ptg.Sprite):
            def __init__(self, length): ...
        
            def new_surf_factory(self):
                return Surface("-" * self.length)
        
            def double_my_length(self):
                self.length *= 2
                self.update_surf()
                # .update_surf() will automatically call .new_surf_factory() to get the newest surf and set it
        ```
        """
        raise NotImplementedError("Sprite.update_surf() should only be called if Sprite.new_surf_factory() is defined.")
    
    # State conversion methods

    def place(self, coords: XY = Coords.ORIGIN, scene: Scene | None = None):
        """After a sprite is being placed, it:
        - has a surface
        - is attached to a scene
        - has XYZ coordinates on the scene
        - calls .on_placed(), which can be overriden by subclasses freely
        - unlocks methods such as .move()
        - can be killed via .kill()
        """

        if self.placed:
            raise Exception("Invalid call, sprite is already placed.")
        
        # Resolve surface: set self.surf
        
        if (not hasattr(type(self), "surf")) and (not hasattr(self, "surf")):
            try:
                self.update_surf()
            except NotImplementedError:
                raise NotImplementedError("Subclass of Sprite must define either .surf or .new_surf_factory()") from None

        # Attach to scene: set self._scene

        if scene is None:
            if Scene._active_context is not None:
                scene = Scene._active_context
            else:
                scene = _active.get_scene()
        self._scene = scene
        scene.add(self)

        # Resolve coords: set self._coords, self._z
    
        self._coords = Coords.coerce(coords)
        self._z = scene._next_z()

        # add to class group if one exists
        if isinstance(self.group, Group):
            self.group.add(self)

        self.on_placed()

        self._rendered = RenderedState(True, False, self._coords, self.surf)
        self.placed = True

        return self

    def kill(self):
        """Set the sprite as a zombie and erases it from the scene.
    
        Zombies are truly killed in Group.update() via Sprite._kill() (see below)
        Therefore, it is recommended to use Sprite.kill() in Sprite.update()
        """
        if self.zombie:
            return
        self.render(flush=False, erase=True)
        self.zombie = True

    def _kill(self):
        """Truly kills a sprite, should only call as zombie."""

        # frees all references and destroyed by garbage collector
        while len(self._groups):
            self._groups[0].remove(self)

    # Methods subclasses can override

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
    
    @overload
    def apply_style(self, style: Style) -> Self: ...
    @overload
    def apply_style(self, *, 
        align_horizontal: Dir = None,
        align_vertical: Dir = None,
        fg: Color = None,
        bg: Color = None,
        bold: bool = None,
        inverted: bool = None) -> Self: ...
    
    def apply_style(self, style: Style | None = None, **style_options) -> Self:
        """Apply style to sprite. 2 ways to use:
        
        Method 1: use a `Style` object
        (your type checker probably likes this more)
        >>> sprite.apply_style(Style(fg = Color.red, bg = Color.green))

        Method 2: provide arguments directly
        >>> sprite.apply_style(fg = Color.red, bg = Color.green)
        """
        if style is None:
            style = Style(**style_options)
        changed = self.style.update(style)
        if changed:
            self.set_dirty()
        return self
    
    # Rendering

    def _apply_style(self):
        """Modifies coords and surfs right before rendering"""
        if self.style.align_horizontal == Dir.right and self.surf.width != self._rendered.surf.width:
            self._coords = self._coords.dx(-(self.surf.width - self._rendered.surf.width))
        if self.style.align_vertical == Dir.bottom and self.surf.height != self._rendered.surf.height:
            self._coords = self._coords.dy(-(self.surf.height - self._rendered.surf.height))
    
    def _render(self, flush=True, erase=False):
        if erase:
            coords = self._rendered.coords
            surf = self._rendered.surf.to_blank()

            # # [future: collision]
            # self._scene.mat.remove(self)
        else:
            coords = self._scene.apply_scroll(self._coords)
            surf = self.surf

            # [future: collision]
            # self._collisions = self._scene.mat.add(self)

        if coords.x + surf.width < 0 or \
            coords.y + surf.height < 0 or \
            coords.x >= terminal.width() or \
            coords.y >= terminal.height():
            return # out of screen, do nothing!

        if coords.x < 0:
            # partially out of left bound
            slice_x = slice(int(abs(coords.x)), None, None)
        elif coords.x + surf.width > terminal.width():
            # partially out of right bound
            # terminal.width() - int(coords.x) = how many chars to show
            slice_x = slice(None, terminal.width() - int(coords.x), None)
        else:
            slice_x = slice(None, None, None)
        
        ansi = "\033[m" + self.style.to_ansi()

        for i, line in enumerate(surf.lines()):
            segment = line[slice_x]
            if len(segment) == 0:
                continue
            line_coords = coords.dy(i)
            if line_coords.y < 0 or line_coords.y >= terminal.height():
                continue # line is vertically out of screen
            terminal.goto(*line_coords.to_term())
            terminal.write(ansi + segment)

        terminal.write("\033[m")

        if flush:
            terminal.flush() # flush at once, not every line

    def render(self, flush=True, erase=False):
        """Render sprite onto terminal
        - flush: whether to flush stdout after rendering
        - erase:
            - True -> use whitespaces to overwrite the old surface on the terminal
            - False -> render current surface
        """
        if self.zombie:
            return
        
        if self.hidden:
            erase = True
        
        if erase and not self._rendered.on_screen:
            return
        
        if erase and self._rendered.on_screen:
            self._rendered.on_screen = False
        
        if (not erase) and not self._rendered.on_screen:
            self._rendered.on_screen = True


        self._apply_style()
        
        self._render(flush, erase)
        
        self._rendered.coords = self._scene.apply_scroll(self._coords)
        self._rendered.surf = self.surf
        self._rendered.dirty = False

    # Movement

    def set_dirty(self, propagate=True):
        if self._virtual or (not self.placed) or self._rendered.dirty:
            return
        self._rendered.dirty = True
        for sprite in self.get_movement_collisions():
            if not sprite.zombie:
                # if we re-render a sprite, we must also re-render other sprites touching it to avoid overlapping
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
        self._coords = self._coords.with_x(x)
        self.set_dirty()

    def set_y(self, y):
        self._coords = self._coords.with_y(y)
        self.set_dirty()
    
    def set_surf(self, surf: Surface):
        self.surf = surf
        self.set_dirty()
    
    def update_surf(self):
        self.set_surf(self.new_surf_factory())

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
        - ie, set_dirty is temporarily disabled
        """
        return _Virtual(self)
    
    # Collisions
    # disambiguation: collision = overlap
    
    @_ensure_placed
    def get_movement_collisions(self) -> Generator[Sprite, None, None]:
        """Get collision of both old and new states"""
        # TODO: better name and documentation
        for sprite in self._scene.sprites:
            if sprite is not self and (sprite._is_colliding_sprite(self) or sprite._is_colliding_sprite(self, old=True)):
                yield sprite
    
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface):
        return (self.x - other_surf.width < other_coords.x < self.x + self.width) \
            and (self.y - other_surf.height < other_coords.y < self.y + self.height) \
    
    def _is_colliding_sprite(self, other: Sprite, old=False):
        if self is other:
            return False
        return super()._is_colliding_sprite(other, old)

    @_ensure_placed
    def was_colliding(self, sprite: Collidable):
        if not self._rendered.on_screen:
            return False
        return sprite._is_colliding_sprite(self, old=True)

    @_ensure_placed
    def was_colliding_any(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
        if not self._rendered.on_screen:
            return False
        for sp in _iter_sprites(sprite_or_sprites):
            if sp._is_colliding_sprite(self, old=True):
                return True
        return False

    @_ensure_placed
    def is_colliding(self, sprite: Collidable):
        if self.hidden:
            return False
        return sprite._is_colliding_sprite(self)

    @_ensure_placed
    def is_colliding_any(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
        if self.hidden:
            return False
        for sp in _iter_sprites(sprite_or_sprites):
            if sp._is_colliding_sprite(self):
                return True
        return False
    
    @_ensure_placed
    def get_collisions_with(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
        if self.hidden:
            return
        for sp in _iter_sprites(sprite_or_sprites):
            if sp._is_colliding_sprite(self):
                yield sp
    
    # # [future: collision]
    if False:

        @_ensure_placed
        def get_collisions(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
            if self.hidden:
                return
            for sp in _iter_sprites(sprite_or_sprites):
                if sp in self._collisions:
                    yield sp
                elif isinstance(sp, Collidable) and sp._is_colliding_sprite(self):
                    yield sp
        
        get_collisions_with = get_collisions

        @_ensure_placed
        def get_old_collisions(self):
            yield from self._scene.mat.get_collisions(self._rendered.coords, self._rendered.surf)
        
        @_ensure_placed
        def get_all_collisions(self):
            yield from self._collisions
        
        @_ensure_placed
        def get_movement_collisions(self):
            yield from self._collisions
            if self._was_on_screen:
                for sp in self.get_old_collisions():
                    if sp not in self._collisions:
                        yield sp
        
        @_ensure_placed
        def is_colliding_any(self, sprite_or_sprites: Collidable | Group | Iterable[Collidable | Group]):
            for sp in _iter_sprites(sprite_or_sprites):
                if sp in self._collisions:
                    return True
            return False

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
    """A KinematicSprite has velocity, unlocking more complex interactions
    
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
    
    def move_until_collision(self, sprite_or_sprites: Sprite | Group | Iterable[Sprite | Group]) -> set[Collidable]:
        """self.move() but stops on collision
        Returns the list of sprites it collided with.
        """
        intervals = max(abs(self.vx), abs(self.vy))
        ix = Fraction(self.vx) / intervals
        iy = Fraction(self.vy) / intervals
        # fractions are used to prevent float errors

        with self.virtual():
            for _ in range(intervals):
                self.move(ix, iy)
                collisions = set(self.get_collisions_with(sprite_or_sprites))
                if collisions:
                    return collisions
            
        self.set_dirty()

        return set()

    def bounce(self, sprite_or_sprites: Sprite | Group | Iterable[Sprite | Group]) -> set[Collidable]:
        """self.move() but sprite bounces
        The final position and velocity are calculated by simulating sub-tick movements via .virtual().
        Returns sprites that have been collided with
        """
        # minimum intervals to divide the motion into
        # such that for each interval the maximum delta in each axis is 1
        intervals = max(abs(self.vx), abs(self.vy))

        # interval velocity
        ix = Fraction(self.vx) / intervals
        iy = Fraction(self.vy) / intervals
        # fractions are used to prevent float errors

        collided: set[Collidable] = set()

        with self.virtual():
            for _ in range(intervals):

                states = set()

                tmp_mask_x = 0
                tmp_mask_y = 0

                # We fiddle with the velocities until nothing blocks us
                # yes it is fragile code but it works well
                while True:

                    states.add((ix, iy))

                    # upward collision
                    if iy < 0:
                        self.move(0, -1)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(0, 1)
                        if collisions:
                            self.vy = -self.vy
                            iy = -iy
                            if (ix, iy) in states:
                                tmp_mask_y = -iy
                                break
                            continue

                    # downward collision
                    if iy > 0:
                        self.move(0, 1)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(0, -1)
                        if collisions:
                            self.vy = -self.vy
                            iy = -iy
                            if (ix, iy) in states:
                                tmp_mask_y = -iy
                                break
                            continue

                    # leftward collision
                    if ix < 0:
                        self.move(-1, 0)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(1, 0)
                        if collisions:
                            self.vx = -self.vx
                            ix = -ix
                            if (ix, iy) in states:
                                tmp_mask_x = -ix
                                break
                            continue

                    # rightward collision
                    if ix > 0:
                        self.move(1, 0)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(-1, 0)
                        if collisions:
                            self.vx = -self.vx
                            ix = -ix
                            if (ix, iy) in states:
                                tmp_mask_x = -ix
                                break
                            continue

                    # corners

                    # top-left collision
                    if ix < 0 and iy < 0:
                        self.move(-1, -1)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(1, 1)
                        if collisions:
                            self.vx = -self.vx
                            self.vy = -self.vy
                            ix = -ix
                            iy = -iy
                            if (ix, iy) in states:
                                tmp_mask_x = -ix
                                tmp_mask_y = -iy
                                break
                            continue

                    # top-right collision
                    if ix > 0 and iy < 0:
                        self.move(1, -1)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(-1, 1)
                        if collisions:
                            self.vx = -self.vx
                            self.vy = -self.vy
                            ix = -ix
                            iy = -iy
                            if (ix, iy) in states:
                                tmp_mask_x = -ix
                                tmp_mask_y = -iy
                                break
                            continue

                    # bottom-left collision
                    if ix < 0 and iy > 0:
                        self.move(-1, 1)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(1, -1)
                        if collisions:
                            self.vx = -self.vx
                            self.vy = -self.vy
                            ix = -ix
                            iy = -iy
                            if (ix, iy) in states:
                                tmp_mask_x = -ix
                                tmp_mask_y = -iy
                                break
                            continue

                    # bottom-right collision
                    if ix > 0 and iy > 0:
                        self.move(1, 1)
                        collisions = set(self.get_collisions_with(sprite_or_sprites))
                        collided.update(collisions)
                        self.move(-1, -1)
                        if collisions:
                            self.vx = -self.vx
                            self.vy = -self.vy
                            ix = -ix
                            iy = -iy
                            if (ix, iy) in states:
                                tmp_mask_x = -ix
                                tmp_mask_y = -iy
                                break
                            continue
                    
                    break

                self.move(ix + tmp_mask_x, iy + tmp_mask_y)
        
        self.set_dirty()

        return collided
