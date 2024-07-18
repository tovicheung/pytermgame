import pytermgame as ptg
import random

rocket_art = \
"""
\\\\
===>
//
""".strip("\n")

class Asteroid(ptg.Sprite):
    surf = ptg.Surface("####\n####\n####")
    group = ptg.Group()

    def on_placed(self):
        self.goto(ptg.terminal.width(), random.randint(0, ptg.terminal.height() - 1 - self.surf.height))

    def update(self):
        if not self.zombie:
            self.move(-0.5, 0)

            if self.is_colliding(ptg.ScreenEdge.left):
                self.kill()
                score_counter.decrement()

class Bullet(ptg.KinematicSprite):
    surf = ptg.Surface("--")

    def init(self):
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
    
    ptg.clock.set_interval(SPAWN, secs=1)
    ptg.clock.set_interval(GAIN_POWER, secs=0.5)

    rocket = ptg.Object(rocket_art).place((0, 0))
    power = ptg.Gauge(20, 10, 20).place((0, ptg.terminal.height() - 1))

    score_text = ptg.Text("Score:").place((14, ptg.terminal.height() - 1))
    score_counter = ptg.Counter(0).place((21, ptg.terminal.height() - 1))
    
    while game.loop():
        for event in ptg.event.get():
            if event.is_key(ptg.key.UP):
                rocket.move(0, -1)
            elif event.is_key(ptg.key.DOWN):
                rocket.move(0, 1)
            elif event.is_key(ptg.key.LEFT):
                rocket.move(-1, 0)
            elif event.is_key(ptg.key.RIGHT):
                rocket.move(1, 0)
            elif event.is_key(ptg.key.SPACE):
                if power.value > 0:
                    Bullet()
                    power.update_value(power.value - 1)
            elif event.is_type(SPAWN):
                Asteroid().place()
            elif event.is_type(GAIN_POWER):
                if power.value < power.full:
                    power.update_value(power.value + 1)
        
        game.update()
        game.render()
        game.tick()
    
    ptg.event.wait_until((ptg.event.KEYEVENT, ptg.key.SPACE))
