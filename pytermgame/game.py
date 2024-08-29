"""ptg.game

This module contains the Game class, which controls the entire game.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Literal
import time
import sys

if TYPE_CHECKING:
    from .clock import Interval, Timer

from . import terminal, event, cursor
from .debugger import Debugger
from .event import add_event, EventLike
from .scene import Scene

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum
    class StrEnum(str, Enum): ...

if sys.platform != "win32":
    import termios
    import fcntl
    import os

class UpdateScreenSize(StrEnum):
    # always get the latest screen size
    always = "always"

    # update and cache screen size every tick
    every_tick = "every_tick"

    # assume the screen size is fixed
    none = "none"

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
            silent_errors: tuple[type[BaseException], ...] = (KeyboardInterrupt,),
            text_wrapping: bool = False,
            clear_first: bool = False,
            update_screen_size: UpdateScreenSize | Literal["always", "every_tick", "none"] = "every_tick",
            cache_nested_collidables: bool = False,
            time_source: Callable[[], int | float] = time.perf_counter,
            ):
        """Initialization options:
        - fps - frames per second, execute as fast as possible if set to None
        - alternate_screen - whether to use an alternate terminal screen
        - show_cursor - whether to show the cursor (shorthand to cursor.show())
        - silent_errors - what errors should not be displayed
        - text_wrapping - whether to wrap overflow in terminal
        - clear_first - whether to clear the terminal before starting
        - update_screen_size - when to get the latest screen size via os.get_terminal_size()
        - cache_nested_collidables - whether to @lru_cache collidable.flatten_collidables
            : results in huge performance boost in collision-heavy games, but killed sprites may not be immediately collected by gc
        - time_source: function to get time eg time.perf_counter or time.time
        """

        # Initialization options
        self.fps = fps
        self.alternate_screen = alternate_screen
        self.show_cursor = show_cursor
        self.silent_errors = silent_errors
        self.text_wrapping = text_wrapping
        self.clear_first = clear_first
        self.update_screen_size = UpdateScreenSize(update_screen_size)
        self.cache_nested_collidables = cache_nested_collidables
        self.time_source = time_source

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

        self._tick_start = 0
        self.ntick = 0
    
    # Start and end

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, typ: type[BaseException], val: Any, tb: TracebackType):
        self.cleanup()
        if typ in self.silent_errors:
            return True

    def start(self):
        if self.update_screen_size == UpdateScreenSize.none:
            terminal.set_size_cache()

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
        elif self.clear_first:
            terminal.clear()

        if self.show_cursor:
            cursor.show()
        else:
            cursor.hide()
            cursor.write_ansi()

        if self.text_wrapping:
            terminal.enable_autowrap()
        else:
            terminal.disable_autowrap()
        
        if self.cache_nested_collidables:
            from . import collidable
            collidable.flatten_collidables = collidable._flatten_collidables_cached

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
        
        if self.update_screen_size == UpdateScreenSize.none:
            terminal.disable_size_cache()
        
        if self.cache_nested_collidables:
            from . import collidable
            collidable.flatten_collidables = collidable._real_flatten_collidables

    def run(self, f: Callable[[Game], None]):
        """Intended use:
        ```python
        @Game(...).run
        def my_super_fun_game(game: Game):
            ...
        ```
        """
        self.start()
        try:
            f(self)
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
        self.intervals.append((event, ticks, self.ntick % ticks))
    
    def clear_intervals(self):
        self.intervals.clear()

    # Methods to be called each game loop

    def tick(self, timeless: bool = False):
        """Blocks the game until one tick has passed.
        Does not wait if timeless is true
        
        Things that happen regardless of timeless:
        - checks if debugger needs to interrupt
        - process intervals (tick-based recurring events)
        - increase tick count
        """

        get_time = self.time_source
        _tick_ignore_duration = 0

        if self._block_next_tick:
            self._block_next_tick = False
            start = get_time()
            self.debugger.block() # type: ignore
            _tick_ignore_duration = get_time() - start
        
        if self.debugger is not None and self._block_key is not None and not event._got:
            for key in event.get_keys():
                if key == self._block_key:
                    start = get_time()
                    self.debugger.block() # type: ignore
                    _tick_ignore_duration = get_time() - start
                else:
                    event.queue.append((event.KEYEVENT, key))

        for interval in self.intervals:
            if (self.ntick - interval[2]) % interval[1] == 0:
                add_event(interval[0])

        for timer in self.timers:
            if self.ntick == timer[1]:
                add_event(timer[0])

        if self.update_screen_size == UpdateScreenSize.every_tick:
            terminal.set_size_cache()
        
        event._got = False

        if (not timeless) and self.fps is not None and self.spf is not None:
            end_of_tick = self._tick_start + self.spf
            now = get_time()
            if now < end_of_tick:
                time.sleep(end_of_tick - now)
        
        now = get_time()

        # duration of last tick
        self._last_tick_dur = now - self._tick_start - _tick_ignore_duration

        self._tick_start = now
        self.ntick += 1

    def update(self):
        """Not strictly required to call each game loop.
        This method is only a shorthand for calling .update() on all sprites in the active scene.
        If your sprites do not use .update(), there is no need to call this method.
        See Sprite.update() for more details.
        """
        self.scene.update()

    def render(self):
        self.scene.rerender()
    
    # Game loop controls

    def loop(self):
        if self._break_loop:
            self._break_loop = False
            return False
        return True

    def break_loop(self):
        self._break_loop = True
    
    def event_loop(self, update: bool = True, render: bool = True):
        """Gets event and loop until .break_loop() is called.
        update / render: whether to call .update() / .render() each loop
        """
        while self.loop():
            if update:
                self.update()
            if render:
                self.render()
            yield event.wait_for_event()

# Initialize ptg._active

from . import _active
_active.Game = Game
_active.initialized = True
