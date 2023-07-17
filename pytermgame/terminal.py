import sys
import os
import platform

WINDOWS = platform.system() == "Windows"

width, height = os.get_terminal_size()

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
    # screen coords -> terminal coords
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
