# for testing keys cross platform, ignore
from pytermgame._get_key import get_keys

while True:
    a = get_keys()
    if len(a):
        print(a)
