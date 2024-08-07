# Development use

ENSURE_SPRITE_DESTRUCTION = True
ENSURE_VALID_TERMCOORDS = True

# Modify some code to monitor performance

from functools import wraps

if ENSURE_SPRITE_DESTRUCTION:
    import gc
    from .sprite import Sprite

    Sprite._real_kill = Sprite._kill
    @wraps(Sprite._kill)
    def _kill(self: Sprite):
        self._real_kill()
        assert len(self._groups) == 0, f"attempted to kill sprite but sprite is still in groups: {self._groups}"
        refs = gc.get_referrers(self)
        assert len(refs) == 0, f"attempted to kill sprite but sprite is still referenced by: {refs}"

if ENSURE_VALID_TERMCOORDS:
    from . import terminal
    terminal._real_goto = terminal.goto

    @wraps(terminal.goto)
    def goto(x, y):
        assert 1 <= x <= terminal.width(), f"terminal.goto() received invalid x-coordinate: {x}"
        assert 1 <= y <= terminal.height(), f"terminal.goto() received invalid y-coordinate: {y}"
