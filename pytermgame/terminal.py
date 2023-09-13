import sys
import os
import platform
from random import randint

WINDOWS = platform.system() == "Windows"

def width():
    return os.get_terminal_size().lines

def height():
    return os.get_terminal_size().columns



def write(string: str):
    sys.stdout.write(string)

def flush():
    sys.stdout.flush()

def fwrite(string: str):
    write(string)
    flush()

def goto(x: int, y: int):
    write(f"\033[{y};{x}H")

def transform_coords(x: int, y: int):
    # screen coords (0, 0) based -> terminal coords (1, 1) based
    # may support extended axis scrolling in the future
    return x + 1, y + 1

def enable_alternate_buffer():
    fwrite("\033[?1049h")

def disable_alternate_buffer():
    fwrite("\033[?1049l")

def hide_cursor():
    fwrite("\033[?25l")

def show_cursor():
    fwrite("\033[?25h")

def clear():
    write("\033[2J")

def home():
    write("\033[H")

def full_clear(): # currently unused, may cause flickering
    os.system("cls" if os.name == "nt" else "clear")

def enable_autowrap():
    write("\033[?7h")

def disable_autowrap():
    write("\033[?7l")

# code helpers
def randy():
    return randint(0, height() - 1)
def randx():
    return randint(0, width() - 1)
