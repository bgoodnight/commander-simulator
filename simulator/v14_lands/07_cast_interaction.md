# Land play and fetch do not trigger cast engines

Forced conserved setup; real deck cards and source payments.

Preordain made one Pyromancer Elemental. Playing and activating Passage made none. The fourth fetched Island untapped and paid for Ponder, which made exactly one additional Elemental through the ordinary cast trigger.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #487; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #483 -> (0, 1, 0)
    MANA P0: Mountain #487 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=1.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #485 -> (0, 1, 0)
  P0 (magnus) casts Preordain [sorcery] for 1; mana=0.
    STACK +2 [spell] P0: Preordain.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    CHOICE scry P0: ['Sorcerer Class', "An Offer You Can't Refuse"]; {'top': [459], 'bottom': [460]}.
    LAND ENTERS P0: Fabled Passage #497; tapped=False; life_paid=0; cause=land_play.
    STACK +4 [activated] P0: Fabled Passage: fabled_passage_fetch.
    LAND ENTERS P0: Island #499; tapped=True; life_paid=0; cause=basic_fetch.
    BASIC FETCH P0: source #497; fetched #499; lands=4; untapped=True; shuffled.
    MANA P0: Island #499 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=0.
    STACK +5 [spell] P0: Ponder.
    STACK +6 [triggered] P0: Young Pyromancer: create_token.
    CHOICE ponder_order P0: ['Impulse', 'Mountain', 'Mountain']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
```
