# Life payment and typed lands produce different legal mana

Forced conserved setup; real deck cards and source payments.

Branch 1 declined Steam Vents payment, leaving it tapped at 40 life. Its Island/Mountain types still let Sulfur Falls enter untapped and pay for Ponder. Branch 2 paid 2 life for Steam Vents, then used it for Ponder; life was 38 and damage taken stayed zero.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Steam Vents #469; tapped=True; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Sulfur Falls #471; tapped=False; life_paid=0; cause=land_play.
    MANA P0: Sulfur Falls #471 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=0.
    STACK +1 [spell] P0: Ponder.
    CHOICE ponder_order P0: ['Mountain', 'Stormcarved Coast', 'Heralds of Tzeentch']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
```

## Branch 2

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Steam Vents #469; tapped=False; life_paid=2; cause=land_play.
    MANA P0: Steam Vents #469 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=0.
    STACK +1 [spell] P0: Ponder.
    CHOICE ponder_order P0: ['Mountain', 'Baral, Chief of Compliance', 'Searing Touch']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
```
