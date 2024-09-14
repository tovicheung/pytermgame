from __future__ import annotations
from types import TracebackType

from . import cursor, terminal
from .coords import Coords, XY

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .sprite import Sprite

def _traverse_sprite(sprite: Sprite, dirty_set: set):
    dirty_set.add(sprite)
    for sp in sprite.get_required_renders():
        if sp not in dirty_set:
            _traverse_sprite(sp, dirty_set)

class Scene:
    """A scene is essentially a list of sprites ordered by z-coordinate."""

    # IMPORTANT: +Z is top, -Z is bottom

    _active_context: Scene | None = None

    def __init__(self):
        self.sprites: list[Sprite] = []
        self.offset = Coords.ORIGIN
    
    def _reassign_z(self, start: int, stop: int):
        for i, sprite in enumerate(self.sprites[start:stop]):
            sprite._z = start + i
    
    # Sprite interaction

    def add(self, sprite: Sprite):
        """Adds sprite to scene and assigns a z-index"""
        sprite._z = len(self.sprites)
        self.sprites.append(sprite)
    
    def remove(self, sprite: Sprite):
        self.sprites.remove(sprite)
        self._reassign_z(sprite._z, len(self.sprites))
    
    def update(self):
        """Call .update() on every sprite in the scene"""
        for sprite in self.sprites:
            sprite.update()
    
    # Render and re-render

    def render(self, flush: bool = True, erase: bool = False):
        for sprite in self.sprites:
            sprite.render(flush=False, erase=erase)

        if flush:
            terminal.flush()
    
    def get_rerender_queue(self) -> list[Sprite]:
        dirty: set[Sprite] = set()

        for sprite in filter(lambda sp: sp._rendered.dirty, self.sprites):
            _traverse_sprite(sprite, dirty)
        
        return sorted(dirty, key=lambda sp: sp._z)
    
    def rerender(self):
        """Erases and re-renders dirty sprites.
        Not to be confused with Scene.render() that calls .render() on all sprites.
        """
        rerender_queue = self.get_rerender_queue()

        if len(rerender_queue) == 0: # prevents rapid cursor blinks
            if cursor.state.dirty:
                cursor.write_ansi()
                terminal.flush()
            return
        
        if cursor.is_visible():
            terminal.hide_cursor(flush=True)
        for dirty_sprite in rerender_queue:
            dirty_sprite.render(flush=False, erase=True)
            if dirty_sprite.zombie:
                dirty_sprite._kill()
        for dirty_sprite in rerender_queue:
            if not dirty_sprite.zombie:
                dirty_sprite.render(flush=False, erase=False)
        
        if cursor.is_visible():
            cursor.write_ansi()
        
        # flush once after all the rendering
        terminal.flush()
    
    # Context manager for easy sprite placement

    def __enter__(self):
        if Scene._active_context is not None:
            raise Exception("Cannot enter more than one scene")
        Scene._active_context = self
        return self
    
    def __exit__(self, typ: type[BaseException], val: Any, tb: TracebackType):
        Scene._active_context = None
    
    # Scrolling

    def apply_scroll(self, coords: Coords):
        return coords.d(-self.offset)
    
    def scroll(self, dx: int = 0, dy: int = 0):
        self.offset = self.offset.d((dx, dy))
        if dx != 0 or dy != 0:
            for sprite in self.sprites:
                # no need to propagate since we are setting for all sprites
                sprite.set_dirty()
    
    def set_scroll(self, offset: XY):
        self.offset = Coords.coerce(offset)
        for sprite in self.sprites:
            sprite.set_dirty()
    
    # Sprite ordering (unstable)

    def move_sprite_to_below(self, sprite_to_move: Sprite, reference_sprite: Sprite):
        if sprite_to_move not in self.sprites:
            raise ValueError("sprite to move is not in sprites")
        if reference_sprite not in self.sprites:
            raise ValueError("reference sprite is not in sprites")
        if sprite_to_move is reference_sprite:
            raise ValueError("sprite to move and reference sprite cannot be the same")
        
        old_index = self.sprites.index(sprite_to_move)
        new_index = self.sprites.index(reference_sprite)
        
        self.sprites.insert(new_index, self.sprites.pop(old_index))

        self._reassign_z(min(old_index, new_index), max(old_index, new_index) + 1)
