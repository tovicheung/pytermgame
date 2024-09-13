# pytermgame

You've seen frameworks for making terminal apps (`textual`, `pytermgraphics`, `asciimatics` etc.), but how about a framework for games ... like `pygame` but in the terminal?

Supports Python 3.10 or above

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
- supports scrolling
- extensible sprite class
- collision engine with sub-tick motion prediction
- optimized rendering: game calculates the minimum number of objects to erase and re-render **(it takes care of overlapping sprites too!)**
- cross-platform key event reading
- includes an integrated debugger and an external profiler
- (**New**) basic composite UI support: `ptg.ui`

> [!NOTE]
> This is not a full-fledged game engine, but more of an experiment to create terminal games

## Tested on
- Windows 10 & 11
- WSL Ubuntu 22.04

Unfortunately i am too broke to afford a mac

## Examples
Examples are included in `examples/`.

Playing instructions are included in the respective files.

## Demo

https://github.com/user-attachments/assets/202c4f01-b9ec-4aac-bbbc-0cfa07369a2d

https://github.com/tovicheung/pytermgame/assets/demo_breakout.mp4

Atari breakout gameplay (example 4)

## Future plans
check out `TODO.md`
