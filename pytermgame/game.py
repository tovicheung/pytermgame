from __future__ import annotations
from typing import TYPE_CHECKING
import time

from . import terminal
from .event import add_event
if TYPE_CHECKING:
    from .sprite import Sprite
    from .clock import Repeat

if not terminal.WINDOWS:
    import sys
    import termios
    import fcntl
    import os

Interval = tuple[int, int]

class Game:
    # holds reference to currently active game
    active: Game | None = None

    def __init__(self,
                fps: int | None = 20,
                alternate_screen: bool = True,
                show_cursor: bool = False,
                silent_errors: tuple[BaseException] = (KeyboardInterrupt,),
                text_wrapping: bool = False,
                ):
        self.fps = fps
        self.alternate_screen = alternate_screen
        self.show_cursor = show_cursor
        self.silent_errors = silent_errors
        self.text_wrapping = text_wrapping

        self.sprites: list[Sprite] = []
        self.timers: list[Repeat] = []
        self.intervals: list[Interval] = []

        self.last_tick = 0
        self.ntick = 0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, typ, val, tb):
        self.cleanup()
        if typ in self.silent_errors:
            return True
        
    @property
    def nextz(self):
        return len(self.sprites)

    def add_timer(self, timer: Repeat):
        # assumed to be called after game start
        self.timers.append(timer)
        timer.start()

    def add_interval(self, event: int, ticks: int):
        self.intervals.append((event, ticks))

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
        if self.text_wrapping:
            terminal.enable_autowrap()
        else:
            terminal.disable_autowrap()

        for timer in self.timers:
            timer.start()

        type(self).active = self
        self.ntick = -1
        self.tick(force=True)

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

    def tick(self, force=False):
        if self.fps is None:
            return

        if not force:
            next_tick = self.last_tick + 1 / self.fps
            while time.time() < next_tick:
                ...
        self.last_tick = time.time()
        self.ntick += 1

        for interval in self.intervals:
            if self.ntick % interval[1] == 0:
                add_event(interval[0])

    def update(self):
        for sprite in self.sprites:
            sprite.update()

    def render(self):
        queue = sorted(filter(lambda sprite: sprite._dirty, self.sprites), key=lambda sprite: sprite.z)
        for sprite in queue:
            sprite.render(flush=False, erase=True)
        for sprite in queue:
            sprite.render(flush=False)
        terminal.flush()
