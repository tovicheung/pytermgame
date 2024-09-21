"""
pytermgame example: jet and ball

Controls:
    up/down arrow keys -> jet movement
    h -> hide for 3 seconds

Goal:
    Dodge the balls and gain points
"""

import pytermgame as ptg

class Ball(ptg.Sprite):
    # default surface for all instances
    surf = ptg.Surface("O")

    # any new instances will be added to this group automatically
    group = ptg.Group()

    # default style for all instances
    style = ptg.Style(fg = "red")

    def on_placed(self):
        self.goto(ptg.terminal.width(), ptg.terminal.randy())

    def update(self):
        self.move(-1, 0)
    
        if self.is_colliding(ptg.viewport.left):
            score.increment()
            self.kill()
            return
        
        if self.is_colliding(myjet):
            game.break_loop()
        
        if self.is_colliding(myline):
            self.apply_style(fg = "red")
        else:
            self.apply_style(fg = "default")

class Line(ptg.Sprite):
    surf = ptg.Surface("-" * (ptg.terminal.width()))
    style = ptg.Style(fg = "blue")

    def update(self):
        if myjet.y != self.y:
            self.set_y(myjet.y)

with ptg.Game() as game:

    # Custom events

    NEWBALL = ptg.event.USEREVENT + 1
    SHOWJET = ptg.event.USEREVENT + 2

    game.add_interval(NEWBALL, ticks=5)

    # Sprites

    myline = Line().place((0, 0))

    ptg.Text("Score:").place((0, 1))
    score = ptg.Counter(0).place((7, 1))
    ptg.Text("Dodge the balls!").place((0, 0))

    myjet = ptg.Object("--->").place((4, 4))

    # Main game loop
    
    while game.loop():
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
                    ptg.clock.add_timer(SHOWJET, secs = 3, loops = 1)

            elif event == NEWBALL:
                Ball().place()
                # do not bind to name so that it can be garbage collected

            elif event == SHOWJET:
                myjet.show()

        game.update() # calls update() on every sprite
        game.render() # calls render() on appropriate sprites
        game.tick() # wait for next tick
    
    game.new_scene()

    ptg.Text(f"Game Over!\nScore: {score}\nPress Space to exit").place()
    game.render()

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
