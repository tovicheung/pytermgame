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
    word_input = ptg.TextInput().place((0, round))

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
            message.update_value("") # clear last message

            # draw results
            correct = 0
            for i, char in enumerate(word_input.value):
                sprite = ptg.Text(char).place((i, round))
                if answer[i] == char:
                    color = ptg.Color.green
                    correct += 1
                elif char in answer:
                    color = ptg.Color.yellow
                else:
                    color = ptg.Color.red
                sprite.modify(ptg.Modifier(fg = color))
            
            if correct == 5:
                winlose = "win"
                game.break_loop()
            
            if round == 5:
                winlose = "lose"
                game.break_loop()
            
            # update input
            round += 1
            word_input.move(0, 1)
            word_input.update_value("")
        
        elif word_input.process(event):
            # word_input tries to process the event
            pass
    
    game.new_scene()

    ptg.Text(f"You {winlose}! The word is {answer}!").place()
    ptg.Text("Press space to exit").place((0, 1))
    ptg.cursor.hide()

    game.render()

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
