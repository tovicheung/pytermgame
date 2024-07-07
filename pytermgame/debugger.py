from .sprite import Sprite
from .surface import Surface
from . import terminal as term
from . import _active

class Debugger(Sprite):
    surf = Surface("No debug info yet")

    def init(self):
        self.data = {}

    def field(self, key, value):
        self.data[key] = value
        self._dirty = 1
        return self

    def render(self, flush=True, erase=False):
        super().render(flush, True)
        self.surf = Surface(str(self.data))
        super().render(flush, erase)
    
    def block(self):
        while True:
            term.home()
            term.goto(0, term.height()-2)
            cmd = input("empty=leave | [t]ick | >").strip()
            if len(cmd) == 0:
                break
            elif cmd.startswith("t"):
                _active.get_active()._block_next_tick = True
                break
            term.clear()
            _active.get_scene().render()
        term.clear()
        _active.get_scene().render()
    
    def block_on_key(self, key: str):
        from . import event
        event._get = event.get
        def get():
            for ev in event._get():
                if ev == (event.KEYEVENT, key):
                    _active.get_active()._block_next_tick = True
                yield ev
        event.get = get
        return self
    
    def _unused_block_on_key(self, key: str):
        _active.get_active()._block_key = key
        return self
