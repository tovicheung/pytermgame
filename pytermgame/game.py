"""ptg.game

This module contains the Game class, which controls the entire game.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias
import time
import sys

from . import terminal, event, transition as _transition
from .debugger import Debugger
from .event import add_event, EventLike
from .scene import Scene

if TYPE_CHECKING:
    from .coords import Coords
    from .transition import Transition

if sys.platform != "win32":
    import termios
    import fcntl
    import os

Interval: TypeAlias = tuple[EventLike, int]
Timer: TypeAlias = tuple[EventLike, int]

class Game:
    """The class that ties everything together.
    
    What a Game does:
    - set up terminal for a game
    - attached by an active scene
    - attached by intervals and timers
    - blocks (ticks) to maintain fps via Game.tick()
    
    What a Game can do for you:
    - calls .update() on the active scene via Game.update()
    - renders the terminal via Game.render() which just calls Scene.rerender()
    """

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
        - show_cursor - whether to show the cursor (shorthand to game.cursor.show())
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
        self.spf = None if self.fps is None else 1 / self.fps

        self.timers: list[Timer] = []
        self.intervals: list[Interval] = []

        self.debugger: Debugger | None = None
        self._block_next_tick = False
        self._block_key: str | None = None
        self._last_tick_time: float | None = None
        self._last_tick_dur: float | None = None

        # Game loop controls
        self._break_loop = False

        # A game must have a scene at all times
        self.scene = Scene()

        self.last_tick = 0
        self.ntick = 0
    
    # Start and end

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, typ, val, tb):
        self.cleanup()
        if typ in self.silent_errors:
            return True

    def start(self):
        # determine the control codes to send

        if sys.platform != "win32":
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
        terminal.disable_alternate_buffer()
        terminal.show_cursor()

        if sys.platform != "win32":
            termios.tcsetattr(self._nix_fd, termios.TCSAFLUSH, self._nix_old_term)
            fcntl.fcntl(self._nix_fd, fcntl.F_SETFL, self._nix_old_flags)
        
        type(self)._active = None

    def wrapper(self, f):
        self.start()
        try:
            f()
        except self.silent_errors:
            pass
        finally:
            self.cleanup()
    
    def get_debugger(self):
        self.debugger = Debugger().place((0, 0))
        return self.debugger
    
    # Active
    
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
    
    # Scene

    def new_scene(self):
        self.set_scene(Scene())
    
    def set_scene(self, scene: Scene):
        self.scene.render(flush=False, erase=True)
        self.scene = scene
        self.scene.render()
    
    # Clock

    def add_timer(self, event: EventLike, ticks: int):
        self.timers.append((event, self.ntick + ticks))
    
    def clear_timers(self):
        self.timers.clear()

    def add_interval(self, event: EventLike, ticks: int):
        self.intervals.append((event, ticks))
    
    def clear_intervals(self):
        self.intervals.clear()

    # Methods to be called each game loop

    def tick(self, timeless=False):
        """Blocks the game until one tick has passed.
        Does not wait if timeless is true
        
        Things that happen regardless of timeless:
        - checks if debugger needs to interrupt
        - process intervals (tick-based recurring events)
        - increase tick count
        """

        # TODO: integrate with last_tick below
        now = time.time()
        if self._last_tick_time is not None:
            self._last_tick_dur = now - self._last_tick_time
        self._last_tick_time = now

        if self._block_next_tick:
            self._block_next_tick = False
            self.debugger.block() # type: ignore
            self._last_tick_time = time.time()

        
        if self.debugger is not None and self._block_key is not None and not event.got:
            for key in event.get_keys():
                if key == self._block_key:
                    self.debugger.block() # type: ignore
                    self._last_tick_time = time.time()
                else:
                    event.queue.append((event.KEYEVENT, key))

        for interval in self.intervals:
            if self.ntick % interval[1] == 0:
                add_event(interval[0])

        for timer in self.timers:
            if self.ntick == timer[1]:
                add_event(timer[0])

        if self.fps is None or self.spf is None:
            # self.spf is None  is here only for type checkers
            return

        if not timeless:
            next_tick = self.last_tick + self.spf
            now = time.time()
            if now < next_tick:
                time.sleep(next_tick - now)
        self.last_tick = time.time()
        self.ntick += 1
        
        event.got = False # new tick, reset

    def update(self):
        """Not strictly required to call each game loop.
        This method is only a shorthand for calling .update() on all sprites in the active scene.
        If your sprites do not use .update(), there is no need to call this method.
        See Sprite.update() for more details.
        """
        self.scene.update()

    def render(self):
        self.scene.rerender()

    def _switch_scene(self, scene: Scene, transition: Transition, ticks: int):
        # Unused
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
    
    # Game loop controls

    def loop(self):
        if self._break_loop:
            self._break_loop = False
            return False
        return True

    def break_loop(self):
        self._break_loop = True

# Initialize ptg._active

from . import _active
_active.Game = Game
_active.initialized = True
