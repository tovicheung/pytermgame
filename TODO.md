Improvements / Ideas

- Stricter control over sprite placement
    1. Check if placed in methods (current)
    2. Split into two classes: `ArbitrarySprite` and `PlacedSprite`
        * seems to be confusing
    3. Add `coords` and `scene` arguments to `Sprite.__init__`
        * subclasses must also include them and call super() if they want to customize the constructor

- Create a game-wise entry specifically for sprites.Value s and use the currently unused descriptor
    * Benefits:
        * No need to call `.set()`, just set the value
        * No namespace cluttering
    * Drawbacks:
        * Does not play well with type-checking

- Create example for scrolling

- Provide simple interface for abstract positioning
    * top of screen, horizontally middle, etc.
    * planned: `ptg.layout`
