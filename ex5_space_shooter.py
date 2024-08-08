"""
pytermgame example: space shooter

Controls:
    arrow keys -> move ship
    space -> fire bullets

Goal:
    destroy asteroids with bullets

Mechanics
    +1 point when asteroid is destroyed
    -1 point when asteroid hits left side
"""

import pytermgame as ptg
import random

class Asteroid(ptg.Sprite):
    group = ptg.Group()

    def __init__(self):
        super().__init__()
        self.update_surf()
        self.place((ptg.terminal.width(), random.randint(0, ptg.terminal.height() - 1 - self.surf.height)))
    
    def new_surf_factory(self) -> ptg.Surface:
        height = random.randint(1, 3)
        asteroid = ["".join(random.choice(" *@#$") for _ in range(random.randint(4, 7))) for _ in range(height)]
        return ptg.Surface(asteroid)

    def update(self):
        if not self.zombie:
            self.move(-0.5, 0)

            if self.is_colliding(ptg.ScreenEdge.left):
                self.kill()
                score_counter.decrement()

class Bullet(ptg.KinematicSprite):
    surf = ptg.Surface("----")

    def __init__(self):
        super().__init__()
        self.place((rocket.x + rocket.width + 1, rocket.y + 1))
        self.vx = 6

    def update(self):
        collidees = self.move_until_collision((Asteroid.group, ptg.ScreenEdge.right))
        if collidees:
            self.kill()
            for sprite in collidees:
                if isinstance(sprite, Asteroid):
                    sprite.kill()
                    score_counter.increment()

with ptg.Game(fps=30) as game:
    SPAWN = ptg.event.USEREVENT + 1
    GAIN_POWER = ptg.event.USEREVENT + 2
    
    ptg.clock.add_interval(SPAWN, secs=1)
    ptg.clock.add_interval(GAIN_POWER, secs=0.5)

    rocket = ptg.Object([
        "\\\\",
        "===>",
        "//",
    ]).place((0, 0))
    
    power = ptg.Gauge(20, 10, 20).place((0, ptg.terminal.height() - 1))

    score_text = ptg.Text("Score:").place((14, ptg.terminal.height() - 1))
    score_counter = ptg.Counter(0).place((21, ptg.terminal.height() - 1))
    
    while game.loop():
        for event in ptg.event.get():
            if event.is_key("up"):
                rocket.move(0, -1)
            elif event.is_key("down"):
                rocket.move(0, 1)
            elif event.is_key("left"):
                rocket.move(-1, 0)
            elif event.is_key("right"):
                rocket.move(1, 0)
            elif event.is_key("space"):
                if power.value > 0:
                    Bullet()
                    power.update_value(power.value - 1)
            elif event.is_type(SPAWN):
                Asteroid()
            elif event.is_type(GAIN_POWER):
                if power.value < power.full:
                    power.update_value(power.value + 1)
        
        game.update()
        game.render()
        game.tick()
    
    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
