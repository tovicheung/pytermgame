import pytermgame as ptg

ptg.terminal.goto(ptg.terminal.width + 3, ptg.terminal.height + 3)
ptg.terminal.fwrite("A\n")
ptg.sleep(1)
ptg.terminal.goto(0, 0)