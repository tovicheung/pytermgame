from .terminal import WINDOWS

if WINDOWS:
    import msvcrt
    def getchar():
        if msvcrt.kbhit():
            return chr(int.from_bytes(msvcrt.getch(), "big"))

    def getkey() -> str:
        ch = getchar()
        if ch is None:
            return ch
        # if it is a normal character, return it
        if ch not in "\x00\xe0":
            return ch
        # if it is a special key, read second half
        ch2 = getchar()
        if ch2 is None:
            return ch
        return "\x00" + ch2

    def get_keys() -> list[str]:
        keys = []
        while msvcrt.kbhit():
            keys.append(getkey())
        return keys
else:
    import sys
    import os
    import select
    
    fd = sys.stdin.fileno()
    
    def     get_keys() -> list[str]:
        chars = []
        while True:
            r, w, x = select.select([sys.stdin], [], [], 0.0)
            if r:
                key = os.read(fd, 1024).decode().strip()
                chars.append(key)
            else:
                break

        keys = []
        while len(chars):
            c1 = chars.pop(0)

            if c1 != "\x1B":
                keys.append(c1)
                continue

            c2 = chars.pop(0)
            if c2 not in "\x4F\x5B":
                keys.append(c1 + c2)
                continue

            c3 = chars.pop(0)
            if c3 not in "\x31\x32\x33\x35\x36":
                keys.append(c1 + c2 + c3)
                continue

            c4 = chars.pop(0)
            if c4 not in "\x30\x31\x33\x34\x35\x37\x38\x39":
                keys.append(c1 + c2 + c3 + c4)
                continue

            c5 = chars.pop(0)
            keys.append(c1 + c2 + c3 + c4 + c5)

        return keys
