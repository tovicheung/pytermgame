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

class Ball(ptg.KinematicSprite):
    surf = ptg.Surface("O")

    def new_round(self):
        self.vx = round(random.random() + 1) * (random.randint(0, 1) * 2 - 1)
        self.vy = round(random.random() + 1) * (random.randint(0, 1) * 2 - 1)
        self.goto(randabs(ptg.terminal.width() // 2, 3), randabs(ptg.terminal.height() // 2, 3))

    on_placed = new_round

    def update(self):
        for collidee in self.bounce((pad1, pad2, ptg.viewport)):
            if collidee is ptg.viewport.left:
                score2.increment(1)
                self.new_round()
            elif collidee is ptg.viewport.right:
                score1.increment(1)
                self.new_round()

with ptg.Game(fps=30) as game:
    pad_string = ("*\n" * (ptg.terminal.height() // 2)).rstrip("\n") # remove last redundant \n

    pad1 = ptg.Object(pad_string).place((2, ptg.terminal.height() // 2))
    pad2 = ptg.Object(pad_string).place((ptg.terminal.width() - 2, ptg.terminal.height() // 2))

    mid = ptg.terminal.width() // 2

    score_middle = ptg.FText(":").place((mid, 0))
    score1 = ptg.Counter(0) \
        .apply_style(align_horizontal = ptg.Dir.right) \
        .place((mid - 2, 0))
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

        pad1.bound_on_screen()
        pad2.bound_on_screen()

        game.update()
        game.render()
        game.tick()
