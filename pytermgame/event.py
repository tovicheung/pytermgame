import threading

from .game import Game
from ._get_key import get_keys
class Event:
    __slots__ = ("type", "value")
    def __init__(self, type, value = None):
        self.type = type
        self.value = value

KEYEVENT = 2
USEREVENT = 31

queue = []

def get():
    for key in get_keys():
        yield Event(KEYEVENT, key)
    queued = queue.copy()
    queue.clear()
    for event in queued:
        yield event

class Repeat(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def set_timer(event: int, millis: int):
    def _func():
        queue.append(Event(event))
    Game.active.add_timer(Repeat(interval=millis / 1000, function=_func))

def delay(event: int, millis: int):
    def _func():
        queue.append(Event(event))
    Game.active.add_timer(threading.Timer(millis / 1000, _func))
