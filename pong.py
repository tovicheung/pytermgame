"""
pytermgame example: pong

Controls:
    w/s -> left player pad
    up/down arrow -> right player pad
Note: you can only control your pad when the ball is moving towards you
"""

import pytermgame as ptg
import random

def randabs(base: int, x: int) -> int:
    return random.randint(base-x, base+x)

class Ball(ptg.Sprite):
    surf = ptg.Surface("O")

    def new_round(self):
        # magnitude: random 1-2
        self.vx = (random.random() + 1) * (random.randint(0, 1) * 2 - 1)
        self.vy = (random.random() + 1) * (random.randint(0, 1) * 2 - 1)
        self.goto(randabs(ptg.terminal.width() // 2, 3), randabs(ptg.terminal.height() // 2, 3))

        # real coordinates
        self.rx, self.ry = self.x, self.y

    on_placed = new_round

    def update(self):
        if self.x < 0:
            score1.increment(1)
            self.new_round()
        if self.x > ptg.terminal.width() - 1:
            score2.increment(1)
            self.new_round()
        if self.y < 0:
            self.vy = abs(self.vy)
        if self.y > ptg.terminal.height() - 1:
            self.vy = -abs(self.vy)
        
        if self.is_colliding(pad1) or self.is_colliding(pad2):
            self.vx = -self.vx
        
        # Live data for debugging
        debugger.field("vx", self.vx).field("vy", self.vy)
        
        self.rx += self.vx
        self.ry += self.vy
        self.goto(round(self.rx), round(self.ry))

with ptg.Game(fps=30) as game:
    # Debugger setup - press d to activate
    debugger = game.get_debugger().block_on_key("d")

    pad1 = ptg.Object("*\n*\n*\n*").place((2, ptg.terminal.height() // 2))
    pad2 = ptg.Object("*\n*\n*\n*").place((ptg.terminal.width() - 2, ptg.terminal.height() // 2))

    mid = ptg.terminal.width() // 2

    score_middle = ptg.FText(":").place((mid, 0))
    score1 = ptg.Counter(0).align_right().place((mid - 2, 0))
    score2 = ptg.Counter(0).place((mid + 2, 0))

    ball = Ball().place((0, 0))

    while True:
        for event in ptg.event.get():
            # only let player at left side move when ball moving left, vice versa
            if ball.vx < 0:
                if event.is_key("w"):
                    pad1.move(0, -1)
                elif event.is_key("s"):
                    pad1.move(0, 1)
            if ball.vx > 0:
                if event.is_key(ptg.key.UP):
                    pad2.move(0, -1)
                elif event.is_key(ptg.key.DOWN):
                    pad2.move(0, 1)

        pad1.bound(y_min = 0, y_max = ptg.terminal.height() - pad1.surf.height)
        pad2.bound(y_min = 0, y_max = ptg.terminal.height() - pad2.surf.height)

        game.update()
        game.render()
        game.tick()
