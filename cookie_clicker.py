"""
pytermgame example: cookie clicker
Press space, number keys to buy factories
(Instructions in game)
"""

import pytermgame as ptg

cookie_art = """ ___
/^  \\
|^ ^|
\\___/
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

    mycookie = Cookie().place((2, 2))
    ptg.Text("Press Space").place((0, 8))

    scoreboard = ptg.FText("You have {} cookies!", 0).place((0, 0))
    score = 0

    ptg.Text("Use number keys").place((20, 1))
    for i, factory in enumerate(factories, start=1):
        ptg.Text(f"Press [{i}] to buy a {factory[0]} using {factory[2]} cookies: {factory[1]} cps ").place((20, i + 1))
    

    space_last_pressed = 0

    running = True
    while running:
        for event in ptg.event.get():
            if event.is_key("q"):
                running = False
            elif event.is_key(ptg.key.SPACE):
                # Prevent holding
                time = ptg.clock.gettime()
                if time - 0.1 > space_last_pressed:
                    score += 1
                    scoreboard.format(score)
                space_last_pressed = time
            elif event.passes(str.isdigit):
                num = int(event.value)
                if 1 <= num <= 4:
                    factory = factories[num - 1]
                    if score >= factory[2]:
                        score -= factory[2]
                        scoreboard.format(score)
                        
                        # Here, we can use as_interval to prevent spawning many threads
                        # no difference because 1 sec = 30 ticks (not decimal ticks)
                        ptg.clock.set_timer(ptg.event.USEREVENT + num, 1, as_interval = True)
            # using ints as event types lets it encode additional information
            elif event.is_user():
                score += factories[event.type - ptg.event.USEREVENT - 1][1]
                scoreboard.format(score)

        game.update()
        game.render()
        game.tick()
