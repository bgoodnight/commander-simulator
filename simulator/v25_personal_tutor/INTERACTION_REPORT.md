# Personal Tutor into Ral’s Reinforcements

Forced setup with actual land payments. Personal Tutor found the sorcery and triggered Young Pyromancer. A subsequent declared draw and cast of Ral’s Reinforcements triggered Pyromancer again and created two blue/red Elementals: four Elemental tokens total.

```text
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #487; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #489; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #491; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #483 -> (0, 1, 0)
    MANA P0: Mountain #489 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #485 -> (0, 1, 0)
  P0 (magnus) casts Personal Tutor [sorcery] for 1; mana=0.
    STACK +2 [spell] P0: Personal Tutor.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    PERSONAL TUTOR P0: revealed Ral's Reinforcements; shuffled, then placed on top.
    MANA P0: Island #487 -> (0, 1, 0)
    MANA P0: Mountain #491 -> (0, 0, 1)
  P0 (magnus) casts Ral's Reinforcements [sorcery] for 2; mana=0.
    STACK +4 [spell] P0: Ral's Reinforcements.
    STACK +5 [triggered] P0: Young Pyromancer: create_token.
    REINFORCEMENTS P0: two blue/red Elementals created.
```
