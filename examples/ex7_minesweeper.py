import pytermgame as ptg

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
    
    def reveal(self): # recursive
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

    # 1. Select board size

    column = ptg.ui.Column().wrap(
        ptg.Text("Up/down arrow to select board size, space to confirm"),
        menu := ptg.ui.SelectionMenu().wrap(
            ptg.Text("5x5"),
            ptg.Text("6x6"),
            ptg.Text("7x7"),
        )
    ).place((2, 2))
    
    for event in game.event_loop():
        if menu.process(event):
            pass
        elif event.is_key("space"):
            board_size = menu.selected_index + 5
            game.break_loop()
    
    game.new_scene()
    
    # 2. Generate initial board

    mines_left = board_size

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
        cols = board_size, rows = board_size,
        children_factory = lambda x, y: Cell(x, y)
    ).place((2, 4))

    # Initial selection
    for event in game.event_loop():
        if tmap.process(event):
            pass
        elif event.is_key("space"):
            initial = tmap.selected
            game.break_loop()

    # 3. Generate mines based on initial selection

    possible_mines = list(filter(lambda cell: abs(cell.col - initial.col) + abs(cell.row - initial.row) > 2, tmap.get_children()))

    for mine in random.sample(possible_mines, mines_left):
        mine.is_mine = True
        Cell.real_unmarked_mines += 1

        for adjacent in tmap.get_adjacent(mine.col, mine.row):
            adjacent.n += 1
    
    initial.click()

    # 4. Main game loop

    for event in game.event_loop():
        if tmap.process(event):
            pass
        elif event.is_key("space"):
            tmap.selected.click()
        elif event.is_key("f"):
            selected = tmap.selected
            if selected.revealed: # cell is revealed
                pass
            elif selected.marked: # cell is marked as a mine
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
    