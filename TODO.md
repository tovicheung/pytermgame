Future updates

> [!NOTE]
> Some planned updates have a tag next to them, for example `[future: collision]`.
> This means there is already some progress on it and any relevant code are marked by the same tag using comments.
> You can search for that tag to view the relevant code.

- Use a 2D matrix to track sprite occupancy of each coordinate (`[future: collision]`)
    * **Tested:** no significant improvement
    * maybe make this an optional feature?
    * Benefits:
        * efficient collision detection
        * shape-wise collision detection instead of hitbox-wise
    * Drawbacks:
        * huge changes in api

- Provide simple interface for positioning (`[future: layout]`)
    * top of screen, horizontally middle, etc

- Game state?

Design choices made

- Stricter control over sprite placement; 3 ways:
    1. (**current**) Check if placed in methods
    2. Split into two classes: `ArbitrarySprite` and `PlacedSprite`
        * seems to be confusing
    3. Add `coords` and `scene` arguments to `Sprite.__init__`
        * subclasses must also include them and call super() if they want to customize the constructor
