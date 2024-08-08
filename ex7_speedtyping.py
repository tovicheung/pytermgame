import pytermgame as ptg

import random
from pathlib import Path

with open(Path(__file__).parent / "assets/1000_common_words.txt") as f:
    words = f.read().splitlines()

with ptg.Game(show_cursor = True, alternate_screen = False) as game:
    pending_words: list[ptg.Value] = []
    relative_x = 0
    chars: list[ptg.Text] = []

    def generate_row_of_words(y: int):
        x = 0
        while x <= ptg.terminal.width() + 1:
            word = ptg.Value(random.choice(words)).place((x, y))
            pending_words.append(word)
            x += len(word.value) + 1
        
        word.kill() # remove the last one (that is out of bound)
        pending_words.pop()

        pending_words.append(None) # ugly hack to separate lines
    
    generate_row_of_words(y = 0)
    generate_row_of_words(y = 1)
    
    ONE_SEC = ptg.event.USEREVENT + 1

    started = False
    time = ptg.Counter(9).place((0, 4))
    time.hide()

    words_typed = 0
    correct_words_typed = 0
    chars_typed = 0
    wrong_chars_typed = 0
    stats = ptg.FText("{} WPM | {}% Accuracy", 0, 100).place((0, 3))
    
    pending_words[0].apply_style(fg = ptg.Color.yellow)
    
    ptg.cursor.goto(0, 0)

    while game.loop():
        for event in ptg.event.get():
            if event.is_key("space"):                
                pending_words[0].kill()
                pending_words.pop(0)

                relative_x = 0

                if pending_words[0] is None:
                    # new row
                    pending_words.pop(0)
                    for word in pending_words:
                        if word is not None:
                            word.move(0, -1)
                    generate_row_of_words(y = 1)

                    for char in chars:
                        char.kill()
                
                words_typed += 1
            
            elif event.is_key("backspace"):
                relative_x -= 1
                if relative_x < 0:
                    relative_x = 0
                c = chars.pop()
                chars_typed -= 1
                if c.style.fg == ptg.Color.red:
                    wrong_chars_typed -= 1
                c.kill()
                del c

            elif event.is_key() and event.value_passes(str.isascii):
                if not started:
                    started = True
                    ptg.clock.add_interval(ONE_SEC, secs=1)
                
                if relative_x >= len(pending_words[0].value):
                    continue

                char = ptg.Text(event.value).apply_style(fg = ptg.Color.green)
                chars.append(char)
                chars_typed += 1

                if event.value != pending_words[0].value[relative_x]:
                    char.apply_style(fg = ptg.Color.red)
                    wrong_chars_typed += 1
                
                char.place((pending_words[0].x + relative_x, 0))

                relative_x += 1

            elif event.is_type(ONE_SEC):
                time.increment()

                if time.value <= 0:
                    game.break_loop()

        if words_typed != 0 and chars_typed != 0:
            stats.format(words_typed / (time.value / 60), (chars_typed - wrong_chars_typed) * 100 // chars_typed)

        ptg.cursor.set_x(pending_words[0].x + relative_x)
        game.render()
        game.tick()
    
    ptg.event.wait_for_event()

