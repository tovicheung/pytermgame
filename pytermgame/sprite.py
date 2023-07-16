from __future__ import annotations

from .surface import Surface
from . import terminal
from .game import Game
import gc

# from ._instructions import Instruction
# def asfunc(cls):
#     def _inner(*args, **kwargs):
#         return cls(*args, **kwargs)
#     return _inner

DEBUG = False

class Sprite:
    surf: Surface
    group: Group | None = None

    def __init__(self, active_render: bool = False):
        self._x = 0
        self._y = 0
        self._lx = 0
        self._ly = 0
        self._active_render = active_render
        self._groups: list[Group] = []
        Game.active.register(self)
        if self.group is not None:
            self.group.add(self)
        self.init()

    def init(self):
        """called after __init__"""

    def update(self):
        """generic method, can be customized to receive arguments"""

    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y
    
    @property
    def width(self):
        return self.surf.width
    
    @property
    def height(self):
        return self.surf.height

    def render(self, flush=True, erase=False):
        if erase:
            surf = self.surf.to_blank()
            tx, ty = terminal.transform_coords(self._lx, self._ly)
        else:
            surf = self.surf
            tx, ty = terminal.transform_coords(self.x, self.y)
        for i, line in enumerate(surf.lines()):
            terminal.goto(tx, ty + i)
            terminal.write(line)
        if flush:
            terminal.flush() # flush at once, not every line
        self._lx = self.x
        self._ly = self.y

    # @asfunc
    # class goto(Instruction):
    #     def __init__(self, sprite, x, y):
    #         self.sprite = sprite
    #         self.x = x
    #         self.y = y
    
    def goto(self, x, y):
        self._x = x
        self._y = y
        if self._active_render:
            self.render()

    def move(self, dx, dy):
        self._x += dx
        self._y += dy
        if self._active_render:
            self.render()

    def kill(self):
        self.render(flush=False, erase=True)
        # frees all references and destroyed by garbage collector
        # tested with gc.get_referrers()
        Game.active.sprites.remove(self)
        for group in self._groups:
            group.remove(self)
        
        
        if DEBUG:
            assert gc.get_referrers() == []

    def touching(self, other: Sprite):
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
