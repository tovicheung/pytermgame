from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum, IntEnum

class Color(IntEnum):
    black = 0
    red = 1
    green = 2
    yellow = 3
    blue = 4
    magenta = 5
    cyan = 6
    white = 7
    default = 9

    def to_fg_ansi(self):
        return f"\033[3{self.value}m"

    def to_bg_ansi(self):
        return f"\033[4{self.value}m"

class Dir(Enum):
    left = "left"
    right = "right"
    top = up = "top"
    bottom = down = "bottom"
    center = "center"

@dataclass
class Modifier:
    """Styling options for sprites
    
    When it is set as Sprite.modifier:
    - styling for that sprite
    - should contain default values instead of None

    When it is passed as an argument to Sprite.modify():
    - unspecified fields should be None
    """
    align_horizontal: Dir = None
    align_vertical: Dir = None
    foreground_color: Color = None
    background_color: Color = None

    @classmethod
    def default(cls):
        return cls(Dir.left, Dir.top, Color.default, Color.default)
    
    def update(self, other: Modifier):
        changed = False
        for field in fields(other):
            val = getattr(other, field.name)
            if val is not None and getattr(self, field.name) != val:
                setattr(self, field.name, val)
                changed = True
        return changed
