import sys
import os
import platform
from random import randint

# WINDOWS = platform.system() == "Windows"
WINDOWS = sys.platform == "win32" # most stubs use this

# Terminal size

def width():
    return os.get_terminal_size().columns

def height():
    return os.get_terminal_size().lines

# I/O

def write(string: str):
    sys.stdout.write(string)

def flush():
    sys.stdout.flush()

def fwrite(string: str):
    write(string)
    flush()

# Terminal config

def enable_alternate_buffer():
    fwrite("\033[?1049h")

def disable_alternate_buffer():
    fwrite("\033[?1049l")

def enable_autowrap():
    write("\033[?7h")

def disable_autowrap():
    write("\033[?7l")

# Cursor

def goto(x: int, y: int):
    write(f"\033[{y};{x}H")

def hide_cursor():
    fwrite("\033[?25l")

def show_cursor():
    fwrite("\033[?25h")

def home():
    write("\033[H")

# Clear

def clear():
    write("\033[2J")

def full_clear():
    # currently unused, may cause flickering
    os.system("cls" if os.name == "nt" else "clear")

# Helpers

def randy():
    return randint(0, height() - 1)
def randx():
    return randint(0, width() - 1)
