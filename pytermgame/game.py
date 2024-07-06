"""ptg.game

This module contains the Game class, which controls the entire game.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import time
import sys

from . import terminal
from .event import add_event, EventLike
from .scene import Scene
from . import transition as _transition

if TYPE_CHECKING:
    from threading import Timer
    from .transition import Transition

if not terminal.WINDOWS:
    import termios
    import fcntl
    import os

Interval = tuple[EventLike, int]

class Game:
    """Represents a game"""

    # reference to currently active game
    _active: Game | None = None

    def __init__(self,
            fps: int | None = 30,
            alternate_screen: bool = True,
            show_cursor: bool = False,
            silent_errors: tuple[type[BaseException]] = (KeyboardInterrupt,),
            text_wrapping: bool = False,
            clear_first: bool = False,
            ):
        """Initialization options:
        - fps - frames per second, execute as fast as possible if set to None
        - alternate_screen - whether to use an alternate terminal screen
        - show_cursor - whether to show the cursor
        - silent_errors - what errors should not be displayed
        - text_wrapping - whether to wrap overflow in terminal
        - clear_first - whether to clear the terminal before starting
        """

        # Initialization options
        self.fps = fps
        self.alternate_screen = alternate_screen
        self.show_cursor = show_cursor
        self.silent_errors = silent_errors
        self.text_wrapping = text_wrapping
        self.clear_first = clear_first

        # Don't compute every tick
        self.spf = 1 / self.fps

        self.timers: list[Timer] = []
        self.intervals: list[Interval] = []

        # A game must have a scene at all times
        self.scene = Scene()

        self.last_tick = 0
        self.ntick = 0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, typ, val, tb):
        self.cleanup()
        if typ in self.silent_errors:
            return True
    
    def is_active(self):
        return self is type(self)._active 
        
    @classmethod
    def get_active(cls):
        """Get the currently active game"""
        if cls._active is None:
            raise RuntimeError("Invalid call, no active game")
        return cls._active
    
    @classmethod
    def get_scene(cls):
        """Get the scene of the currently active game"""
        return cls.get_active().scene
    
    @classmethod
    def get_sprites(cls):
        """Get the sprites of the scene of the currently active game"""
        return cls.get_scene().sprites
    
    def set_scene(self, scene: Scene):
        self.scene.render(flush=False, erase=True)
        self.scene = scene
        self.scene.render()

    def add_timer(self, timer: Timer):
        self.timers.append(timer)
        if self.is_active():
            timer.start()

    def add_interval(self, event: EventLike, ticks: int):
        self.intervals.append((event, ticks))

    def start(self):
        # determine the control codes to send

        # if not terminal.WINDOWS:
        if sys.platform != "win32": # align with stubs and reduce errors
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
        
        if self.clear_first:
            terminal.clear()

        for timer in self.timers:
            timer.start()

        type(self)._active = self
        self.ntick = -1
        self.tick(timeless=True)

    def cleanup(self):
        for timer in self.timers: # must be done first (error may occur below and stop the cleanup process, leaving unkilled threads)
            timer.cancel()
        terminal.disable_alternate_buffer()
        terminal.show_cursor()
        # if not terminal.WINDOWS:
        if sys.platform != "win32": # align with stubs and reduce errors
            termios.tcsetattr(self._nix_fd, termios.TCSAFLUSH, self._nix_old_term)
            fcntl.fcntl(self._nix_fd, fcntl.F_SETFL, self._nix_old_flags)
        type(self)._active = None

    def wrapper(self, f):
        self.start()
        try:
            f()
        except self.silent_errors as e:
            pass
        finally:
            self.cleanup()

    # Methods to be called each game loop

    def tick(self, timeless=False):
        # blocking unless force is set

        if self.fps is None:
            return

        if not timeless:
            next_tick = self.last_tick + self.spf
            while time.time() < next_tick:
                pass
        self.last_tick = time.time()
        self.ntick += 1

        for interval in self.intervals:
            if self.ntick % interval[1] == 0:
                add_event(interval[0])

    def update(self):
        self.scene.update()

    def render(self):
        self.scene.rerender()

    def switch_scene(self, scene: Scene, transition: Transition, ticks: int):
        switched = False
        for flags in transition(ticks):
            if flags & _transition.F_SWITCH:
                self.scene = scene
                switched = True
            if flags & _transition.F_CLEAR:
                terminal.clear()
            if flags & _transition.F_RENDER:
                self.scene.render(flush=True)
            self.tick()
            if flags & _transition.F_RENDER_AFTER_TICK:
                self.scene.render(flush=True)
        
        if not switched:
            self.scene = scene

        terminal.clear()
        terminal.reset()
        scene.render()

# Initialize ptg._active

from . import _active
_active.Game = Game
_active.initialized = True
