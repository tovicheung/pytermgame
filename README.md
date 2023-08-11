# pytermgame

You've seen frameworks for making terminal apps (`textual`, `pytermgraphics`, `asciimatics` etc.), but how about a framework for games ... like `pygame`?

## Installation
`pip install pytermgame`

## Features
- pygame-inspired structure
- customizable terminal behaviour (alternate screen, cursor visibility)
- optimized rendering: game figures out which sprites requires erase and re-render **(it takes care of overlapping sprites too!)**
- provides both tick-based and thread-based event systems
- cross-platform support for reading and identifying keys

## Examples
Examples are included in the repo root (there's 2 currently)

Instructions are in the file of the example (docstrings)

## Future plans
- cross-platform support for more keys
- simulated scrolling (extended axis)
- a "Scene" or "Screen" system
- use integer IDs to reference sprites (for performance?)
- support color using ANSI (Char class?)
    - option to remain black and white (less memory)
- cross-platform mouse support
- more examples
