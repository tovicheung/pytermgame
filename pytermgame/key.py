import sys

from . import _key_win, _key_posix
from .terminal import WINDOWS

# Check if _key_win and _key_posix entries match

if _key_win.__dict__.keys() != _key_posix.__dict__.keys():
    win = set(filter(lambda s: s[0] != "_", _key_win.__dict__.keys()))
    posix = set(filter(lambda s: s[0] != "_", _key_posix.__dict__.keys()))
    diffwin = win.difference(posix)
    diffposix = posix.difference(win)
    raise AssertionError(f"_key_win and _key_posix have different entries\nwin - posix: {diffwin}\nposix - win: {diffposix}")

if sys.platform == "win32":
    from ._key_win import *
else:
    from ._key_posix import *

# Common entires across windows and posix

CR = "\r"
LF = "\n"
SPACE = " "
TAB = "\t"
ESC = "\x1b"

CTRL_A = "\x01"
CTRL_B = "\x02"
CTRL_C = "\x03"
CTRL_D = "\x04"
CTRL_E = "\x05"
CTRL_F = "\x06"
CTRL_G = "\x07"
CTRL_H = "\x08"
CTRL_I = TAB
CTRL_J = LF
CTRL_K = "\x0b"
CTRL_L = "\x0c"
CTRL_M = CR
CTRL_N = "\x0e"
CTRL_O = "\x0f"
CTRL_P = "\x10"
CTRL_Q = "\x11"
CTRL_R = "\x12"
CTRL_S = "\x13"
CTRL_T = "\x14"
CTRL_U = "\x15"
CTRL_V = "\x16"
CTRL_W = "\x17"
CTRL_X = "\x18"
CTRL_Y = "\x19"
CTRL_Z = "\x1a"
