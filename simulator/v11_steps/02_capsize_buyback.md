# Capsize: successful buyback, then a countered recast

**Forced-board interaction diagnostic; not an unbiased opening.**

First cast returned the target and Capsize to hand. After an explicitly advanced untap, the second bought-back cast was countered; Capsize entered the graveyard.

## Branch 1

```text
FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.
    MANA P2: control:land:36 #484 -> (1, 0, 0)
    MANA P2: control:land:26 #486 -> (1, 0, 0)
  P2 (control) casts control:small:1 [creature] for 2; mana=6.
    STACK +1 [spell] P2: control:small:1.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Island #436 -> (0, 1, 0)
    MANA P0: Island #438 -> (0, 1, 0)
    MANA P0: Island #440 -> (0, 1, 0)
    MANA P0: Island #442 -> (0, 1, 0)
    MANA P0: Island #444 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 6; mana=4.
    STACK +2 [spell] P0: Capsize.
    Capsize returns control:small:1 to its owner's hand.
    Buyback paid: Capsize returns to hand after successful resolution.
  DIAGNOSTIC NEXT TURN: untap the detailed seat's actual sources.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Island #436 -> (0, 1, 0)
    MANA P0: Island #438 -> (0, 1, 0)
    MANA P0: Island #440 -> (0, 1, 0)
    MANA P0: Island #442 -> (0, 1, 0)
    MANA P0: Island #444 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 6; mana=4.
    STACK +3 [spell] P0: Capsize.
    MANA P2: control:land:13 #488 -> (1, 0, 0)
    MANA P2: control:land:33 #490 -> (1, 0, 0)
  P2 (control) casts control:counter:0 [instant] for 2; mana=4.
    STACK +4 [spell] P2: control:counter:0.
    STACK -3: Capsize countered.
```
