# Reiterate copies Step Through

Forced fixture with actual land-source payments. Reiterate copied Step Through and changed both targets. The copy returned the second pair, and the original returned the first. Young Pyromancer triggered for the two cast spells, not the copy.

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
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Mountain #469 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #457 -> (0, 1, 0)
    MANA P0: Island #459 -> (0, 1, 0)
    MANA P0: Island #461 -> (0, 1, 0)
    MANA P0: Island #463 -> (0, 1, 0)
    MANA P0: Island #465 -> (0, 1, 0)
  P0 (magnus) casts Step Through [sorcery] for 5; mana=0.
    STACK +2 [spell] P0: Step Through.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    MANA P0: Island #467 -> (0, 1, 0)
    MANA P0: Mountain #471 -> (0, 0, 1)
    MANA P0: Mountain #473 -> (0, 0, 1)
  P0 (magnus) casts Reiterate [instant] for 3; mana=0.
    STACK +4 [spell] P0: Reiterate.
    STACK +5 [triggered] P0: Young Pyromancer: create_token.
    STACK +6 [spell] P0: Step Through.
    COPY P0: Step Through copied onto stack (not cast).
```
