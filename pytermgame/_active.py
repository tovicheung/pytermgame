"""ptg._active

This internal submodule is made to avoid circular imports.
References to the active game is often required in other submodules such as ptg.sprite,
but importing the whole ptg.game submodule will likely cause circular imports
as ptg.game also depends on those submodules.

This submodule does not depend on any other submodules, and can be safely imported without circular imports.
However, functions in this submodule should not be called directly upon importing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from functools import wraps

if TYPE_CHECKING:
    from .game import Game as _GameType

# This will be set to True by ptg.game
initialized = False

# This will be set to the Game class by ptg.game
Game: type[_GameType] = None # type: ignore

def wrap(f):
    @wraps(f)
    def new(*args, **kwargs):
        if not initialized:
            raise Exception(f"{f.__qualname__} should only be called after ptg.game is imported")
        return f(*args, **kwargs)
    return new

@wrap
def get_active():
    return Game.get_active()

@wrap
def get_scene():
    return Game.get_scene()

@wrap
def is_active():
    return Game._active is None
