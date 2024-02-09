Improvements
- Stricter control over sprite placement
    1. Check if placed in methods (current)
    2. Split into two classes: `ArbitrarySprite` and `PlacedSprite`
    3. Add `coords` and `scene` arguments to `Sprite.__init__`
        * subclasses must also include them and call super() if they want to customize the constructor
