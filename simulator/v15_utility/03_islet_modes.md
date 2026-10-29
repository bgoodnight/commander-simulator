# Fiery Islet pays life for mana, then later sacrifices to draw

Forced conserved setup; actual sources; synthetic response explicitly marked where used.

An actual Fiery Islet mana activation produced U and paid one life without damage. After a declared next-turn untap, a different land paid the one-mana draw-ability cost; Islet was tapped and sacrificed before the card was drawn.

```text
FORCED DIAGNOSTIC: declared actual card/source layout; not a natural opening.
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Fiery Islet #459; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Fiery Islet #459 -> (0, 1, 0)
DIAGNOSTIC NEXT OWN TURN: pool emptied and sources untapped.
    MANA P0: Island #455 -> (0, 1, 0)
    STACK +1 [activated] P0: Fiery Islet: fiery_islet_draw.
```
