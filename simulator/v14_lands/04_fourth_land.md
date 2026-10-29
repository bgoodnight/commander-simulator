# Fourth fetched land enters tapped, then untaps and pays for a spell

Forced conserved setup; real deck cards and source payments.

Three actual sources paid for Adaptation and were tapped. Passage was played and sacrificed. Its fetched Island entered tapped, then untapped because the resulting battlefield had four lands. That exact new source paid for Ponder immediately; Passage itself was not counted.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #473; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #469 -> (0, 1, 0)
    MANA P0: Island #471 -> (0, 1, 0)
    MANA P0: Mountain #473 -> (0, 0, 1)
  P0 (magnus) casts Arcane Adaptation [enchantment] for 3; mana=0.
    STACK +1 [spell] P0: Arcane Adaptation.
    Arcane Adaptation enters: Wizard chosen; additive types apply in all declared zones.
    LAND ENTERS P0: Fabled Passage #478; tapped=False; life_paid=0; cause=land_play.
    STACK +2 [activated] P0: Fabled Passage: fabled_passage_fetch.
    LAND ENTERS P0: Island #480; tapped=True; life_paid=0; cause=basic_fetch.
    BASIC FETCH P0: source #478; fetched #480; lands=4; untapped=True; shuffled.
    MANA P0: Island #480 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=0.
    STACK +3 [spell] P0: Ponder.
    CHOICE ponder_order P0: ['Sulfur Falls', 'Searing Touch', 'Mutalith Vortex Beast']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': True}.
```
