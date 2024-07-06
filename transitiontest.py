import pytermgame as ptg

with ptg.Game(alternate_screen=False, fps=30, clear_first=True) as game:
    ptg.Text("hello world").place((5, 5))
    game.render()
    with ptg.Scene() as scene2:
        ptg.Text("bye world").place((50, 8))
    ptg.event.wait_until(ptg.event.KEYEVENT)

    game.switch_scene(scene2, ptg.transition.wipe, 60)

    ptg.event.wait_until(ptg.event.KEYEVENT)
