from .terminal import WINDOWS

if WINDOWS:
    UP = "\x00H"
    DOWN = "\x00P"
    LEFT = "\x00K"
    RIGHT = "\x00M"

    HOME = "\x00G"
    END = "\x00O"
    PAGEUP = "\x00I"
    PAGEDOWN = "\x00Q"

    DELETE = "\x00S"

    SPACE = " "
    ENTER = "\r"
    TAB = "\t"
else:
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    LEFT = "\x1b[D"
    RIGHT = "\x1b[C"

    HOME = "\x1b[H"
    END = "\x1b[F"
    PAGEUP = "\x1b[5~"
    PAGEDOWN = "\x1b[6~"

    DELETE = "\x1b[3~"

    # Linux, why?
    SPACE = ""
    ENTER = ""
    TAB = ""
