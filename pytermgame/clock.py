import time
import threading

from .event import EventLike, add_event
from .game import Game

# Thread-based intervals do not make sense in a tick-oriented game
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

def set_interval(event: EventLike, ticks: int | None = None, secs: float | None = None):
    """Triggers an event every n ticks.
    Intervals are managed and triggered by the game."""
    if ticks is None:
        if secs is None:
            raise ValueError("Either ticks or secs must be a value")
        if Game.get_active().fps is None:
            raise ValueError("Cannot set secs-based interval on game with fps=None")
        ticks = Game.get_active().fps * secs
    Game.get_active().add_interval(event, ticks)

def delay(event: EventLike, secs: float):
    def _func():
        add_event(event)
    Game.get_active().add_timer(threading.Timer(secs, _func))

# Convenient aliases
wait = sleep = time.sleep
get_time = gettime = time.time
