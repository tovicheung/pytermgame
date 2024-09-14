from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from fractions import Fraction
from functools import wraps
from math import floor
from typing import Any, Generator, overload
import sys

if sys.version_info >= (3, 11):
    from typing import Self

from . import terminal, _active
from .collidable import Collidable, flatten_collidables, NestedCollidables
from .coords import Coords, XY
from .group import Group
from .style import Style, Dir, Color, _resolve_style
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
        if self.zombie and False:
            raise RuntimeError(f"Sprite.{f.__name__}() should not be called when the sprite is zombie and waiting to be garbage collected ({self._debug()})")
        return f(self, *args, **kwargs)
    return _new

@dataclass
class RenderedState:
    """Sprite's state when it was last rendered on screen"""

    # should sprite be re-rendered?
    dirty: bool

    # was sprite rendered on screen?
    on_screen: bool
    
    coords: Coords
    screen_coords: Coords # for erasing
    surf: Surface

    # for erasing
    collisions: set[Sprite]

class Sprite(Collidable):
    """
    For special objects without a surface (eg screen edges) see `ptg.collidable`

    Functional states of a sprite:
    * abstract: sprite is not attached to a scene
    * placed: sprite is attached to a scene with coordinates and a surface
    * zombie: sprite is no longer on screen, but object still exists in memory

    The respective methods are `.__init__()`, `.place()`, and `.kill()`.

    Game states of a sprite:
    * hidden: sprite is not visible, no collisions
        - methods: `.hide()` and `.show()`
    * virtual: collisions do not affect other sprites
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

    # Define costumes for a sprite
    costumes: dict[Any, tuple[Surface | None, Style | None]]

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
        self._parent: Parent | None = None

    def _debug(self) -> str:
        # returns a debug info string
        debug = f"{type(self).__name__}"
        if self.placed:
            debug += f"({self._coords})"
        if self.zombie:
            debug = "zombie " + debug
        return debug
    
    __repr__ = _debug
    
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
            self.unset_resolved_style()
        return self
    
    # State conversion methods

    def place(self, coords: XY = Coords.ORIGIN, scene: Scene | None = None) -> Self:
        """After a sprite is being placed, it:
        * is attached to a scene
        * has XYZ coordinates on the scene
        * has a surface
        * calls .on_placed(), which can be overriden by subclasses freely
        * unlocks methods such as .move()
        * can be killed via .kill()
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
        self._z: int = -1 # will be assigned in scene.add(), here for typing purposes
        scene.add(self)

        # Resolve coords: set self._coords
    
        self._coords = Coords.coerce(coords)
        
        # Resolve surface: set self.surf
        
        if (not hasattr(type(self), "surf")) and (not hasattr(self, "surf")):
            self.update_surf()
        else:
            self.surf = Surface.coerce(self.surf)

        # add to class group if one exists
        if hasattr(type(self), "group") and isinstance(type(self).group, Group):
            self.group.add(self)

        self.on_placed()

        self._rendered = RenderedState(dirty=True, on_screen=False, coords=self._coords, screen_coords=self._coords, surf=self.surf, collisions=set())
        self.placed = True

        return self

    def kill(self) -> None:
        """Set the sprite as a zombie, hide it, and removes it from all groups."""
        if self.zombie:
            return
        
        self.hide()
        self.zombie = True

        while len(self._groups) > 1:
            group = self._groups[0]
            group.remove(self)

    def _kill(self) -> None:
        """Frees as much references as possible.
        This should only be called by Scene after ensuring it is erased.
        """

        self._scene.remove(self)
        
        if self._parent is not None:
            self._parent.remove_child(self)
        
        # Potential remaining referrers:
        # * user variables  --  nothing we can do
        # * RenderedState.collisions -- will eventually be taken care of by gc

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
        if self.hidden and not erase:
            return
        
        if erase and not self._rendered.on_screen:
            return
        
        if erase and self._rendered.on_screen:
            self._rendered.on_screen = False
        
        if (not erase) and not self._rendered.on_screen:
            self._rendered.on_screen = True

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

        if not erase:
            self._rendered.coords = self._coords
            self._rendered.screen_coords = self._scene.apply_scroll(self._coords)
            self._rendered.surf = self.surf
            self._rendered.dirty = False
            try:
                self._rendered.collisions = self._collisions
            except AttributeError:
                ...

    def set_dirty(self) -> None:
        if self._virtual or (not self.placed) or self._rendered.dirty:
            return
        self._rendered.dirty = True
    
    def unset_resolved_style(self) -> None:
        self._resolved_style = None
        self.set_dirty()

    # Movement

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

    @_ensure_placed
    def hide(self) -> None:
        if self.hidden:
            return
        self.hidden = True
        self.set_dirty()

    @_ensure_placed
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
    def get_required_renders(self) -> Generator[Sprite]:
        """Returns sprites to re-render if self needs to be re-rendered."""
        self._collisions = set()
        for sprite in self._scene.sprites:
            if sprite is not self and (sprite._is_colliding_sprite(self)):
                self._collisions.add(sprite)
                yield sprite
        yield from self._rendered.collisions
    
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
        for sp in flatten_collidables(sprite_or_sprites):
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
        for sp in flatten_collidables(nested_collidables):
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
        for sp in flatten_collidables(nested_collidables):
            if sp._is_colliding_sprite(self):
                yield sp
    
    # Costumes

    def has_costume(self, identifier):
        return hasattr(self, "costumes") and identifier in self.costumes
    
    def set_costume(self, identifier):
        if not self.has_costume(identifier):
            raise KeyError(f"Costume identifier {identifier!r} not found")
        costume = self.costumes[identifier]
        surf, style = costume
        if surf is not None:
            self.set_surf(surf)
        if style is not None:
            self.apply_style(style)

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

class Parent(Sprite, ABC):
    """Parents can be set as Sprite._parent and must implement these methods.
    Parents can use any way to store children, as long as their presence can be checked and they can be removed.
    """
    @abstractmethod
    def remove_child(self, child: Sprite) -> None:
        pass

    @abstractmethod
    def has_child(self, child: Sprite) -> bool:
        pass

    def unset_resolved_style(self) -> None:
        super().unset_resolved_style()
        self.unset_children_resolved_style()
    
    @abstractmethod
    def unset_children_resolved_style(self) -> None:
        pass

class KinematicSprite(Sprite):
    """A KinematicSprite has velocity, unlocking more complex interactions
    
    When to use KinematicSprite:
    * collisions
    * bouncing
    * acceleration of sprites
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
