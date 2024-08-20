import pytermgame as ptg
import random

class Ball(ptg.KinematicSprite):
    surf = ptg.Surface("O")
    group = ptg.Group()

    def on_placed(self):
        self.vx = random.choice((-3, 3))
        self.vy = random.choice((-1, 1))
    
    def update(self):
        self.bounce((ptg.screen, Ball.group))

try:
    with ptg.Game(fps=30, update_screen_size = "every_tick") as game:
        prof, disp = ptg.Profiler(game, sample_ticks=30).with_display()

        ptg.clock.add_interval(ptg.event.USEREVENT, ticks=10)

        # colored balls to verify collisions are happening
        # Ball().place((5, 5)).apply_style(fg = ptg.Color.red)
        # Ball().place((2, 2)).apply_style(fg = ptg.Color.green)
        while True:
            for event in ptg.event.get():
                if event.is_type(ptg.event.USEREVENT):
                    Ball().place((5, 5))

            game.update()
            game.render()
            game.tick()

            prof.tick().min_average_fps(15)
except ptg.profiler.ProfileException as exc:
    print(exc)
