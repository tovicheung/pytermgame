# pytermgame

You've seen frameworks for making terminal apps (`textual`, `pytermgraphics`, `asciimatics`) ... but how about a framework for games ... like `pygame`?

Installation: `pip install pytermgame`

## Features
- pygame-inspired structure
- customizable terminal behaviour (alternate screen, cursor visibility)
- optimized rendering, game figures out which sprites requires erase and re-render **(it takes care of overlapping sprites too!)**
- cross-platform support for reading and identifying keys

## Examples
Currently there is one only: `jet_and_ball.py`

Use up and down arrows to control, just dodge the balls

The grey line is for alignment

### TODO:
- support for more keys
- simulated scrolling (extended axis)
- use integer IDs to reference sprites (for performance?)
- support color using ANSI (Char class?)
    - option to remain black and white (less memory)
- mouse support
- more examples
