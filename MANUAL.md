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

Sprites become zombies after `.kill()` is called. Zombies:
* cannot be collided with
* frees as much references as possible

## Scenes

A `Scene` is a part of a game that can be attached by sprites. One and only one scene must be active at all times during a game.

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

# UI in pytermgame

An easy-to-use and intuitive API for creating flexible UI using pytermgame is in the making. Check out the `pytermgame.ui` submodule.

## Interop with the base sprite model

Parent-child relationships have been introduced to all sprites via the `._parent` private attribute.
* If a child has a placed parent, it will call `.update_surf()` on the parent everytime the child's surf is changed (in `.set_surf()`).
* A child will inherit style options that it hasn't specified from its parent.

Note: this would not affect games that do not use UI constructs.

## Container

A container extends its child's dimensions or add additional details around it. A container can have zero or one child. A container's inner dimensions are the dimensions of the child.

When a container has no child, its inner dimensions are 0x0.

Example: definition of Padding
```python
class Padding(Container[_S]):
    def __init__(self, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0, child: _S | None = None):
        # optional child argument at last
        super().__init__(child)
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
    
    # -- alternative constructors omitted --
    
    # define child offset (no offset if undefined)
    def get_child_offset(self) -> Coords:
        return Coords(self.left, self.top)
    
    # a Container must define this
    def new_surf_factory(self) -> Surface:
        # do not use .child.width and .child.height directly
        inner_width, inner_height = self.get_inner_dimensions()

        width = inner_width + self.left + self.right
        height = inner_height + self.top + self.bottom

        # create surface, often blank
        return Surface.blank(width, height)
```

## Collection

A collection defines how its children are arranged.

Example: definition of Column
```python
class Column(Collection):
    # a Collection must define this
    def new_surf_factory(self):
        width = height = 0

        for child in self.get_children():
            # helper function provided in ptg.ui
            place_or_set_coords(child, self._coords.dy(height))
            height += child.height
            width = max(width, child.width)
        
        return Surface.phantom(width, height)
```
