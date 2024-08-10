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

    ball_initial_coords = (ptg.terminal.width() // 2 + random.randint(-5, 5), ptg.terminal.height() // 2)

    debugger.field("termsize", (ptg.terminal.width(), ptg.terminal.height()))
    debugger.field("ball_initial_coords", ball_initial_coords)

    ball = Ball().place(ball_initial_coords)
    
    pad = ptg.Object("#" * 20) \
        .place((ptg.terminal.width() // 2, ptg.terminal.height() - 3)) \
        .apply_style(fg = ptg.Color.cyan)

    # Generate tiles

    for y in range(3):
        for x in range(y * 3 % Tile.surf.width - Tile.surf.width + 1, ptg.terminal.width(), Tile.surf.width):
            Tile().place((x, y)).apply_style(fg = ptg.Color(y + 1))
    
    # Setup win/lose scenes

    with ptg.Scene() as game_over_scene:
        ptg.Text("Game over - Press space to exit").place((0, ptg.terminal.height() // 2))

    with ptg.Scene() as you_won_scene:
        ptg.Text("You won - Press space to exit").place((0, ptg.terminal.height() // 2))

    # Game loop

    while game.loop():
        for event in ptg.event.get():
            if event.is_key(ptg.key.LEFT):
                pad.move(-6, 0)
            if event.is_key(ptg.key.RIGHT):
                pad.move(6, 0)

        # If you want to cheat:
        # pad.set_x(ball.x - pad.width // 2)

        pad.bound_on_screen()
        game.update()
        game.render()
        game.tick()

    if len(Tile.group):
        game.set_scene(game_over_scene)
    else:
        game.set_scene(you_won_scene)

    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
