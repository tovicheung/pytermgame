# Development use
# Add `from pytermgame import _dev` to activate

CHECK_PLATFORM_KEYS_ENTRIES = True
ENSURE_SPRITE_DESTRUCTION = True
ENSURE_VALID_TERMCOORDS = True

# Modify some code to monitor performance

from functools import wraps

if CHECK_PLATFORM_KEYS_ENTRIES:
    from . import _key_win, _key_posix
    if _key_win.__dict__.keys() != _key_posix.__dict__.keys():
        win = set(filter(lambda s: s[0] != "_", _key_win.__dict__.keys()))
        posix = set(filter(lambda s: s[0] != "_", _key_posix.__dict__.keys()))
        diffwin = win.difference(posix)
        diffposix = posix.difference(win)
        raise AssertionError(f"_key_win and _key_posix have different entries\nwin - posix: {diffwin}\nposix - win: {diffposix}")

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
    
    Sprite._kill = _kill

if ENSURE_VALID_TERMCOORDS:
    from . import terminal

    terminal._real_goto = terminal.goto

    @wraps(terminal.goto)
    def goto(x, y):
        assert 1 <= x <= terminal.width(), f"terminal.goto() received invalid x-coordinate: {x}"
        assert 1 <= y <= terminal.height(), f"terminal.goto() received invalid y-coordinate: {y}"
        terminal._real_goto(x, y)
    
    terminal.goto = goto
