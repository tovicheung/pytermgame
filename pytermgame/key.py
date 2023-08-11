from .terminal import WINDOWS

if WINDOWS:
    UP = "\x00H"
    DOWN = "\x00P"
    LEFT = "\x00K"
    RIGHT = "\x00M"

    SPACE = " "
else:
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    LEFT = "\x1b[D"
    RIGHT = "\x1b[C"

    SPACE = "" # Linux, why?
