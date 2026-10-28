# Artifact power tracks tokens entering and being spent

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

Artist was 4 power with Sol Ring plus an artifact Soldier. Ponder added 2 Treasures and another Soldier, raising it to 7. Activating an actual Treasure for U immediately lowered power to 6. That mana paid for Preordain; its triggers added 3 artifacts, raising power to 9.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Island #450 -> (0, 1, 0)
    MANA P0: Island #452 -> (0, 1, 0)
    MANA P0: Mountain #464 -> (0, 0, 1)
  P0 (magnus) casts Storm-Kiln Artist [creature] for 4; mana=9.
    STACK +1 [spell] P0: Storm-Kiln Artist.
    Storm-Kiln Artist enters battlefield (2/2).
    MANA P0: Island #454 -> (0, 1, 0)
    MANA P0: Mountain #466 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=7.
    STACK +2 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P0: Island #456 -> (0, 1, 0)
    MANA P0: Mountain #468 -> (0, 0, 1)
  P0 (magnus) casts Third Path Iconoclast [creature] for 2; mana=5.
    STACK +3 [spell] P0: Third Path Iconoclast.
    Third Path Iconoclast enters battlefield (1/1).
    MANA P0: Island #458 -> (0, 1, 0)
  P0 (magnus) casts Sol Ring [artifact] for 1; mana=4.
    STACK +4 [spell] P0: Sol Ring.
    STACK +5 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +6 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #547: now 2/4 until cleanup.
    Sol Ring enters untapped; its mana ability is immediately available.
    MANA P0: Island #460 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=5.
    STACK +7 [spell] P0: Ponder.
    STACK +8 [triggered] P0: Storm-Kiln Artist: create_token.
    STACK +9 [triggered] P0: Storm-Kiln Artist: create_token.
    STACK +10 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +11 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #547: now 3/5 until cleanup.
    CHOICE ponder_order P0: ['Riptide Laboratory', 'Mountain', 'Exalted Flamer of Tzeentch']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': True}.
    MANA P0: Treasure #558 -> (0, 1, 0) (sacrificed)
  P0 (magnus) casts Preordain [sorcery] for 1; mana=6.
    STACK +12 [spell] P0: Preordain.
    STACK +13 [triggered] P0: Storm-Kiln Artist: create_token.
    STACK +14 [triggered] P0: Storm-Kiln Artist: create_token.
    STACK +15 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +16 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #547: now 4/6 until cleanup.
    CHOICE scry P0: ['Spirebluff Canal', 'Baral, Chief of Compliance']; {'top': [66], 'bottom': [4]}.
```
