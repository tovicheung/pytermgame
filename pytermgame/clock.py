import time
import threading
from .game import Game
from .event import Event, add_event

class Repeat(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def set_timer(event: int, millis: int):
    def _func():
        add_event(Event(event))
    Game.active.add_timer(Repeat(interval=millis / 1000, function=_func))

def set_interval(event: int, ticks: int):
    Game.active.add_interval(event, ticks)

def delay(event: int, millis: int):
    def _func():
        add_event(Event(event))
    Game.active.add_timer(threading.Timer(millis / 1000, _func))

wait = sleep = time.sleep
