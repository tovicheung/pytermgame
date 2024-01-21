Improvements
- Remove coordinates from `Sprite.__init__`
    - Use private variable to keep track if placed
    - Or, split into two classes: `ArbitrarySprite` and `PlacedSprite`

Bugs
- When text shrinks, overflow is not erased
