import pytermgame as ptg
from pytermgame import _dev

import random

class Cell(ptg.Value):
    real_unmarked_mines = 0

    def __init__(self, col: int, row: int):
        super().__init__("?")
        self.col = col
        self.row = row
        self.is_mine = False
        self.n = 0
        self.revealed = False
        self.marked = False
    
    def reveal(self):
        if self.revealed:
            return
        self.revealed = True

        if self.is_mine:
            return
        if self.n > 0:
            self.update_value(self.n)
            return
        
        self.update_value(" ")
        
        for cell in tmap.get_adjacent(self.col, self.row):
            cell.reveal()
    
    def click(self):
        if self.is_mine:
            self.update_value("!")
            msg.update_value("Boom!")
            msg.apply_style(bg = ptg.Color.red)
            game.break_loop()
        else:
            self.reveal()

with ptg.Game() as game:
    mines_left = 6

    ptg.ui.Column().wrap(
        ptg.ui.Row().wrap(
            ptg.Border().wrap(
                mines_left_display := ptg.FText("{} mines left", mines_left)
            ),
            ptg.Border(child = ptg.Text("Arrow keys = move")),
            ptg.Border(child = ptg.Text("Space = reveal")),
            ptg.Border(child = ptg.Text("F = flag as mine")),
        ),
        msg := ptg.Value(""),
    ).place((0, 0))

    tmap = ptg.ui.TileMap.from_factory(
        cols = 6, rows = 6,
        children_factory = lambda x, y: Cell(x, y)
    ).place((2, 4))

    # Initial selection
    while True:
        game.render()

        event = ptg.event.wait_for_event()
        if tmap.process(event):
            pass
        elif event.is_key("space"):
            initial = tmap.selected
            break
    
    # not too close to initial
    possible_mines = list(filter(lambda cell: abs(cell.col - initial.col) + abs(cell.row - initial.row) > 2, tmap.get_children()))

    for mine in random.sample(possible_mines, mines_left):
        mine.is_mine = True
        Cell.real_unmarked_mines += 1

        for adjacent in tmap.get_adjacent(mine.col, mine.row):
            adjacent.n += 1
    
    initial.click()

    while game.loop():
        game.render()

        event = ptg.event.wait_for_event()
        if tmap.process(event):
            pass
        elif event.is_key("space"):
            tmap.selected.click()
        elif event.is_key("f"):
            selected = tmap.selected
            if selected.revealed:
                pass
            elif selected.marked:
                selected.marked = False
                selected.update_value("?")
                mines_left += 1
                mines_left_display.format(mines_left)

                if tmap.selected.is_mine:
                    Cell.real_unmarked_mines += 1
            else:
                selected.marked = True
                tmap.selected.update_value("F")
                mines_left -= 1
                mines_left_display.format(mines_left)

                if tmap.selected.is_mine:
                    Cell.real_unmarked_mines -= 1
        
        if Cell.real_unmarked_mines == 0:
            msg.update_value("You won!")
            msg.apply_style(bg = ptg.Color.green)
            game.break_loop()

    game.render() # last render
    ptg.event.wait_for_event()
    