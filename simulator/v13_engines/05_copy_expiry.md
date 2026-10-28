# Copies trigger again and delayed exile is not doubled

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

With Harmonic, the first spell produced 2 Stormsplitter tokens. The second produced 6 more: 9 Stormsplitters including the original. At the next end-step beginning, exactly 8 delayed exile abilities queued (not doubled). Tokens survived until those abilities resolved, then all 8 ceased; the original remained.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Island #450 -> (0, 1, 0)
    MANA P0: Island #452 -> (0, 1, 0)
    MANA P0: Mountain #464 -> (0, 0, 1)
  P0 (magnus) casts Stormsplitter [creature] for 4; mana=9.
    STACK +1 [spell] P0: Stormsplitter.
    Stormsplitter enters battlefield (1/4).
    MANA P0: Island #454 -> (0, 1, 0)
    MANA P0: Mountain #466 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=7.
    STACK +2 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P0: Island #456 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=6.
    STACK +3 [spell] P0: Ponder.
    STACK +4 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +5 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +6 [triggered] P0: Harmonic Prodigy: pump_self.
    PROWESS #547: now 2/4 until cleanup.
    COPY #550: next end-step #1; copiable base only.
    COPY #551: next end-step #1; copiable base only.
    CHOICE ponder_order P0: ['Impulse', 'Fiery Islet', 'Island']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
    MANA P0: Island #458 -> (0, 1, 0)
  P0 (magnus) casts Preordain [sorcery] for 1; mana=5.
    STACK +7 [spell] P0: Preordain.
    STACK +8 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +9 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +10 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +11 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +12 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +13 [triggered] P0: Stormsplitter: copy_source_until_end.
    STACK +14 [triggered] P0: Stormsplitter: copy_source_until_end.
    COPY #556: next end-step #1; copiable base only.
    COPY #557: next end-step #1; copiable base only.
    COPY #558: next end-step #1; copiable base only.
    COPY #559: next end-step #1; copiable base only.
    PROWESS #547: now 3/5 until cleanup.
    COPY #560: next end-step #1; copiable base only.
    COPY #561: next end-step #1; copiable base only.
    CHOICE scry P0: ['Fiery Islet', 'Island']; {'top': [], 'bottom': [445, 444]}.
  STEP P0: end.
    END-STEP #1: 8 delayed exile abilities due.
    STACK +15 [triggered] P0: Stormsplitter: exile_object.
    STACK +16 [triggered] P0: Stormsplitter: exile_object.
    STACK +17 [triggered] P0: Stormsplitter: exile_object.
    STACK +18 [triggered] P0: Stormsplitter: exile_object.
    STACK +19 [triggered] P0: Stormsplitter: exile_object.
    STACK +20 [triggered] P0: Stormsplitter: exile_object.
    STACK +21 [triggered] P0: Stormsplitter: exile_object.
    STACK +22 [triggered] P0: Stormsplitter: exile_object.
    DELAYED EXILE #561: completed (departed objects are ignored).
    DELAYED EXILE #560: completed (departed objects are ignored).
    DELAYED EXILE #559: completed (departed objects are ignored).
    DELAYED EXILE #558: completed (departed objects are ignored).
    DELAYED EXILE #557: completed (departed objects are ignored).
    DELAYED EXILE #556: completed (departed objects are ignored).
    DELAYED EXILE #551: completed (departed objects are ignored).
    DELAYED EXILE #550: completed (departed objects are ignored).
```
