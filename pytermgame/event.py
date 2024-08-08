from __future__ import annotations

from typing import Any

from ._get_key import get_keys
from . import key as _key

class Event:
    __slots__ = ("type", "value")

    def __init__(self, type: int | tuple[int, int] | Event, value: Any = None):
        """
        Method 1:
        >>> myevent = Event(typ, val)
        
        Method 2:
        >>> myevent = Event((typ, val))
        """
        if isinstance(type, Event):
            self.type = type.type
            self.value = type.value
        elif isinstance(type, tuple):
            self.type, self.value = type
        else:
            self.type = type
            self.value = value

    # Convenient methods
    
    def is_key(self, key: str | None = None):
        """Checks if event is a key event
        ```
        event.is_key() # event.type == KEYEVENT
        event.is_key("a") # event.type == KEYEVENT and event.value == "a"
        event.is_key(ptg.key.UP) # event.type == KEYEVENT and event.value == up arrow
        event.is_key("up") # event.type == KEYEVENT and event.value == up arrow
        event.is_key("ctrl-a") # event.type == KEYEVENT and event.value == Ctrl A
        ```
        """
        if key is None:
            return self.type == KEYEVENT
        return self.type == KEYEVENT and (self.value == key or self.value == _key.__dict__.get(key.upper().replace("-", "_"), None))
    
    def is_type(self, type: int):
        return self.type == type

    def as_pair(self):
        return (self.type, self.value)

    def __eq__(self, other: EventLike):
        if isinstance(other, int):
            # used as event == TYPE
            return self.is_type(other)
        elif isinstance(other, type(self)):
            return other.type == self.type and other.value == self.value
        return self.as_pair() == other
    
    def value_passes(self, func):
        """equivalent to func(event.value) but silences errors
        
        Example:
        ```python
        event.value_passes(str.isdigit)
        ```
        """
        try:
            return func(self.value)
        except Exception:
            return False
        
    def is_user(self):
        return self.type >= USEREVENT

EventLike = int | tuple[int, Any] | Event
# 2 == Event(type=2, value=None)
# (2, False) == Event(type=2, value=False)

EXIT = 1 # unused for now
KEYEVENT = 2
MOUSECLICK = MOUSELEFTCLICK = 3 # unused for now
MOUSERIGHTCLICK = 4 # unused for now
MOUSESCROLLUP = 5 # unused for now
MOUSESCROLLDOWN = 6 # unused for now
USEREVENT = 31

queue: list[EventLike] = []

def wait_for_event():
    """blocks until an event is triggered"""
    while True:
        queue.extend(Event(KEYEVENT, x) for x in get_keys())
        if len(queue):
            break
    return Event(queue.pop(0))
    

def get():
    """non-blocking, should be used in tick-based games"""
    global _got
    _got = True

    for key in get_keys():
        yield Event(KEYEVENT, key)
    
    # new events may be triggered when looping over get()
    queued = queue.copy()
    queue.clear()
    for event in queued:
        yield Event(event)

_got = False # has get() been called this tick?
_get = get

def add_event(event: EventLike):
    if not isinstance(event, Event):
        event = Event(event)
    queue.append(event)

def wait_until(event: EventLike):
    """blocks until an event that meets the criteria is triggered
    Note: any events that are triggered while waiting are discarded
    For a more safer method to wait for events use wait_for_event()"""
    while True:
        for e in get():
            if event == e:
                return e
