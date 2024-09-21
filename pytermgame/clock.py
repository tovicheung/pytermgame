from __future__ import annotations

from math import floor
import time
from typing import Any, Callable, TypeAlias

from .event import Event, EventLike


Callback: TypeAlias = Callable[[], Any]


class Timer:
    """A timer emits events periodically based on actual time instead of game ticks.
    
    Implementation detail:
    A timer does not use threads. Instead, events are lazily generated from Timer.emit_events()
    (called by ptg.event.get()) based on the current time and the last called time.
    """

    _next_id = 0
    _pool: set[Timer] = set()

    @classmethod
    def get_running(cls):
        return tuple(cls._pool)
    
    def __init__(self, event: Event, secs: float, loops: int = 0):
        """Initializes a timer, does not start it.
        loops > 0  =>  [loops] events are emitted at max
        loops = 0  =>  events are emitted indefinitely
        """
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
            if self.loops <= n:
                n = self.loops
                self.stop()
            self.loops -= n
                
        return (self.event,) * n


class CallbackTimer(Timer):
    def __init__(self, event: Callback, secs: float, loops: int = 0):
        self.id = None
        self.event = event
        self.secs = secs
        self.loops = loops
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
            if self.loops <= n:
                n = self.loops
                self.stop()
            self.loops -= n
        
        for _ in range(n):
            self.event()
        
        return ()


def add_timer(event: EventLike, secs: float, loops: int = 0) -> int:
    """Starts a timer with the given arguments.
    * event - the event to emit
    * secs - duration between events
    * loops - maximal number of events to emit, infinite if 0
    """
    return Timer(Event(event), secs, loops).start()


def add_callback_timer(callback: Callback, secs: float, loops: int = 0) -> int:
    """Same as add_timer() but with auto callback.
    Note: timer id can still be used in remove_timer()
    """
    return CallbackTimer(callback, secs, loops).start()


def remove_timer(id: int):
    for timer in Timer.get_running():
        if timer.id == id:
            timer.stop()
            return


# Convenient aliases
wait = sleep = time.sleep
get_time = gettime = time.time
