import time
import threading
from .game import Game
from .event import EventLike, add_event

class Repeat(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def set_timer(event: EventLike, secs: float):
    def _func():
        add_event(event)
    Game.active.add_timer(Repeat(interval=secs, function=_func))

def set_interval(event: EventLike, ticks: int):
    Game.active.add_interval(event, ticks)

def delay(event: EventLike, secs: float):
    def _func():
        add_event(event)
    Game.active.add_timer(threading.Timer(secs, _func))

# Convenient aliases
wait = sleep = time.sleep
gettime = time.time
