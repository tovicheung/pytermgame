# Under development

from typing import TypeAlias, Generator, Callable, ParamSpec, Concatenate

from . import terminal as term

P = ParamSpec("P")
Transition: TypeAlias = Callable[Concatenate[int, P], Generator[int, None, None]]

F_NONE = 0
F_SWITCH = 1
F_RENDER = 2
F_RENDER_AFTER_TICK = 4
F_CLEAR = 8

def fill(ticks: int, char: str = " ", ansi: str = "\033[7m"):
    for _ in range(ticks):
        term.home()
        term.write(ansi + ((term.width() * char + "\n") * term.height()).rstrip("\n"))
        term.flush()
        yield F_NONE

def wipe(ticks: int, char: str = " ", ansi: str = "\033[7m"):
    mid = ticks // 2
    for tick in range(mid):
        width = term.width()
        
        x = round(width - width / mid * tick)
        w = width - x

        if x < 0:
            term.reset()
                
        for y in range(term.height()):
            term.goto(x + 1, y + 1)
            term.write(ansi + char * w)
        
        term.flush()

        yield F_NONE
    
    yield F_SWITCH

    for tick in range(ticks - mid):
        w = round(width - width / (ticks - mid) * tick)

        for y in range(term.height()):
            term.goto(1, y + 1)
            term.write(ansi + char * w + "\033[m" + " " * w)
        
        term.flush()

        yield F_NONE


"""

    def _switch_scene(self, scene: Scene, transition: Transition, ticks: int):
        # Unused
        switched = False
        for flags in transition(ticks):
            if flags & _transition.F_SWITCH:
                self.scene = scene
                switched = True
            if flags & _transition.F_CLEAR:
                terminal.clear()
            if flags & _transition.F_RENDER:
                self.scene.render(flush=True)
            self.tick()
            if flags & _transition.F_RENDER_AFTER_TICK:
                self.scene.render(flush=True)
        
        if not switched:
            self.scene = scene

        terminal.clear()
        terminal.reset()
        scene.render()
"""
