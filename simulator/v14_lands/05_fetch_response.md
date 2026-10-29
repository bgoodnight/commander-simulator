# A response changes the resolution-time untap threshold

Forced conserved setup; real deck cards and source payments.

Passage began as the fourth land and was sacrificed as a cost. With its ability waiting, source-paid Capsize bounced another Island. The fetched basic still arrived, but the resulting three-land battlefield failed the untap condition, so it stayed tapped.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Fabled Passage #461; tapped=False; life_paid=0; cause=land_play.
    STACK +1 [activated] P0: Fabled Passage: fabled_passage_fetch.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Island #457 -> (0, 1, 0)
    MANA P0: Island #459 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 3; mana=0.
    STACK +2 [spell] P0: Capsize.
    Capsize returns Island to its owner's hand.
    LAND ENTERS P0: Island #467; tapped=True; life_paid=0; cause=basic_fetch.
    BASIC FETCH P0: source #461; fetched #467; lands=3; untapped=False; shuffled.
```
