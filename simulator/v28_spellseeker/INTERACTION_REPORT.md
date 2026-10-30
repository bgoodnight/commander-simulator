# Wizardcycling to Spellseeker to Consider

Forced fixture with actual land-source payments. Wizardcycling discarded Step Through and found Spellseeker. Its enter-the-battlefield ability found Consider, which was then cast and triggered Young Pyromancer. Cycling and casting the creature did not themselves trigger Pyromancer.

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
    LAND ENTERS P0: Mountain #501; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #483 -> (0, 1, 0)
    MANA P0: Mountain #497 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=0.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #485 -> (0, 1, 0)
    MANA P0: Island #487 -> (0, 1, 0)
    STACK +2 [activated] P0: Step Through: wizardcycling.
    WIZARDCYCLING P0: revealed Spellseeker, put into hand, then shuffled.
    MANA P0: Island #489 -> (0, 1, 0)
    MANA P0: Island #491 -> (0, 1, 0)
    MANA P0: Island #493 -> (0, 1, 0)
  P0 (magnus) casts Spellseeker [creature] for 3; mana=0.
    STACK +3 [spell] P0: Spellseeker.
    STACK +4 [triggered] P0: Spellseeker: spellseeker_search.
    SPELLSEEKER P0: revealed Consider, put into hand, then shuffled.
    MANA P0: Island #495 -> (0, 1, 0)
  P0 (magnus) casts Consider [instant] for 1; mana=0.
    STACK +5 [spell] P0: Consider.
    STACK +6 [triggered] P0: Young Pyromancer: create_token.
    CONSIDER P0: surveil card #66, move to graveyard=False; draw one.
```
