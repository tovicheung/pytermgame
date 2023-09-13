"""
pytermgame example: jet and ball
Use up and down arrow keys to control your jet
Dodge the balls
The grey line is for alignment
"""

import pytermgame as ptg

class Jet(ptg.Sprite):
    surf = ptg.Surface("--->")

class Ball(ptg.Sprite):
    surf = ptg.Surface("O")
    # any new instances will be added to this group on init
    group = ptg.Group()

    def init(self):
        self.goto(ptg.terminal.width(), ptg.terminal.randy())

    def update(self):
        self.move(-1, 0)
        if self.x == 0:
            score.increment()
            self.kill()
            return
        if self.touching(myjet):
            global running
            running = False
        if self.touching(myline):
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
    # Custom event
    NEWBALL = ptg.event.USEREVENT + 1
    SHOWJET = ptg.event.USEREVENT + 2
    # ptg.clock.set_timer(NEWBALL, 300)
    ptg.clock.set_interval(NEWBALL, 5)

    myline = Line().place(0, 0)

    # text and scores
    ptg.Text("Score:").place(0, 1)
    score = ptg.Counter(0).place(7, 1) # you can specify initial coords in place()
    ptg.Text("Dodge the balls!", 0, 0).place() # or in the constructor

    # Jet
    myjet = Jet().place(4, 4)

    # game loop
    running = True
    while running:
        for event in ptg.event.get():
            if event.type == ptg.event.KEYEVENT:

                if event.value == ptg.key.UP:
                    if myjet.y > 0:
                        myjet.move(0, -1)
                elif event.value == ptg.key.DOWN:
                    if myjet.y < ptg.terminal.height() - 1:
                        myjet.move(0, 1)
                elif event.value == "h":
                    if not myjet.hidden:
                        myjet.hide()
                        ptg.clock.delay(SHOWJET, 3)

            elif event.type == NEWBALL:
                Ball().place()
                # do not bind to name to prevent hogging up memory

            elif event.type == SHOWJET:
                myjet.show()

        game.update() # calls update() on every sprite
        game.render() # calls render() on appropriate sprites
        game.tick() # wait for next tick
