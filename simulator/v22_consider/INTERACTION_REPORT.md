# Mystical Tutor, Consider, and Young Pyromancer

Forced fixture with actual land payments: Mystical Tutor searched for Consider; the subsequent draw and cast of Consider produced a second Elemental. The default surveil choice kept the looked-at card on top, then drew it.

```text
    LAND ENTERS P0: Island #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #473; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #475; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #477; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #469 -> (0, 1, 0)
    MANA P0: Mountain #475 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #471 -> (0, 1, 0)
  P0 (magnus) casts Mystical Tutor [instant] for 1; mana=0.
    STACK +2 [spell] P0: Mystical Tutor.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    MYSTICAL TUTOR P0: revealed Consider; shuffled, then placed on top.
    MANA P0: Island #473 -> (0, 1, 0)
  P0 (magnus) casts Consider [instant] for 1; mana=0.
    STACK +4 [spell] P0: Consider.
    STACK +5 [triggered] P0: Young Pyromancer: create_token.
    CONSIDER P0: surveil card #50, move to graveyard=False; draw one.
```
