"""
pytermgame example: atari breakout

Controls:
    left/right arrow keys -> move pad

Goal:
    break blocks using ball

This example demonstrates:
- how to use the debugger
- how to use KinematicSprite
"""

import pytermgame as ptg
import random

class Ball(ptg.KinematicSprite):
    surf = ptg.Surface("O")

    def on_placed(self):
        self.vx = 1
        self.vy = -1

    def update(self):
        # Bouncing mechanism
        for collidee in self.bounce((Tile.group, pad, ptg.screen)):
            if isinstance(collidee, Tile):
                collidee.kill()
            elif collidee is ptg.ScreenEdge.bottom:
                game.break_loop()
        
        if len(Tile.group) == 0:
            game.break_loop()

        debugger \
            .field("vx", self.vx) \
            .field("vy", self.vy) \
            .field("x", self.x) \
            .field("y", self.y)

class Tile(ptg.Sprite):
    surf = ptg.Surface("[-----]")
    group = ptg.Group() # automatically adds Tile sprites into this group

with ptg.Game(fps=30) as game:

    # Setup debugger

    debugger = ptg.Debugger() \
                .place((0, ptg.terminal.height() - 1)) \
                .hook(game) \
                .block_on_key("d")

    ball = Ball().place((ptg.terminal.width() // 2 + random.randint(-5, 5), ptg.terminal.height() // 2))
    
    pad = ptg.Object("#" * 20).place((ptg.terminal.width() // 2, ptg.terminal.height() - 3))

    # Generate tiles

    for y in range(3):
        for x in range(y * 2 % Tile.surf.width, ptg.terminal.width(), Tile.surf.width):
            Tile().place((x, y))
    
    # Setup win/lose scenes

    with ptg.Scene() as game_over:
        ptg.Text("Game over - Press space to exit").place((0, ptg.terminal.height() // 2))

    with ptg.Scene() as you_won:
        ptg.Text("You won - Press space to exit").place((0, ptg.terminal.height() // 2))

    # Game loop

    while game.loop():
        for event in ptg.event.get():
            if event.is_key(ptg.key.LEFT):
                pad.move(-6, 0)
            if event.is_key(ptg.key.RIGHT):
                pad.move(6, 0)

        # If you want to cheat:
        pad.set_x(ball.x - pad.width // 2)

        pad.bound_on_screen()
        game.update()
        game.render()
        game.tick()

    if len(Tile.group):
        game.set_scene(game_over)
    else:
        game.set_scene(you_won)

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
