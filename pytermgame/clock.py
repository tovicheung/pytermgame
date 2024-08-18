import time
from typing import TypeAlias

from .event import EventLike
from .game import Game

# Thread-based intervals do not make sense in a tick-based game
# 
# import threading
# 
# class Repeat(threading.Timer):
#     def run(self):
#         while not self.finished.wait(self.interval):
#             self.function(*self.args, **self.kwargs)
# 
# def set_timer(event: EventLike, secs: float, as_interval = False):
#     """Triggers an event every n seconds.
#     Timers run on separate seconds."""
#     if as_interval:
#         active = Game.get_active()
#         if active.fps is None:
#             raise Exception("Cannot set timers using intervals when fps=None (ie as fast as possible)")
#         set_interval(event, round(secs * active.fps))
#     else:
#         def _func():
#             add_event(event)
#         Game.get_active().add_timer(Repeat(interval=secs, function=_func))

def add_interval(event: EventLike, ticks: int | None = None, secs: float | None = None):
    """Triggers an event every n ticks.
    Intervals are managed and triggered by the game."""
    if ticks is None:
        if secs is None:
            raise ValueError("Either ticks or secs must be a value")
        fps = Game.get_active().fps
        if fps is None:
            raise ValueError("Cannot set secs-based interval on game with fps=None")
        ticks = round(fps * secs)
    Game.get_active().add_interval(event, ticks)

def add_timer(event: EventLike, ticks: int | None = None, secs: float | None = None):
    if ticks is None:
        if secs is None:
            raise ValueError("Either ticks or secs must be a value")
        fps = Game.get_active().fps
        if fps is None:
            raise ValueError("Cannot set secs-based timer on game with fps=None")
        ticks = round(fps * secs)
    Game.get_active().add_timer(event, ticks)

# Convenient aliases
wait = sleep = time.sleep
get_time = gettime = time.time

# Type aliases
Interval: TypeAlias = tuple[EventLike, int, int]
Timer: TypeAlias = tuple[EventLike, int]
