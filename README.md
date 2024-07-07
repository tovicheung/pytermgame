# pytermgame

You've seen frameworks for making terminal apps (`textual`, `pytermgraphics`, `asciimatics` etc.), but how about a framework for games ... like `pygame` but in the terminal?

## Installation
`pip install pytermgame`

## Features
- pygame-inspired structure
- customizable terminal behaviour (alternate screen, cursor visibility)
- optimized rendering: game figures out which sprites requires erase and re-render **(it takes care of overlapping sprites too!)**
- provides both tick-based and thread-based event systems
- cross-platform support for reading and identifying keys

## Tested on
- Windows 10
- Ubuntu (WSL) 22.04

Unfortunately i am too broke to afford a mac

## Examples
Examples are included in the repo root:
- `jet_and_ball.py`
- `cookie_clicker.py`
- `pong.py`

Playing instructions are included in the examples

## Future plans
- cross-platform support for more keys
- extended screen (scrolling, multiple scenes, etc.)
- better interface to ANSI colors
- grayscale option
- cross-platform mouse support
- more examples
