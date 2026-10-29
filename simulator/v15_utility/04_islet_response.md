# A spell resolves before the waiting Islet draw

Forced conserved setup; actual sources; synthetic response explicitly marked where used.

The Islet draw ability paid its source and mana costs. Brainstorm was cast in response, completing its draw and put-back choices before the Islet ability resolved and drew its card.

```text
FORCED DIAGNOSTIC: declared actual card/source layout; not a natural opening.
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #487; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Fiery Islet #489; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #483 -> (0, 1, 0)
    STACK +1 [activated] P0: Fiery Islet: fiery_islet_draw.
    MANA P0: Island #485 -> (0, 1, 0)
  P0 (magnus) casts Brainstorm [instant] for 1; mana=1.
    STACK +2 [spell] P0: Brainstorm.
    CHOICE brainstorm_put_back P0: ['Cyclonic Rift', 'Fellwar Stone']; {}.
```
