# Understanding pytermgame

## Sprites

`Sprite`s are the building blocks of a game. They have 3 functional states:

#### 1. Abstract state

Sprites are initially abstract when their constructors are called.

```python
# these sprites are abstract
myball = Ball()
mysquare = Square(side_length=5)
```

They are not attached to any scenes or games. This means they can be created dynamically outside of games.

#### 2. Placed state
Sprites are placed after calling `.place()`

```python
# these sprites are placed
myball = Ball().place((5, 5))
mysquare = Square(side_length=5).place((1, 9))
```
After a sprite is being placed, it:
* has a surface
* is attached to a scene
* has XYZ coordinates on the scene
* calls `.on_placed()`, which can be overriden by subclasses freely
* unlocks methods such as `.move()`
* can be killed via `.kill()`

They become a "concrete" sprite that can be rendered and interacted with.

#### 3. Zombie state

Sprites become zombies after `.kill()` is called. Zombies are truly destroyed all at once by the game (usually per tick).

## Sprite groups and lists

A `Group` is essentially a set of sprites. Sprites are aware of their presence in groups.

Groups can perform sprite operations on all its sprites:
* `Group.update()`: calls `.update()` on all its sprites
* `Group.render()`: calls `.render()` on all its sprites and only flushes stdout at the end

A `SpriteList` is an ordered list of sprites. Otherwise it is the same as a group.

## Scenes

A `Scene` is a part of a game that can be attached by sprites. One and only one scene must be active at all times during a game.

A scene is implemented as a SpriteList, with its sprites ordered by z-coordinate.

## How to attach a sprite to a scene

#### Method 1: implicit scene attachment
```python
myball = Ball().place((5, 5))
```
The sprite will be placed to the active scene of the active game by default.

#### Method 2: explicit scene attachment
```python
myball = Ball().place((5, 5), scene=myscene)
```
Attach sprite to the given scene regardless of context.

#### Method 3: scene context
```python
with ptg.Scene() as myscene:
    myball = Ball().place((5, 5))
```
Sprites will be attached to `myscene`. This method can be used even when another scene is active.

## How to define a surface for a subclass of `Sprite`

#### Method 1: `.surf` class attribute
```python
class Smile(ptg.Sprite):
    surf = ptg.Surface("^_^")
```
All instances will have the same surface.

#### Method 2: define in `__init__`
```python
class Smile(ptg.Sprite):
    def __init__(self, mouth_length: int):
        super().__init__()
        self.surf = ptg.Surface("^" + "_" * mouth_length + "^")
```
Should be used when the surface is fixed for each sprite.

#### Method 3: use a factory
```python
class Line(ptg.Sprite):
    def __init__(self, length: int):
        super().__init__()
        self.length = length
    
    def new_surf_factory(self):
        return Surface("-" * self.length)
    
    def resize(self, new_length: int):
        self.length = new_length
        self.update_surf()
        # .update_surf() is provided to
        # 1) get a new surf from factory
        # 2) calls .set_surf()
```
Should be used when the surface depends on each sprite's attributes and may change over time.

`.update_surf()` is automatically called in `.place()` to generate the initial surface.


