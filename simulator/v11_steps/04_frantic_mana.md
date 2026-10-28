# Frantic Search: atomic selection, untap and source reuse

**Forced-board interaction diagnostic; not an unbiased opening.**

Drew 2, discarded 2, untapped 3 actual lands. Young Pyromancer then reused restored source IDs [434] in the same main phase.

## Branch 1

```text
FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Island #436 -> (0, 1, 0)
    MANA P0: Island #438 -> (0, 1, 0)
  P0 (magnus) casts Frantic Search [instant] for 3; mana=7.
    STACK +1 [spell] P0: Frantic Search.
    Frantic Search: draw 2, discard ('Reiterate', 'Underworld Breach'), untap lands (434, 436, 438); no intermediate priority.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Mountain #446 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=8.
    STACK +2 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
```
