# Phyrexian Altar interaction

Forced fixture with real land-source payments: cast Altar and Young Pyromancer, then Ral’s Reinforcements creates two tokens and triggers Pyromancer for a third. After an explicitly forced tap of the lands, Altar sacrifices an Elemental for blue mana to cast Consider; Pyromancer then replaces the sacrificed token.

```text
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #461; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #463; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #465; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #467; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #473; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Island #457 -> (0, 1, 0)
    MANA P0: Island #459 -> (0, 1, 0)
  P0 (magnus) casts Phyrexian Altar [artifact] for 3; mana=0.
    STACK +1 [spell] P0: Phyrexian Altar.
    MANA P0: Island #461 -> (0, 1, 0)
    MANA P0: Mountain #465 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +2 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #463 -> (0, 1, 0)
    MANA P0: Mountain #467 -> (0, 0, 1)
  P0 (magnus) casts Ral's Reinforcements [sorcery] for 2; mana=0.
    STACK +3 [spell] P0: Ral's Reinforcements.
    STACK +4 [triggered] P0: Young Pyromancer: create_token.
    REINFORCEMENTS P0: two blue/red Elementals created.
    MANA P0: Phyrexian Altar #476 sacrifices Elemental #482 -> (0, 1, 0).
  P0 (magnus) casts Consider [instant] for 1; mana=0.
    STACK +5 [spell] P0: Consider.
    STACK +6 [triggered] P0: Young Pyromancer: create_token.
    CONSIDER P0: surveil card #432, move to graveyard=False; draw one.
```
