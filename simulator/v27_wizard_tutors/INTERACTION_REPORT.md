# Fabricate and wizardcycling with Young Pyromancer

Forced setup with actual land payments. Fabricate found Phyrexian Altar and triggered Pyromancer. Step Through was then discarded and its wizardcycling ability found Spellseeker; cycling did not trigger Pyromancer because no spell was cast. Altar and Spellseeker effects are not yet implemented.

```text
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #461; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #463; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #465; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #467; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #469; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Mountain #465 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #457 -> (0, 1, 0)
    MANA P0: Island #459 -> (0, 1, 0)
    MANA P0: Island #461 -> (0, 1, 0)
  P0 (magnus) casts Fabricate [sorcery] for 3; mana=0.
    STACK +2 [spell] P0: Fabricate.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    FABRICATE P0: revealed Phyrexian Altar, put into hand, then shuffled.
    MANA P0: Island #463 -> (0, 1, 0)
    MANA P0: Mountain #467 -> (0, 0, 1)
    STACK +4 [activated] P0: Step Through: wizardcycling.
    WIZARDCYCLING P0: revealed Spellseeker, put into hand, then shuffled.
```
