# Queued copies survive a source bounce without copying pumps

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

Ponder queued a copy trigger. Capsize responded, queuing another before bouncing the pumped original Stormsplitter. Both copy triggers resolved: the older one used last-known copiable values. Both tokens were base 1/4, not the modified original's 4/7; the actual original card returned to hand.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
    MANA P0: Island #476 -> (0, 1, 0)
    MANA P0: Island #478 -> (0, 1, 0)
    MANA P0: Island #480 -> (0, 1, 0)
    MANA P0: Mountain #492 -> (0, 0, 1)
  P0 (magnus) casts Stormsplitter [creature] for 4; mana=9.
    STACK +1 [spell] P0: Stormsplitter.
    Stormsplitter enters battlefield (1/4).
    MANA P0: Island #482 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=8.
    STACK +2 [spell] P0: Ponder.
    STACK +3 [triggered] P0: Stormsplitter: copy_source_until_end.
    MANA P0: Island #484 -> (0, 1, 0)
    MANA P0: Island #486 -> (0, 1, 0)
    MANA P0: Island #488 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 3; mana=5.
    STACK +4 [spell] P0: Capsize.
    STACK +5 [triggered] P0: Stormsplitter: copy_source_until_end.
    COPY #577: next end-step #1; copiable base only.
    Capsize returns Stormsplitter to its owner's hand.
    COPY #580: next end-step #1; copiable base only.
    CHOICE ponder_order P0: ['Arcane Denial', 'Mountain', 'Step Through']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
```
