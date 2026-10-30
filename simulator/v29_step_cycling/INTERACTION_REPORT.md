# Step Through interaction

Forced fixture using real land-source payments. Casting Step Through triggered Young Pyromancer. A synthetic response removed one target; the remaining legal creature returned. The spell resolved rather than fizzling.

```text
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #487; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #489; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #491; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #493; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #495; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #497; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #499; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #483 -> (0, 1, 0)
    MANA P0: Mountain #497 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #485 -> (0, 1, 0)
    MANA P0: Island #487 -> (0, 1, 0)
    MANA P0: Island #489 -> (0, 1, 0)
    MANA P0: Island #491 -> (0, 1, 0)
    MANA P0: Island #493 -> (0, 1, 0)
  P0 (magnus) casts Step Through [sorcery] for 5; mana=0.
    STACK +2 [spell] P0: Step Through.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
SYNTHETIC RESPONSE: remove the first target before resolution.
```
