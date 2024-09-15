from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if sys.platform != "win32":
    import termios
    import fcntl
    import os

from . import terminal as term
from . import _active
from .sprite import Sprite
from .surface import Surface

if TYPE_CHECKING:
    from .game import Game

class Debugger(Sprite):
    # Debuggers are meant to be ugly

    surf = Surface("No debug info yet")

    def on_placed(self):
        self.data: dict[Any, Any] = {}
        self.active = True
    
    def hook(self, game: Game):
        game.debugger = self
        return self

    def field(self, key: Any, value: Any):
        self.data[key] = value
        self._rendered.dirty = True
        return self

    def render(self, flush: bool = True, erase: bool = False):
        if not self.active:
            return
        super().render(flush, True)
        self.surf = Surface("Debug: " + str(self.data))
        super().render(flush, erase)
    
    def block(self):
        while True:
            term.home()
            term.goto(0, term.height()-2)
            
            if sys.platform != "win32":
                fd, old_attrs, old_flags = term.config_normal()
            
            print("empty=leave | [t]ick | fps <N>")
            cmd = input(">").strip()
            
            if sys.platform != "win32":
                term.config(fd, old_attrs, old_flags)
            
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
                    _active.get_active().spf = None if fps is None else 1 / fps
                except Exception:
                    pass
            term.clear()
            _active.get_scene().render()
        term.clear()
        _active.get_scene().render()

        return self
    
    def block_on_key(self, key: str):
        raise Exception("handle the key event with debugger.block()")

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
        # add .disable() at the end of the chain to quickly hide debugger
        self.active = False
