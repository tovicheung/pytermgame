# One-trick ponies that may come in handy
# Needs to be loaded separately via  from pytermgame import additional

from .game import Game
from . import terminal as term
from .sprites import FText

def require_termsize(min_width, min_height):
    if term.width() >= min_width and term.height() >= min_height:
        return
    
    # bubbles Ctrl-C
    with Game(silent_errors = ()) as game:
        indicator = FText(f"Minimum term dimension: {min_width}x{min_height} | current: {{}}x{{}}", term.width(), term.height()).place((0, 0))

        while not (term.width() >= min_width and term.height() >= min_height):
            indicator.format(term.width(), term.height())
            game.render()
            game.tick()
