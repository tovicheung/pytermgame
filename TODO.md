Future updates

- none planned yet

Design choices made

- Stricter control over sprite placement; 3 ways:
    1. (**current**) Check if placed in methods
    2. Split into two classes: `ArbitrarySprite` and `PlacedSprite`
        * seems to be confusing
    3. Add `coords` and `scene` arguments to `Sprite.__init__`
        * subclasses must also include them and call super() if they want to customize the constructor

Failed ideas

- Use a 2D matrix to track sprite occupancy of each coordinate (`[future: collision]`)
    * **Tested:** no significant improvement
    * maybe make this an optional feature?
    * Benefits:
        * efficient collision detection
        * shape-wise collision detection instead of hitbox-wise
    * Drawbacks:
        * huge changes in api
