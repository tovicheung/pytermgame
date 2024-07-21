from __future__ import annotations

from typing import TYPE_CHECKING

from . import terminal as term
from . import _active
from .sprite import Sprite
from .surface import Surface

if TYPE_CHECKING:
    from .game import Game

class _dummy:
    def __getattribute__(self, name):
        return self
    
    def __call__(self, *args, **kwargs):
        # dummy method calls
        return self

class Debugger(Sprite):
    # Debuggers are meant to be ugly

    surf = Surface("No debug info yet")

    def on_placed(self):
        self.data = {}
        self.active = True
    
    def hook(self, game: Game):
        game.debugger = self
        return self

    def field(self, key, value):
        self.data[key] = value
        self._rendered.dirty = True
        return self

    def render(self, flush=True, erase=False):
        super().render(flush, True)
        self.surf = Surface("Debug: " + str(self.data))
        super().render(flush, erase)
    
    def block(self):
        while True:
            term.home()
            term.goto(0, term.height()-2)
            print("empty=leave | [t]ick | fps <N>")
            cmd = input(">").strip()
            if len(cmd) == 0:
                break
            elif cmd.startswith("t"):
                _active.get_active()._block_next_tick = True
                break
            elif cmd.startswith("fps"):
                try:
                    value = cmd[3:].strip()
                    fps = None if value == "None" else int(value)
                    _active.get_active().fps = fps
                    _active.get_active().spf = None if value == "None" else 1 / fps
                except Exception:
                    pass
            term.clear()
            _active.get_scene().render()
        term.clear()
        _active.get_scene().render()

        return self
    
    def block_on_key(self, key: str):

        # Technique 1: wrap get() to detect special key

        from . import event
        def get():
            for ev in event._get():
                if ev == (event.KEYEVENT, key):
                    _active.get_active()._block_next_tick = True
                yield ev
        event.get = get

        # Technique 2: tell game about special key
        # game will go through key events itself if get() is not called at a tick

        _active.get_active()._block_key = key
        return self
    
    def disable(self):
        """
        Add .disable() at the end of your debugger configuration to disable it easily, without needing to comment out all code
        """
        from . import event
        self.active = False
        self.hide()
        event.get = event._get
        _active.get_active()._block_key = None
        _active.get_active().debugger = None
        return _dummy()
