"""ptg.terminal

This submodule can be used independently for controlling the terminal.
"""

from typing import SupportsInt
from random import randint
import os
import sys

WINDOWS = sys.platform == "win32"

# Terminal size

def width():
    return os.get_terminal_size().columns

def height():
    return os.get_terminal_size().lines

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
