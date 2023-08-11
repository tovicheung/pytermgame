import time
import threading
from .game import Game
from .event import EventLike, add_event

class Repeat(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def set_timer(event: EventLike, millis: int):
    def _func():
        add_event(event)
    Game.active.add_timer(Repeat(interval=millis / 1000, function=_func))

def set_interval(event: EventLike, ticks: int):
    Game.active.add_interval(event, ticks)

def delay(event: EventLike, millis: int):
    def _func():
        add_event(event)
    Game.active.add_timer(threading.Timer(millis / 1000, _func))

# Convenient aliases
wait = sleep = time.sleep
gettime = time.time
