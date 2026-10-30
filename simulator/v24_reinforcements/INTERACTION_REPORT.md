# Magnus, Young Pyromancer and Ral’s Reinforcements

Forced fixture using actual lands. Casting Ral’s Reinforcements triggered Young Pyromancer and then created two blue/red Elemental tokens. With Magnus, the resulting three creature tokens reduced Capsize with buyback from 4UU to 1UU. Capsize produced another Pyromancer trigger and returned to hand.

```text
    LAND ENTERS P0: Island #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #473; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #475; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #477; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #479; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #481; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #487; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #489; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #491; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #493; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #495; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #469 -> (0, 1, 0)
    MANA P0: Mountain #487 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #471 -> (0, 1, 0)
    MANA P0: Island #473 -> (0, 1, 0)
    MANA P0: Island #475 -> (0, 1, 0)
    MANA P0: Island #477 -> (0, 1, 0)
    MANA P0: Mountain #489 -> (0, 0, 1)
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    STACK +2 [spell] P0: Magnus the Red.
    Magnus the Red enters battlefield (4/5).
    MANA P0: Island #479 -> (0, 1, 0)
    MANA P0: Mountain #491 -> (0, 0, 1)
  P0 (magnus) casts Ral's Reinforcements [sorcery] for 2; mana=0.
    STACK +3 [spell] P0: Ral's Reinforcements.
    STACK +4 [triggered] P0: Young Pyromancer: create_token.
    REINFORCEMENTS P0: two blue/red Elementals created.
    MANA P0: Island #481 -> (0, 1, 0)
    MANA P0: Island #483 -> (0, 1, 0)
    MANA P0: Island #485 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 3; mana=0.
    STACK +5 [spell] P0: Capsize.
    STACK +6 [triggered] P0: Young Pyromancer: create_token.
    Capsize returns fixture target to its owner's hand.
    Buyback paid: Capsize returns to hand after successful resolution.
```
