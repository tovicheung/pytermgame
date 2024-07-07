"""
pytermgame example: pong

currently it's just a ball bouncing around
"""

import pytermgame as ptg
import random

class Ball(ptg.Sprite):
    surf = ptg.Surface("O")

    def init(self):
        self.vx = random.randint(1, 6) * (random.randint(0, 1) * 2 - 1)
        self.vy = random.randint(1, 3) * (random.randint(0, 1) * 2 - 1)

    def update(self):
        if self.x < 0:
            self.vx = abs(self.vx)
        if self.x > ptg.terminal.width() - 1:
            self.vx = -abs(self.vx)
        if self.y < 0:
            self.vy = abs(self.vy)
        if self.y > ptg.terminal.height() - 1:
            self.vy = -abs(self.vy)
        
        # Live data for debugging
        debugger.field("vx", self.vx).field("vy", self.vy)
        
        self.move(self.vx, self.vy)

with ptg.Game(fps=None) as game:
    # Debugger setup - press d to activate
    debugger = game.get_debugger().block_on_key("d")

    # pad = ptg.Object("*\n*\n*\n*").place((ptg.terminal.width() - 2, ptg.terminal.height() // 2))

    ball = Ball().place((5, 6))

    while True:
        # for event in ptg.event.get():
        #     if event.is_key(ptg.key.UP):
        #         pad.move(0, -1)
        #     elif event.is_key(ptg.key.DOWN):
        #         pad.move(0, 1)
        # pad.bound(y_min = 0, y_max = ptg.terminal.height() - pad.surf.height)

        game.update()
        game.render()
        game.tick()
