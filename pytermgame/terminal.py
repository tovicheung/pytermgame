"""ptg.terminal

This submodule can be used independently for controlling the terminal.
"""

from functools import wraps
import os
from random import randint
import sys
from typing import SupportsInt

WINDOWS = sys.platform == "win32"

# Terminal size

## Normal use

def width():
    return os.get_terminal_size().columns

def height():
    return os.get_terminal_size().lines

## Internal use

def _enable_size_cache():
    global _width, _height
    _width, _height = width, height
    _update_size_cache()

def _disable_size_cache():
    global width, height
    width, height = _width, _height

def _update_size_cache():
    global width, height
    w, h = os.get_terminal_size()
    width = wraps(width)(lambda: w)
    height = wraps(height)(lambda: h)

# I/O

def write(string: str, flush=False):
    sys.stdout.write(string)
    if flush:
        sys.stdout.flush()

def flush():
    sys.stdout.flush()

# Terminal configuration

def enable_alternate_buffer(flush=True):
    write("\033[?1049h", flush)

def disable_alternate_buffer(flush=True):
    write("\033[?1049l", flush)

def enable_autowrap():
    write("\033[?7h")

def disable_autowrap():
    write("\033[?7l")

# Cursor

def goto(x: SupportsInt, y: SupportsInt):
    """Note: 1-based"""
    write(f"\033[{int(y)};{int(x)}H")

def hide_cursor(flush=True):
    write("\033[?25l", flush)

def show_cursor(flush=True):
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
