import pytermgame as ptg

class Jet(ptg.Sprite):
    surf = ptg.Surface("--->")

class Ball(ptg.Sprite):
    surf = ptg.Surface("O")
    # any new instances will be added to this group on init
    group = ptg.Group()

    def init(self):
        self.goto(ptg.terminal.width, ptg.randint(0, ptg.terminal.height - 1))

    def update(self):
        # called from Ball.group.update()
        self.move(-1, 0)
        if self.x == 0:
            global score
            score += 1
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

    score = 0
    t = ptg.Text("Dodge the balls!", 0, 0).place()

    # Jet
    myjet = Jet(4, 4).place()

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
                    if not myjet.hidden:
                        myjet.hide()
                        ptg.event.delay(SHOWJET, 3000)

            elif event.type == NEWBALL:
                Ball().place()
                # not binded to name to prevent hogging up memory

            elif event.type == SHOWJET:
                myjet.show()

        Ball.group.update()
        game.render() # update screen
        game.tick() # wait for next tick
