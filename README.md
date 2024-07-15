# pytermgame

You've seen frameworks for making terminal apps (`textual`, `pytermgraphics`, `asciimatics` etc.), but how about a framework for games ... like `pygame` but in the terminal?

## Installation
Install from pip

```
pip install pytermgame
```

Or, install with the latest updates (may be unstable)

```
git clone https://github.com/tovicheung/pytermgame
cd pytermgame
pip install .
```

## Features
- pygame-inspired api structure
- customizable terminal behaviour (alternate screen, cursor visibility)
- optimized rendering: game calculates the minimum number of objects to re-render **(it takes care of overlapping sprites too!)**
- includes an integrated debugger
- cross-platform key event reading

> [!NOTE]
> This is not a full-fledged game engine, but more of a proof of concept of terminal-based game engines.

## Tested on
- Windows 10 & 11
- WSL Ubuntu 22.04

Unfortunately i am too broke to afford a mac

## Examples
Examples are included in the repo root:
- `jet_and_ball.py`
- `cookie_clicker.py`
- `pong.py`

Playing instructions are included in the examples.

## Future plans
- better ANSI api
- grayscale option
- cross-platform mouse support
- more examples
