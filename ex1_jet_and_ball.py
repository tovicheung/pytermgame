"""
pytermgame example: jet and ball

Controls:
    up/down arrow keys -> jet movement
    h -> hide for 3 seconds

Goal:
    Dodge the balls and gain points
"""

import pytermgame as ptg

class Jet(ptg.Sprite):
    surf = ptg.Surface("--->")

class Ball(ptg.Sprite):
    surf = ptg.Surface("O")
    # any new instances will be added to this group automatically
    group = ptg.Group()

    def on_placed(self):
        self.goto(ptg.terminal.width(), ptg.terminal.randy())

    def update(self):
        self.move(-1, 0)
        if self.x == 0:
            score.increment()
            self.kill()
            return
        if self.is_colliding(myjet):
            global running
            running = False
        if self.is_colliding(myline):
            self.color_all("\033[31m")
        else:
            self.color_all("\033[m")

class Line(ptg.Sprite):
    surf = ptg.Surface("-" * (ptg.terminal.width()))

    def init(self):
        self.color_all("\033[38;5;245m")

    def update(self):
        if myjet.y != self.y:
            self.set_y(myjet.y)

with ptg.Game() as game:

    # Custom events

    NEWBALL = ptg.event.USEREVENT + 1
    SHOWJET = ptg.event.USEREVENT + 2

    ptg.clock.set_interval(NEWBALL, 5)

    # Sprites

    myline = Line().place((0, 0))

    ptg.Text("Score:").place((0, 1))
    score = ptg.Counter(0).place((7, 1))
    ptg.Text("Dodge the balls!").place((0, 0))

    myjet = ptg.Object(ptg.Surface("--->")).place((4, 4))

    # Pre-load another scene using context managers

    with ptg.Scene() as end:
        ptg.Text(f"Game Over!\nScore: {score}\nPress Space to exit").place()

    # Main game loop

    running = True

    while running:
        for event in ptg.event.get():
            if event.is_key(ptg.key.UP):
                if myjet.y > 0:
                    myjet.move(0, -1)
                    
            elif event.is_key(ptg.key.DOWN):
                if myjet.y < ptg.terminal.height() - 1:
                    myjet.move(0, 1)

            elif event.is_key("h"):
                if not myjet.hidden:
                    myjet.hide()
                    ptg.clock.delay(SHOWJET, 3)

            elif event.is_key(): ... # block all key events

            elif event == NEWBALL:
                Ball().place()
                # do not bind to name so that it can be garbage collected

            elif event == SHOWJET:
                myjet.show()

        game.update() # calls update() on every sprite
        game.render() # calls render() on appropriate sprites
        game.tick() # wait for next tick
    
    game.set_scene(end)

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
