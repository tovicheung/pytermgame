"""ptg.terminal

This submodule can be used independently for controlling the terminal.
"""

from functools import wraps
import os
from random import randint
import sys
from typing import Any, SupportsInt

# Terminal size

## Normal use

def width():
    return os.get_terminal_size().columns

def height():
    return os.get_terminal_size().lines

## Internal use

_width, _height = width, height

def disable_size_cache():
    global width, height
    width, height = _width, _height

def set_size_cache():
    global width, height
    w, h = os.get_terminal_size()
    width = wraps(_width)(lambda: w)
    height = wraps(_height)(lambda: h)

# I/O

def write(string: str, flush: bool = False):
    sys.stdout.write(string)
    if flush:
        sys.stdout.flush()

def flush():
    sys.stdout.flush()

# Terminal configuration

if sys.platform != "win32":
    import termios
    import fcntl

def config_raw() -> tuple[int, list[Any], int]:
    """Returns old (fd, attrs, flags)"""
    if sys.platform == "win32":
        return 0, [], 0
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    new_attrs = termios.tcgetattr(fd)
    new_attrs[3] = new_attrs[3] & ~(termios.ICANON | termios.ECHO)
    termios.tcsetattr(fd, termios.TCSANOW, new_attrs)
    old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)

    return fd, old_attrs, old_flags

def config_normal() -> tuple[int, list[Any], int]:
    """Returns old (fd, attrs, flags)"""
    if sys.platform == "win32":
        return 0, [], 0
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    new_attrs = termios.tcgetattr(fd)
    new_attrs[3] = new_attrs[3] | termios.ICANON | termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, new_attrs)
    old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, old_flags & (~os.O_NONBLOCK))

    return fd, old_attrs, old_flags

def config(fd: int, old_attrs: list[Any], old_flags: int):
    if sys.platform == "win32":
        return
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_attrs)
    fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)

def enable_alternate_buffer(flush: bool = True):
    write("\033[?1049h", flush)

def disable_alternate_buffer(flush: bool = True):
    write("\033[?1049l", flush)

def enable_autowrap():
    write("\033[?7h")

def disable_autowrap():
    write("\033[?7l")

# Cursor

def goto(x: SupportsInt, y: SupportsInt):
    """Note: 1-based"""
    write(f"\033[{int(y)};{int(x)}H")

def hide_cursor(flush: bool = True):
    write("\033[?25l", flush)

def show_cursor(flush: bool = True):
    write("\033[?25h", flush)

def home():
    write("\033[H")

# Clear

def reset():
    write("\033c")

def clear():
    write("\033[2J")
    home() # scroll so that dirty screen is pushed away

def system_clear():
    # currently unused, may cause flickering
    os.system("cls" if os.name == "nt" else "clear")

# Helpers

def randy():
    return randint(0, height() - 1)

def randx():
    return randint(0, width() - 1)

def is_valid_term_coords(x: SupportsInt, y: SupportsInt):
    # Note: 1-based coords
    return 1 <= int(x) <= width() and 1 <= int(y) <= height()

# Events

from . import _get_key

mouse_enabled = False

if sys.platform == "win32":
    from typing import Any, final
    import win32console
    import win32con
    @final
    class PyCOORD:
        @property
        def X(self): ...
        @property
        def Y(self): ...

    @final
    class PyINPUT_RECORD:
        EventType: int
        KeyDown: int | bool
        RepeatCount: int
        VirtualKeyCode: int
        VirtualScanCode: Any
        Char: str
        ControlKeyState: int
        ButtonState: int
        EventFlags: int
        MousePosition: PyCOORD
        Size: PyCOORD
        SetFocus: Any
        CommandId: Any

    ENABLE_EXTENDED_FLAGS = 0x0080

    MOUSE_SCROLL_UP = 8388608
    MOUSE_SCROLL_DOWN = 4286578688

    win_in = None
    old_mode = None

    def setup_mouse_input():
        global win_in, old_mode, mouse_enabled
        win_in = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
        old_mode = win_in.GetConsoleMode()
        win_in.SetConsoleMode(win32console.ENABLE_MOUSE_INPUT | ENABLE_EXTENDED_FLAGS) # 0x0080 is EXTENDED_FLAGS
        mouse_enabled = True
    
    def reset_mouse_input():
        global mouse_enabled
        win_in.SetConsoleMode(old_mode)
        mouse_enabled = False
        
    def get_events() -> list:
        if mouse_enabled:
            num_events = win_in.GetNumberOfConsoleInputEvents()
            if num_events <= 0:
                return []
            return list(win_in.ReadConsoleInput(num_events))
        return _get_key.get_keys()

else:
    ...


