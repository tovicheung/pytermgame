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
class Style:
    """Styling options for sprites. Intended to be mutable.
    
    When it is set as Sprite.style:
    - styling for that sprite
    - should contain default values instead of None

    When it is passed as an argument to Sprite.set_style():
    - unspecified fields should be None
    """

    # we cannot set default values here because None means unspecified
    align_horizontal: Dir | None = None
    align_vertical: Dir | None = None
    fg: Color | None = None
    bg: Color | None = None
    bold: bool | None = None
    inverted: bool | None = None

    @classmethod
    def default(cls):
        return cls(Dir.left, Dir.top, Color.default, Color.default, False, False)
    
    def update(self, other: Style):
        changed = False
        for field in fields(other):
            val = getattr(other, field.name)
            if val is not None and getattr(self, field.name) != val:
                setattr(self, field.name, val)
                changed = True
        return changed
    
    def to_ansi(self):
        assert self.fg is not None, "Cannot call .to_ansi() on style without fg"
        assert self.bg is not None, "Cannot call .to_ansi() on style without bg"
        ansi = Color.to_fg_ansi(self.fg) + Color.to_bg_ansi(self.bg)
        if self.bold:
            ansi += "\033[1m"
        if self.inverted:
            ansi += "\033[7m"
        return ansi
