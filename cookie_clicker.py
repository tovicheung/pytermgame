"""
pytermgame example: cookie clicker
Press space, number keys to buy factories
(Instructions in game)
"""

import pytermgame as ptg

cookie_art = """ ___
/^  \\
|^ ^|
\___/
"""

class Cookie(ptg.Sprite):
    surf = ptg.Surface(cookie_art)

factories = (
    # Name, Cookies per second, Price
    ("Small Factory", 1, 10),
    ("Big Factory", 10, 50),
    ("Very Big Factory", 50, 200),
    ("Very Very Big Factory", 200, 2000),
)

with ptg.Game() as game:
    NEWCOOKIE1 = ptg.event.USEREVENT + 1
    NEWCOOKIE2 = ptg.event.USEREVENT + 2
    NEWCOOKIE3 = ptg.event.USEREVENT + 3
    NEWCOOKIE4 = ptg.event.USEREVENT + 4

    mycookie = Cookie().place(2, 2)
    ptg.Text("Press Space").place(0, 8)

    scoreboard = ptg.FText("You have {} cookies!", 0).place(0, 0)
    score = 0

    ptg.Text("Use number keys").place(20, 1)
    for i, factory in enumerate(factories, start=1):
        ptg.Text(f"[{i}] {factory[0]}: {factory[1]}/s for {factory[2]}").place(20, i + 1)
    

    space_last_pressed = 0

    running = True
    while running:
        for event in ptg.event.get():
            if event.type == ptg.event.KEYEVENT:
                if event.value == "q":
                    running = False
                elif event.value == ptg.key.SPACE:
                    # Prevent holding
                    time = ptg.clock.gettime()
                    if time - 0.1 > space_last_pressed:
                        score += 1
                        scoreboard.format(score)
                    space_last_pressed = time
                elif event.value.isdigit():
                    num = int(event.value)
                    if 1 <= num <= 4:
                        factory = factories[num - 1]
                        if score >= factory[2]:
                            score -= factory[2]
                            scoreboard.format(score)
                            ptg.clock.set_timer(ptg.event.USEREVENT + num, 1)
            elif event.type > ptg.event.USEREVENT:
                score += factories[event.type - ptg.event.USEREVENT - 1][1]
                scoreboard.format(score)

        game.update()
        game.render()
        game.tick()
