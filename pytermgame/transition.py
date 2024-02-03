"""ptg.transition

Simple transitions between scenes

Future plans:
generalize into "effects" that sprites can also activate
"""

from typing import TypeAlias, Generator, Callable, ParamSpec, Concatenate

from . import terminal as term

P = ParamSpec("P")
Transition: TypeAlias = Callable[Concatenate[int, P], Generator[int, None, None]]

F_NONE = 0
F_SWITCH = 1
F_RENDER = 2

def fill(ticks: int, char: str = " ", ansi: str = "\033[7m"):
    for _ in range(ticks):
        term.home()
        term.write(ansi)
        term.write(((term.width() * char + "\n") * term.height()).rstrip("\n"))
        term.flush()
        yield F_NONE

def wipe(ticks: int, char: str = " ", ansi: str = "\033[7m"):
    mid = ticks // 2
    for tick in range(ticks):
        width = term.width()
        
        realx = round(width - width * 2 / ticks * tick)
        x = max(realx, 0)
        w = width - abs(realx)

        if realx < 0:
            term.reset()
                
        for y in range(term.height()):
            term.goto(x + 1, y + 1)
            term.write(ansi + char * w)
        
        term.flush()

        if tick == mid:
            yield F_SWITCH
        elif tick > mid:
            yield F_RENDER
        else:
            yield F_NONE
