# Passage costs are paid before responses; early basic stays tapped

Forced conserved setup; real deck cards and source payments.

Playing Passage did not fetch. Activating it tapped/sacrificed it before anyone received priority; the ability then resolved without its source. The first fetched Island entered tapped and provided no immediate mana. After the next declared own-turn untap it paid for Ponder.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Fabled Passage #497; tapped=False; life_paid=0; cause=land_play.
    STACK +1 [activated] P0: Fabled Passage: fabled_passage_fetch.
    LAND ENTERS P0: Island #499; tapped=True; life_paid=0; cause=basic_fetch.
    BASIC FETCH P0: source #497; fetched #499; lands=1; untapped=False; shuffled.
DIAGNOSTIC NEXT OWN TURN: actual sources untapped; no extra land drop used by fetch.
    MANA P0: Island #499 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=0.
    STACK +2 [spell] P0: Ponder.
    CHOICE ponder_order P0: ['Riptide Laboratory', 'Training Center', 'Baral, Chief of Compliance']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
```
