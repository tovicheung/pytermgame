from typing import Any

from ._get_key import get_keys

class Event:
    __slots__ = ("type", "value")
    def __init__(self, type: int | tuple[int, int], value: Any = None):
        if isinstance(type, tuple):
            self.type, self.value = type
        else:
            self.type = type
            self.value = value

    # Convenient methods
    
    def is_key(self, key: str | None = None):
        if key is None:
            return self.type == KEYEVENT
        return self.type == KEYEVENT and self.value == key
    
    def is_type(self, type: int):
        return self.type == type

    def as_pair(self):
        return (self.type, self.value)

    def __eq__(self, other: tuple[int, Any] | int):
        if isinstance(other, int):
            # used as event == TYPE
            return self.is_type(other)
        return self.as_pair() == other

EventLike = int | tuple[int, int] | Event

EXIT = 1 # unused for now
KEYEVENT = 2
MOUSECLICK = MOUSELEFTCLICK = 3 # unused for now
MOUSERIGHTCLICK = 4 # unused for now
MOUSESCROLLUP = 5 # unused for now
MOUSESCROLLDOWN = 6 # unused for now
USEREVENT = 31

queue: list[Event] = [] # should not be exposed

def get():
    for key in get_keys():
        yield Event(KEYEVENT, key)
    queued = queue.copy()
    queue.clear()
    for event in queued:
        yield event

def add_event(event: EventLike):
    if not isinstance(event, Event):
        event = Event(event)
    queue.append(event)
