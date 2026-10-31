# Reiterate copies Consider

Forced fixture, paid with actual land sources. Consider and Reiterate are cast, each triggering Young Pyromancer; the copy is not cast. Archmage Emeritus triggers on both casts and the copy. Reiterate returns to hand after buyback and both Consider instances resolve.

```text
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #461; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #463; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #465; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #467; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #473; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #475; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #477; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #479; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Mountain #469 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #457 -> (0, 1, 0)
    MANA P0: Island #459 -> (0, 1, 0)
    MANA P0: Island #461 -> (0, 1, 0)
    MANA P0: Island #463 -> (0, 1, 0)
  P0 (magnus) casts Archmage Emeritus [creature] for 4; mana=0.
    STACK +2 [spell] P0: Archmage Emeritus.
    Archmage Emeritus enters battlefield (2/2).
    MANA P0: Island #465 -> (0, 1, 0)
  P0 (magnus) casts Consider [instant] for 1; mana=0.
    STACK +3 [spell] P0: Consider.
    STACK +4 [triggered] P0: Young Pyromancer: create_token.
    STACK +5 [triggered] P0: Archmage Emeritus: draw.
    MANA P0: Island #467 -> (0, 1, 0)
    MANA P0: Mountain #471 -> (0, 0, 1)
    MANA P0: Mountain #473 -> (0, 0, 1)
    MANA P0: Mountain #475 -> (0, 0, 1)
    MANA P0: Mountain #477 -> (0, 0, 1)
    MANA P0: Mountain #479 -> (0, 0, 1)
  P0 (magnus) casts Reiterate [instant] for 6; mana=0.
    STACK +6 [spell] P0: Reiterate.
    STACK +7 [triggered] P0: Young Pyromancer: create_token.
    STACK +8 [triggered] P0: Archmage Emeritus: draw.
    STACK +9 [spell] P0: Consider.
    COPY P0: Consider copied onto stack (not cast).
    Reiterate buyback returns to hand.
    STACK +10 [triggered] P0: Archmage Emeritus: draw.
    CONSIDER P0: surveil card #430, move to graveyard=False; draw one.
    CONSIDER P0: surveil card #92, move to graveyard=False; draw one.
```
