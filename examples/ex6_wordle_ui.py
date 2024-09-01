# Same as ex6_wordle, but using UI structures

import pytermgame as ptg
import random

# with open("assets/wordle.txt") as f:
#     words = f.read().splitlines()
words = ["hello", "world"]

answer = random.choice(words)
round = 1

with ptg.Game(show_cursor=True) as game:
    win_or_lose = "lose"

    message = ptg.Value("Type and press enter ...").place((0, 0))

    # UI
    container = ptg.Border().wrap(
        column := ptg.ui.Column().wrap(
            word_input := ptg.TextInput()
        )
    ).place((0, 1))

    while game.loop():
        game.update()
        game.render()
     
        event = ptg.event.wait_for_event()

        if event.is_key(ptg.key.ENTER):
            if len(word_input.value) != 5:
                message.update_value("Word must be 5 letters long")
                continue
            if not all(x.isalpha() for x in word_input.value):
                message.update_value("Word must only contain letters")
                continue
            message.update_value("") # clear last message

            correct = 0
            char_sprites: list[ptg.Sprite] = []

            for i, char in enumerate(word_input.value):
                char_sprite = ptg.Text(char)

                if answer[i] == char:
                    color = "green"
                    correct += 1
                elif char in answer:
                    color = "yellow"
                else:
                    color = "red"
                
                char_sprite.apply_style(ptg.Style(fg = color))
                char_sprites.append(char_sprite)

            column.insert_child(
                # arrange characters side by side
                ptg.ui.Row(char_sprites),

                # insert above word input
                position = -1
            )
            
            if correct == 5:
                win_or_lose = "win"
                break
            
            if round == 5:
                win_or_lose = "lose"
                break
            
            # update input
            round += 1
            word_input.update_value("")
        
        elif word_input.process(event):
            pass

    ptg.Text(f"You {win_or_lose}! The word is {answer}!").place((0, 8))
    ptg.Text("Press space to exit").place((0, 9))
    ptg.cursor.hide()

    game.render()

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
