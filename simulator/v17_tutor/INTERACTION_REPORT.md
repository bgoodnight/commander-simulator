# Mystical Tutor and Young Pyromancer

Forced fixture with actual land-source payments. Casting Mystical Tutor triggered Young Pyromancer, creating an Elemental before the tutor resolved. The tutor then revealed Ponder, shuffled, and put it on top.

```text
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #461; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Mountain #459 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=2.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #457 -> (0, 1, 0)
  P0 (magnus) casts Mystical Tutor [instant] for 1; mana=1.
    STACK +2 [spell] P0: Mystical Tutor.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    MYSTICAL TUTOR P0: revealed Ponder; shuffled, then placed on top.
```
