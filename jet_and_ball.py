import pytermgame as ptg

class Jet(ptg.Sprite):
    surf = ptg.Surface("--->")

class Ball(ptg.Sprite):
    surf = ptg.Surface("O")
    # any new instances will be added to this group on init
    group = ptg.Group()

    def init(self):
        self.goto(ptg.terminal.width, ptg.randy())

    def update(self):
        # called from Ball.group.update()
        self.move(-1, 0)
        if self.x == 0:
            self.kill()
            return
        if self.touching(myjet):
            global running
            running = False

with ptg.Game() as game:
    # Custom event
    NEWBALL = ptg.event.USEREVENT + 1
    SHOWJET = ptg.event.USEREVENT + 2
    ptg.event.set_timer(NEWBALL, 500)

    # Jet
    myjet = Jet()
    myjet.goto(4, 4)

    # game loop
    running = True
    while running:
        for event in ptg.event.get():

            if event.type == ptg.event.KEYEVENT:
                if event.value == ptg.key.UP:
                    if myjet.y > 0:
                        myjet.move(0, -1)
                elif event.value == ptg.key.DOWN:
                    if myjet.y < ptg.terminal.height - 1:
                        myjet.move(0, 1)
                elif event.value == "h":
                    myjet.hide()
                    ptg.event.delay(SHOWJET, 3000)

            elif event.type == NEWBALL:
                Ball()
                # not binded to name to prevent hogging up memory

            elif event.type == SHOWJET:
                myjet.show()

        Ball.group.update()
        game.update() # update screen
        game.tick() # wait for next tick
