# for testing keys cross platform

import pytermgame as ptg
from pytermgame._get_key import get_keys

with ptg.Game(alternate_screen=False):
    while True:
        a = get_keys()
        if len(a):
            print(a)
