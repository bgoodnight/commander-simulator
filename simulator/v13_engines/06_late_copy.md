# A copy made during an end step waits through cleanup

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

Brainstorm was cast with actual source mana during end-step priority. Its Stormsplitter token was created after that step began. It survived cleanup, then its delayed exile triggered and resolved at the following player's end step.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
    MANA P0: Island #462 -> (0, 1, 0)
    MANA P0: Island #464 -> (0, 1, 0)
    MANA P0: Island #466 -> (0, 1, 0)
    MANA P0: Mountain #478 -> (0, 0, 1)
  P0 (magnus) casts Stormsplitter [creature] for 4; mana=9.
    STACK +1 [spell] P0: Stormsplitter.
    Stormsplitter enters battlefield (1/4).
  STEP P0: end.
    END-STEP #1: 0 delayed exile abilities due.
    MANA P0: Island #468 -> (0, 1, 0)
  P0 (magnus) casts Brainstorm [instant] for 1; mana=8.
    STACK +2 [spell] P0: Brainstorm.
    STACK +3 [triggered] P0: Stormsplitter: copy_source_until_end.
    COPY #561: next end-step #2; copiable base only.
    CHOICE brainstorm_put_back P0: ['Cascade Bluffs', 'Riverglide Pathway']; {}.
  STEP P1: end.
    END-STEP #2: 1 delayed exile abilities due.
    STACK +4 [triggered] P0: Stormsplitter: exile_object.
    DELAYED EXILE #561: completed (departed objects are ignored).
```
