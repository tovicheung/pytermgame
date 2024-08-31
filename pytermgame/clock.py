from __future__ import annotations

from math import floor
import time
from typing import TypeAlias

from .event import Event, EventLike
from .game import Game

class Timer:
    _next_id = 0
    _pool: set[Timer] = set()

    @classmethod
    def get_running(cls):
        return tuple(cls._pool)
    
    def __init__(self, event: Event, secs: float, loops: int = 0):
        self.id = None
        self.event = event
        self.secs = secs
        self.loops = loops
        self.running = False
    
    def start(self):
        self.id = Timer._next_id
        Timer._next_id += 1

        Timer._pool.add(self)
        self.running = True
        self.last_emit_time = time.time()

        return self.id
    
    def stop(self):
        self.id = None
        
        Timer._pool.remove(self)
        self.running = False

    def emit_events(self) -> tuple[Event, ...]:
        if not self.running:
            raise Exception("i am not running")
        now = time.time()

        n = floor((now - self.last_emit_time) / self.secs)
        if n < 1:
            return ()
        
        self.last_emit_time = self.last_emit_time + self.secs * n
        if self.loops > 0:
            if self.loops < n:
                n = self.loops
            self.loops -= n
            if self.loops <= 0:
                self.stop()
                
        return (self.event,) * n

def add_timer(event: EventLike, secs: float, loop: int = 0) -> int:
    return Timer(Event(event), secs, loop).start()

def remove_timer(id: int):
    for timer in Timer.get_running():
        if timer.id == id:
            timer.stop()
            return

# Convenient aliases
wait = sleep = time.sleep
get_time = gettime = time.time
