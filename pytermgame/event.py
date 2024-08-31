from __future__ import annotations

from typing import Any, Callable, Protocol

from ._get_key import get_keys
from . import key as _key

# TODO: use NamedTuple
class Event:
    __slots__ = ("type", "value")

    def __init__(self, type: int | tuple[int, int] | Event, value: Any = None):
        """Supports multiple representations:
        * no value: Event(typ)
        * type and value: Event(typ, val)
        * as a duplet: Event((typ, val))
        """
        if isinstance(type, Event):
            self.type = type.type
            self.value = type.value
        elif isinstance(type, tuple):
            self.type, self.value = type
        else:
            self.type = type
            self.value = value

    # Methods of convenience
    
    def is_key(self, key: str | None = None):
        """Checks if event is a key event
        ```
        event.is_key() # event is key event
        event.is_key("a") # "a" is pressed
        event.is_key(ptg.key.UP) # up arrow is pressed
        event.is_key("up") # up arrow is pressed
        event.is_key("ctrl-a") # Ctrl + a is pressed
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
    
    def value_passes(self, func: Callable[[Any], Any]):
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

_queue: list[Event] = []

def wait_for_event():
    """blocks until an event is triggered"""
    while True:
        _queue.extend(Event(KEYEVENT, x) for x in get_keys())
        if len(_queue):
            break
    return Event(_queue.pop(0))
    
def get() -> list[Event]:
    """non-blocking, should be used in tick-based games"""
    events = [Event(KEYEVENT, key) for key in get_keys()]
    events.extend(_queue)
    _queue.clear()

    return events

def add_event(event: EventLike):
    if not isinstance(event, Event):
        event = Event(event)
    _queue.append(event)

def wait_until(event: EventLike):
    """blocks until an event that meets the criteria is triggered
    Note: any events that are triggered while waiting are discarded
    For a more safer method to wait for events use wait_for_event()"""
    while True:
        for e in get():
            if event == e:
                return e

class EventProcessor(Protocol):
    """Tries to process the event and returns True if processed, else False.

    Example:
    ```python
    if sprite1.process(event):
        pass
    elif sprite2.process(event):
        pass
    ```
    """
    def process(self, event: Event) -> bool: ...
