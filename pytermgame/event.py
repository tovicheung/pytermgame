from ._get_key import get_keys

class Event:
    __slots__ = ("type", "value")
    def __init__(self, type, value = None):
        self.type = type
        self.value = value

KEYEVENT = 2
USEREVENT = 31

queue = [] # should not be exposed

def get():
    for key in get_keys():
        yield Event(KEYEVENT, key)
    queued = queue.copy()
    queue.clear()
    for event in queued:
        yield event

def add_event(event: int | Event):
    if not isinstance(event, Event):
        event = Event(event)
    queue.append(event)
