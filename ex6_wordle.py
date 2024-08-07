"""
pytermgame example: simple wordle

Controls:
    type and press enter

Note: this is very simple wordle, no word validity checks
"""

import pytermgame as ptg

import random

with open("assets/wordle.txt") as f:
    words = f.read().splitlines()

answer = random.choice(words)

round = 1

with ptg.Game(show_cursor=True) as game:
    winlose = "lose"

    message = ptg.Value("Type and press enter ...").place()
    border = ptg.sprites.Border(inner_width=7, inner_height=1).place((0, 1))
    word_input = ptg.TextInput().place((2, 2))

    # This example demonstrates an alternative game structure

    while game.loop():

        # game updates and renders first
        game.update()
        game.render()

        # then blocks until an event is available        
        event = ptg.event.wait_for_event()

        if event.is_key(ptg.key.ENTER):
            # 5-letter check
            if len(word_input.value) != 5:
                message.update_value("Word must be 5 letters long")
                continue
            if not all(x.isalpha() for x in word_input.value):
                message.update_value("Word must only contain letters")
                continue
            message.update_value("") # clear last message

            # draw results
            correct = 0
            for i, char in enumerate(word_input.value):
                sprite = ptg.Text(char).place((2 + i, 1 + round))
                if answer[i] == char:
                    color = ptg.Color.green
                    correct += 1
                elif char in answer:
                    color = ptg.Color.yellow
                else:
                    color = ptg.Color.red
                sprite.apply_style(ptg.Style(fg = color))
            
            if correct == 5:
                winlose = "win"
                # game.break_loop()
                break
                # here we can break directly as there is only one layer of loop
            
            if round == 5:
                winlose = "lose"
                # game.break_loop()
                break
            
            # update input
            round += 1
            word_input.move(0, 1)
            word_input.update_value("")
            border.resize(inner_width=7, inner_height=border.inner_height+1)
        
        elif word_input.process(event):
            # word_input tries to process the event
            pass

    ptg.Text(f"You {winlose}! The word is {answer}!").place((0, 8))
    ptg.Text("Press space to exit").place((0, 9))
    ptg.cursor.hide()

    game.render()

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
