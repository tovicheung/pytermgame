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
    style = ptg.Style(inverted = True)

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

            if self.is_colliding(ptg.viewport.left):
                self.kill()
                score_counter.decrement()

class Bullet(ptg.KinematicSprite):
    surf = ptg.Surface("------")
    style = ptg.Style(fg = "yellow")

    def __init__(self):
        super().__init__()
        self.place((ship.x + ship.width + 1, ship.y + 1))
        self.vx = 6

    def update(self):
        collidees = self.move_until_collision((Asteroid.group, ptg.viewport.right))
        if collidees:
            self.kill()
            for sprite in collidees:
                if isinstance(sprite, Asteroid):
                    sprite.kill()
                    score_counter.increment()

with ptg.Game(fps = 30) as game:

    ship = ptg.Object([
        "\\\\",
        "===>",
        "//",
    ]).place((0, 0))
    
    power = ptg.Gauge(20, 10, 20).place((0, ptg.terminal.height() - 1))

    score_text = ptg.Text("Score:").place((14, ptg.terminal.height() - 1))
    score_counter = ptg.Counter(0).place((21, ptg.terminal.height() - 1))
    
    # Using normal timers:
    # SPAWN = ptg.event.USEREVENT + 1
    # GAIN_POWER = ptg.event.USEREVENT + 2
    # ptg.clock.add_timer(SPAWN, secs = 1)
    # ptg.clock.add_timer(GAIN_POWER, secs = 0.5)
    
    # Using callback timers:
    ptg.clock.add_callback_timer(
        callback = Asteroid, # same as lambda: Asteroid()
        secs = 1,
    )
    ptg.clock.add_callback_timer(
        callback = lambda: power.update_value(min(power.full, power.value + 1)),
        secs = 0.5,
    )
    
    while game.loop():
        for event in ptg.event.get():
            if event.is_key("up"):
                ship.move(0, -1)
            elif event.is_key("down"):
                ship.move(0, 1)
            elif event.is_key("left"):
                ship.move(-1, 0)
            elif event.is_key("right"):
                ship.move(1, 0)
            elif event.is_key("space"):
                if power.value > 0:
                    Bullet()
                    power.update_value(power.value - 1)

                    # flash effect
                    ship.apply_style(bg = "cyan")
                    ptg.clock.add_callback_timer(
                        lambda: ship.apply_style(bg = "default"),
                        secs = 0.1, loops = 1
                    )
            # These event handlers are needed if we use normal timers
            # elif event.is_type(SPAWN):
            #     Asteroid()
            # elif event.is_type(GAIN_POWER):
            #     if power.value < power.full:
            #         power.update_value(power.value + 1)
        
        game.update()
        game.render()
        game.tick()
    
    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
