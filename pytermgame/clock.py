import time
import threading
from .game import Game
from .event import EventLike, add_event

class Repeat(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def set_timer(event: EventLike, secs: float):
    # Timer runs on separate threads
    def _func():
        add_event(event)
    Game.get_active().add_timer(Repeat(interval=secs, function=_func))

def set_interval(event: int, ticks: int):
    # Intervals runs on the same thread and is managed by Game
    Game.get_active().add_interval(event, ticks)

def delay(event: EventLike, secs: float):
    def _func():
        add_event(event)
    Game.get_active().add_timer(threading.Timer(secs, _func))

# Convenient aliases
wait = sleep = time.sleep
get_time = gettime = time.time
