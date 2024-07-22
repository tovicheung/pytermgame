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
- scene-switching within a game, each with its own sprites
- extensible sprite class
- optimized rendering: game calculates the minimum number of objects to erase and re-render **(it takes care of overlapping sprites too!)**
- cross-platform key event reading
- includes an integrated debugger and an external profiler

> [!NOTE]
> This is not a full-fledged game engine, but more of an experiment to create terminal games

## Tested on
- Windows 10 & 11
- WSL Ubuntu 22.04

Unfortunately i am too broke to afford a mac

## Examples
Examples are included in the repo root:
- `ex1_jet_and_ball.py`
- `ex2_cookie_clicker.py`
- `ex3_pong.py`
- `ex4_breakout.py`
- `ex5_space_shooter.py`

Playing instructions are included in the examples.

## Future plans
- cross-platform mouse support
- both hitbox and shape-based collision systems
