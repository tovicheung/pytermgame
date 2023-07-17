from __future__ import annotations
from typing import TYPE_CHECKING
import time

from . import terminal
if TYPE_CHECKING:
    from .sprite import Sprite
    from .event import Repeat

if not terminal.WINDOWS:
    import sys
    import termios
    import fcntl
    import os

class Game:
    # holds reference to currently active game
    active: Game | None = None

    def __init__(self,
                fps: int | None = 20,
                alternate_screen: bool = True,
                show_cursor: bool = False,
                silent_errors: tuple[BaseException] = (KeyboardInterrupt,)
                ):
        self.fps = fps
        self.alternate_screen = alternate_screen
        self.show_cursor = show_cursor
        self.silent_errors = silent_errors

        self.sprites: list[Sprite] = []
        self.timers: list[Repeat] = []

        self.last_tick = 0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, typ, val, tb):
        self.cleanup()
        if typ in self.silent_errors:
            return True

    def add_timer(self, timer: Repeat):
        # assumed to be called after game start
        self.timers.append(timer)
        timer.start()

    def start(self): # determine the control codes to send
        if not terminal.WINDOWS:
            # set terminal attributes to raw mode
            self._nix_fd = fd = sys.stdin.fileno()
            self._nix_old_term = termios.tcgetattr(fd)
            new_term = termios.tcgetattr(fd)
            new_term[3] = new_term[3] & ~(termios.ICANON | termios.ECHO)
            termios.tcsetattr(fd, termios.TCSANOW, new_term)
            self._nix_old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, self._nix_old_flags | os.O_NONBLOCK)
        if self.alternate_screen:
            terminal.enable_alternate_buffer()
        if self.show_cursor:
            terminal.show_cursor()
        else:
            terminal.hide_cursor()
        for timer in self.timers:
            timer.start()
        type(self).active = self

    def cleanup(self):
        for timer in self.timers: # must be done first (error may occur below and stop the cleanup process, leaving unkilled threads)
            timer.cancel()
        terminal.disable_alternate_buffer()
        terminal.show_cursor()
        if not terminal.WINDOWS:
            termios.tcsetattr(self._nix_fd, termios.TCSAFLUSH, self._nix_old_term)
            fcntl.fcntl(self._nix_fd, fcntl.F_SETFL, self._nix_old_flags)
        type(self).active = None

    def wrapper(self, f):
        self.start()
        try:
            f()
        except BaseException as e:
            # `except self.silent_errors: ...` does not work well with linters like pylance (although it works)
            if type(e) not in self.silent_errors:
                raise
        finally:
            self.cleanup()

    def register(self, *sprites: Sprite):
        self.sprites.extend(sprites)

    def tick(self):
        if self.fps is None:
            return

        next_tick = self.last_tick + 1 / self.fps
        while time.time() < next_tick:
            ...
        self.last_tick = time.time()

    def update(self):
        for sprite in self.sprites:
            sprite.render(flush=False, erase=True)
            sprite.render(flush=False)
        terminal.flush()
