# for development use

from __future__ import annotations

from dataclasses import dataclass
import typing

from .sprite import Sprite
from .surface import Surface

if typing.TYPE_CHECKING:
    from .game import Game

@dataclass
class ProfileException(BaseException):
    msg: str
    profiler: Profiler

    def __str__(self):
        return "Profiler raised an exception: " + self.msg + "\nGame state:\n" + str(self.profiler.state)

def _ifnone(val, none):
    if val is None:
        return none
    return val

def _fmt(val, ifnone=0):
    if val is None:
        return _fmt(ifnone)
    if isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        return val.__format__(".4f")

@dataclass
class State:
    tick_durations: list
    sprites: int
    intervals: int
    live_fps: float
    average_fps: float | None

    @classmethod
    def new(cls):
        return cls([], 0, 0, 0, None)
    
    def __str__(self):
        return f"live_fps={_fmt(self.live_fps)}\naverage_fps={_fmt(self.average_fps, ifnone=0)}\nsprites={self.sprites}\nintervals={self.intervals}"

class Profiler:
    """To monitor and analyze a game
    
    The game (or any other part of ptg) does not know about the profiler (unlike the debugger)
    """

    def __init__(self, game: Game, sample_ticks=10):
        self.game = game
        self.sample_ticks = sample_ticks
        self.state = State.new()

    def err(self, msg):
        raise ProfileException(str(msg), self)
    
    def tick(self):
        self.state.live_fps = 0 if self.game._last_tick_dur is None or self.game._last_tick_dur <= 0 else 1 / self.game._last_tick_dur
        self.state.tick_durations.append(self.game._last_tick_dur)
        if len(self.state.tick_durations) > self.sample_ticks:
            self.state.tick_durations.pop(0)
        
        sum_ = sum(self.state.tick_durations)
        if sum_ == 0:
            self.state.average_fps = None
        else:
            self.state.average_fps = 1 / (sum_ / len(self.state.tick_durations))
        
        self.state.sprites = len(self.game.scene.sprites)
        self.state.intervals = len(self.game.intervals)

        return self

    def min_fps(self, min_fps):
        fps = self.state.live_fps
        if fps is not None and fps < min_fps:
            self.err(f"Game fps ({_fmt(fps)}) is lower than minimum ({_fmt(min_fps)})")
        return self

    def min_average_fps(self, min_fps):
        a = self.state.average_fps
        if a is not None and a < min_fps:
            self.err(f"Game fps ({_fmt(a)}) is lower than minimum ({_fmt(min_fps)})")
        return self
    
    def with_display(self):
        return (self, ProfileDisplay(self.state).place((0, 5)))

class ProfileDisplay(Sprite):
    def __init__(self, state: State):
        self.state = state
        self.surf = Surface("<No data>")
        super().__init__()

    def update(self):
        self.surf = Surface(str(self.state))
        self._rendered.dirty = True
