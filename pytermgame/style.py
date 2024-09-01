from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:
    from .sprite import Sprite

COLOR_8 = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
    "default": 9,
}

class Colors(StrEnum):
    black = "black"
    red = "red"
    green = "green"
    yellow = "yellow"
    blue = "blue"
    magenta = "magenta"
    cyan = "cyan"
    white = "white"
    default = "default"

    @staticmethod
    def to_fg_ansi(color: Color):
        return f"\033[3{COLOR_8[color]}m"

    @staticmethod
    def to_bg_ansi(color: Color):
        return f"\033[4{COLOR_8[color]}m"

Color: TypeAlias = Colors | Literal["black", "red", "green", "yellow", "blue", "cyan", "white", "default"]

class Dir(Enum):
    left = "left"
    right = "right"
    top = up = "top"
    bottom = down = "bottom"
    center = "center"

@dataclass
class Style:
    """Styling options for sprites. Intended to be mutable.
    
    If set as Sprite.style, should not contain unspecified fields.
    """

    # we cannot set default values here because None means unspecified
    align_horizontal: Dir | None = None
    align_vertical: Dir | None = None
    fg: Color | None = None
    bg: Color | None = None
    bold: bool | None = None
    inverted: bool | None = None
    
    # used externally
    _resolved_priority: int | None = None

    @classmethod
    def default(cls):
        return cls(Dir.left, Dir.top, Colors.default, Colors.default, False, False)
    
    def merge(self, other: Style) -> bool:
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
        ansi = Colors.to_fg_ansi(self.fg) + Colors.to_bg_ansi(self.bg)
        if self.bold:
            ansi += "\033[1m"
        if self.inverted:
            ansi += "\033[7m"
        return ansi

# Priority:
# 0 = from parent(s), default also treated as parent
# 1 = from self

def _resolve_style(sprite: Sprite) -> Style:
    # affects parents

    resolved_style = Style.default()
    resolved_style._resolved_priority = 0

    for i, field in enumerate(fields(sprite.style)):
        val = getattr(sprite.style, field.name)
        if val is not None:
            setattr(resolved_style, field.name, val)
            resolved_style._resolved_priority |= (1 << i)

    if sprite._parent is not None:
        sprite._parent._resolved_style = parent_style = _resolve_style(sprite._parent)

        inverted = ~resolved_style._resolved_priority

        for i, field in enumerate(fields(parent_style)):
            if inverted & (1 << i):
                setattr(resolved_style, field.name, getattr(parent_style, field.name))

    return resolved_style
