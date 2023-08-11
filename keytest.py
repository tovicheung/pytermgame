# for testing keys cross platform, ignore
from pytermgame._get_key import get_keys
from pytermgame import Game

with Game(alternate_screen=False):
    while True:
        a = get_keys()
        if len(a):
            print(a)
