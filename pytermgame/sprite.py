from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache, wraps
from math import floor
from typing import Iterable, Generator, TypeAlias, overload
import sys

if sys.version_info >= (3, 11):
    from typing import Self

from . import terminal, _active
from .collidable import Collidable
from .coords import Coords, XY
from .group import Group
from .style import Style, Dir, Color, _resolve_style
from .scene import Scene
from .surface import PhantomSurface, Surface, SurfaceLike

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

NestedCollidables: TypeAlias = "Collidable | Iterable[Collidable | NestedCollidables]"

def __iter_collidables(nested_collidables: NestedCollidables) -> Generator[Collidable]:
    if isinstance(nested_collidables, Collidable):
        yield nested_collidables
        return
    if isinstance(nested_collidables, Iterable):
        for x in nested_collidables:
            yield from _iter_collidables(x)
        return
    raise TypeError(f"Argument must be collidable or nested iterables of collidables, got {nested_collidables}")

# very temporary optimization
@lru_cache
def _iter_collidables(nested_collidables: NestedCollidables) -> list[Collidable]:
    return list(__iter_collidables(nested_collidables))

@dataclass
class RenderedState:
    """Sprite's state when it was last rendered on screen
    
    self.dirty == True:
    - sprite needs to be re-rendered (erase and paint)
    - in most cases: self.coords != sprite.coords or self.surf != sprite.surf
        (unless sprite.set_dirty() called manually)
    
    self.dirty == False:
    - sprite does not need to be re-rendered

    self.on_screen == False:
    - sprite was not on screen, no need to erase
    """
    dirty: bool
    on_screen: bool
    coords: Coords
    screen_coords: Coords # for erasing
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

    style: Style

    # If set to a Group(), automatically add instances to the group
    group: Group

    def __init__(self) -> None:
        # sprite is now in abstract state

        # initialized in .place()
        self._scene: Scene
        self._coords: Coords
        self._rendered: RenderedState

        self._groups: list[Group] = []
        
        # styling
        self.style = Style() # all unspecified
        self._resolved_style: Style | None = None # none means requires resolving

        if hasattr(type(self), "style"):
            self.style.merge(type(self).style)

        # user-accessible attributes
        self.placed = False
        self.hidden = False
        self.zombie = False

        self._virtual = False

        # a sprite's parent updates its surface if the sprite's surface changes
        self._parent: Sprite | None = None

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
    
    # Styling

    @overload
    def apply_style(self, style: Style) -> Self: ...
    @overload
    def apply_style(self, *, 
        align_horizontal: Dir | None = None,
        align_vertical: Dir | None = None,
        fg: Color | None = None,
        bg: Color | None = None,
        bold: bool | None = None,
        inverted: bool | None = None) -> Self: ...
    
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
        changed = self.style.merge(style)
        if changed:
            self._resolved_style = None
            self.set_dirty()
        return self
    
    # State conversion methods

    def place(self, coords: XY = Coords.ORIGIN, scene: Scene | None = None) -> Self:
        """After a sprite is being placed, it:
        - is attached to a scene
        - has XYZ coordinates on the scene
        - has a surface
        - calls .on_placed(), which can be overriden by subclasses freely
        - unlocks methods such as .move()
        - can be killed via .kill()
        """

        if self.placed:
            raise Exception("Invalid call, sprite is already placed.")

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
        
        # Resolve surface: set self.surf
        
        if (not hasattr(type(self), "surf")) and (not hasattr(self, "surf")):
            self.update_surf()
        else:
            self.surf = Surface.coerce(self.surf)

        # add to class group if one exists
        if hasattr(type(self), "group") and isinstance(type(self).group, Group):
            self.group.add(self)

        self.on_placed()

        self._rendered = RenderedState(dirty=True, on_screen=False, coords=self._coords, screen_coords=self._coords, surf=self.surf)
        self.placed = True

        return self

    def kill(self) -> None:
        """Set the sprite as a zombie and erases it from the scene.
    
        Zombies are truly killed in Group.update() via Sprite._kill() (see below)
        Therefore, it is recommended to use Sprite.kill() in Sprite.update()
        """
        if self.zombie:
            return
        self.render(flush=False, erase=True)
        self.zombie = True

    def _kill(self) -> None:
        """Truly kills a sprite, should only call as zombie."""

        # frees all references and destroyed by garbage collector
        while len(self._groups):
            self._groups[0].remove(self)

    # Methods subclasses can override

    def on_placed(self) -> None:
        """called AUTOMATICALLY after place()
        Initial coordinates and styles can be customized.
        Position methods such as .goto() and .move() can be used.
        """

    def update(self) -> None:
        """called MANUALLY, often from group.update() or game.update()
        Users are free to customize the behaviour of .update() in their sprites.
        """

    # Properties of a sprite

    @property
    def x(self) -> int:
        return floor(self._coords.x)
    
    @property
    def y(self) -> int:
        return floor(self._coords.y)
    
    @property
    def z(self) -> int:
        return self._z
    
    @property
    def width(self) -> int:
        return self.surf.width
    
    @property
    def height(self) -> int:
        return self.surf.height
    
    # Rendering

    def render(self, flush: bool = True, erase: bool = False) -> None:
        """Render sprite onto terminal
        - flush: whether to flush stdout after rendering
        - erase:
            - True -> use whitespaces to overwrite the old surface on the terminal
            - False -> render current surface
        """
        if self.zombie:
            return
        
        if self.hidden and not erase:
            return
        
        if erase and not self._rendered.on_screen:
            return
        
        if erase and self._rendered.on_screen:
            self._rendered.on_screen = False
        
        if (not erase) and not self._rendered.on_screen:
            self._rendered.on_screen = True
        
        # self._render(flush, erase)

        if erase:
            coords = self._rendered.screen_coords
            surf = self._rendered.surf.to_blank()
        else:
            coords = self._scene.apply_scroll(self._coords)
            surf = self.surf

        ansi = "\033[m"
        if not erase:
            if self._resolved_style is None:
                self._resolved_style = _resolve_style(self)
            ansi += self._resolved_style.to_ansi()
        
        surf.render(coords, ansi, flush=flush)
        
        self._rendered.coords = self._coords
        self._rendered.screen_coords = self._scene.apply_scroll(self._coords)
        self._rendered.surf = self.surf
        self._rendered.dirty = False

    # Movement

    def set_dirty(self) -> None:
        if self._virtual or (not self.placed) or self._rendered.dirty:
            return
        self._rendered.dirty = True
        # if not propagate:
        #     return
        # for sprite in self.get_movement_collisions():
        #     if not sprite.zombie:
        #         # if we re-render a sprite, we must also re-render other sprites touching it to avoid overlapping
        #         sprite.set_dirty()

    def goto(self, x: int | float | Fraction, y: int | float | Fraction) -> None:
        self._coords = Coords(x, y)
        self.set_dirty()

    def bound(self, x_min: int | None = None, x_max: int | None = None, y_min: int | None = None, y_max: int | None = None) -> None:
        if x_min is not None and self.x < x_min:
            self.set_x(x_min)
        if x_max is not None and self.x > x_max:
            self.set_x(x_max)
        if y_min is not None and self.y < y_min:
            self.set_y(y_min)
        if y_max is not None and self.y > y_max:
            self.set_y(y_max)

    def bound_on_screen(self) -> None:
        if self.x < 0:
            self.set_x(0)
        if self.y < 0:
            self.set_y(0)
        if self.x + self.width > terminal.width():
            self.set_x(terminal.width() - self.width)
        if self.y + self.height > terminal.height():
            self.set_y(terminal.height() - self.height)

    def move(self, dx: int | float | Fraction, dy: int | float | Fraction) -> None:
        self._coords = self._coords + Coords(dx, dy)
        self.set_dirty()

    def set_x(self, x: int | float | Fraction) -> None:
        self._coords = self._coords.with_x(x)
        self.set_dirty()

    def set_y(self, y: int | float | Fraction) -> None:
        self._coords = self._coords.with_y(y)
        self.set_dirty()
    
    def set_surf(self, surf: Surface) -> None:
        if self.placed:
            old_surf = self.surf
        self.surf = surf
        if self.placed:
            if self.style.align_horizontal == Dir.right and self.surf.width != old_surf.width:
                self._coords = self._coords.dx(-(self.surf.width - old_surf.width))
            if self.style.align_vertical == Dir.bottom and self.surf.height != old_surf.height:
                self._coords = self._coords.dy(-(self.surf.height - old_surf.height))
        self.set_dirty()
        if self._parent is not None and self._parent.placed:
            self._parent.update_surf()
    
    def update_surf(self) -> None:
        self.set_surf(self.new_surf_factory())

    def hide(self) -> None:
        if self.hidden:
            return
        self.hidden = True
        self.set_dirty()

    def show(self) -> None:
        if not self.hidden:
            return
        self.hidden = False
        self.set_dirty()
    
    def virtual(self) -> _Virtual:
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
    def get_movement_collisions(self) -> Generator[Sprite]:
        """Get collision of both old and new states"""
        # TODO: better name and documentation
        for sprite in self._scene.sprites:
            if sprite is not self and (sprite._is_colliding_sprite(self) or sprite._is_colliding_sprite(self, old=True)):
                yield sprite
    
    def _is_colliding_raw(self, other_coords: Coords, other_surf: Surface) -> bool:
        return (self.x - other_surf.width < other_coords.x < self.x + self.width) \
            and (self.y - other_surf.height < other_coords.y < self.y + self.height) \
    
    def _is_colliding_sprite(self, other: Sprite, old: bool = False) -> bool:
        if self is other:
            return False
        if self.hidden:
            return False
        return super()._is_colliding_sprite(other, old)

    @_ensure_placed
    def was_colliding(self, collidable: Collidable) -> bool:
        if not self._rendered.on_screen:
            return False
        return collidable._is_colliding_sprite(self, old=True)

    @_ensure_placed
    def was_colliding_any(self, sprite_or_sprites: NestedCollidables) -> bool:
        """Check if sprite's rendered state is colliding with any of the collidables.

        Takes in collidables nested in any way.
        
        Examples:
        ```python
        sprite.was_colliding_any(myball)
        sprite.was_colliding_any((myball, myball2))
        sprite.was_colliding_any((myball3, (myball, myball2)))
        ```
        """
        if not self._rendered.on_screen:
            return False
        for sp in _iter_collidables(sprite_or_sprites):
            if sp._is_colliding_sprite(self, old=True):
                return True
        return False

    @_ensure_placed
    def is_colliding(self, sprite: Collidable) -> bool:
        if self.hidden:
            return False
        return sprite._is_colliding_sprite(self)

    @_ensure_placed
    def is_colliding_any(self, nested_collidables: NestedCollidables) -> bool:
        """Check if sprite is colliding with any of the collidables.
        
        Takes in collidables nested in any way.
        
        Examples:
        ```python
        sprite.is_colliding_any(myball)
        sprite.is_colliding_any((myball, myball2))
        sprite.is_colliding_any((myball3, (myball, myball2)))
        ```
        """
        if self.hidden:
            return False
        for sp in _iter_collidables(nested_collidables):
            if sp._is_colliding_sprite(self):
                return True
        return False
    
    @_ensure_placed
    def get_collisions_with(self, nested_collidables: NestedCollidables) -> Generator[Collidable]:
        """Returns the subset of collidables that sprite is colliding with
        
        Takes in collidables nested in any way.
        
        Examples:
        ```python
        sprite.get_collisions_with(myball)
        sprite.get_collisions_with((myball, myball2))
        sprite.get_collisions_with((myball3, (myball, myball2)))
        ```
        """
        if self.hidden:
            return
        for sp in _iter_collidables(nested_collidables):
            if sp._is_colliding_sprite(self):
                yield sp

class _Virtual:
    def __init__(self, owner: Sprite):
        self.owner = owner
    
    def __enter__(self):
        self.owner._virtual = True
        return self
    
    def __exit__(self, typ, val, tb):
        self.owner._virtual = False

def Object(surf: SurfaceLike) -> Sprite:
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
        
    def move(self, dx: int | float | Fraction | None = None, dy: int | float | Fraction | None = None) -> None:
        super().move(self.vx if dx is None else dx, self.vy if dy is None else dy)
    
    def move_until_collision(self, sprite_or_sprites: NestedCollidables) -> set[Collidable]:
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

    def bounce(self, nested_collidables: NestedCollidables) -> set[Collidable]:
        """self.move() but sprite bounces
        The final position and velocity are calculated by simulating sub-tick movements via .virtual().
        Returns sprites that have been collided with.

        Note: bouncing on other KinematicSprites are a little unreliable.
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

                states: set[tuple[Fraction, Fraction]] = set()

                tmp_mask_x = 0
                tmp_mask_y = 0

                # We fiddle with the velocities until nothing blocks us
                # yes it is fragile code but it works well
                while True:

                    states.add((ix, iy))

                    # upward collision
                    if iy < 0:
                        self.move(0, -1)
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
                        collisions = set(self.get_collisions_with(nested_collidables))
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
