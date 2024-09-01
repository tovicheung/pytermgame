"""
pytermgame example: cookie clicker

Controls:
    space -> get 1 cookie
    number keys -> buy factories

Goal:
    Get cookies
"""

import pytermgame as ptg

cookie_art = """ ___
/^  \\
|^ ^|
\\___/
"""

factories_data = (
    # Name, Cookies per second, Cost
    ("Small Factory", 1, 10),
    ("Big Factory", 10, 50),
    ("Very Big Factory", 50, 200),
    ("Very Very Big Factory", 200, 2000),
)

class Factory(ptg.Text):
    def __init__(self, id: int, name: str, cookies_per_second: int, cost: int):
        super().__init__(f"[{id}] [cost: {cost}] {name} ({cookies_per_second} cookies per second)")
        self.cookies_per_second = cookies_per_second
        self.cost = cost
    
    def update(self):
        if score >= self.cost:
            self.apply_style(fg = "green")
        else:
            self.apply_style(fg = "red")

factories: list[Factory] = []

with ptg.Game() as game:

    COOKIES_PRODUCED = ptg.event.USEREVENT + 1
    COOKIE_DIM = ptg.event.USEREVENT + 2

    # Cookie

    cookie = ptg.Object(cookie_art) \
        .apply_style(bold = True) \
        .place((2, 2))

    ptg.Text("Press Space").place((0, 8))

    # Scoreboard

    scoreboard = ptg.FText("You have {} cookies!", 0).place((0, 0))
    score = 0

    # Factories

    ptg.Text("Use number keys").place((20, 1))
    for i, data in enumerate(factories_data, start=1):
        factories.append(Factory(i, *data).place((20, i + 1)))

    space_last_pressed_time = 0

    while game.loop():
        # Read events
        for event in ptg.event.get():

            if event.is_key("q"):
                # Quit
                game.break_loop()

            elif event.is_key(ptg.key.SPACE):
                # Prevent holding space
                time = ptg.clock.get_time()

                # Must at least have 0.1s between presses
                if time - 0.1 > space_last_pressed_time:
                    score += 1
                    scoreboard.format(score)

                    # mini animation
                    cookie.apply_style(fg = "yellow")
                    game.add_interval(COOKIE_DIM, ticks=1, loops=1)
                
                space_last_pressed_time = time

            elif event.is_key() and event.value_passes(str.isdigit):
                # Number key pressed
                num = int(event.value)
                # is a valid numer key
                if 1 <= num <= 4:
                    factory = factories[num - 1]
                    if score >= factory.cost:
                        score -= factory.cost
                        scoreboard.format(score)
                        
                        ptg.clock.add_timer(
                            # (event type, event value)
                            (COOKIES_PRODUCED, factory.cookies_per_second),
                            secs = 1
                        )

            elif event.is_type(COOKIES_PRODUCED):
                score += event.value
                scoreboard.format(score)
            
            elif event.is_type(COOKIE_DIM):
                cookie.apply_style(fg = "default")

        game.update()
        game.render()
        game.tick()
