# Baral loot is successful-counter-only and independently optional

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

An actual Counterspell countered the control seat's creature spell. Harmonic doubled Baral into two separate loot triggers. The first was accepted (draw then discard); the second was declined. Counterspell's colored UU requirement was preserved despite Baral.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
    MANA P0: Island #462 -> (0, 1, 0)
    MANA P0: Island #464 -> (0, 1, 0)
  P0 (magnus) casts Baral, Chief of Compliance [creature] for 2; mana=11.
    STACK +1 [spell] P0: Baral, Chief of Compliance.
    Baral, Chief of Compliance enters battlefield (1/3).
    MANA P0: Island #466 -> (0, 1, 0)
    MANA P0: Mountain #478 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=9.
    STACK +2 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P2: control:land:11 #518 -> (1, 0, 0)
    MANA P2: control:land:10 #520 -> (1, 0, 0)
    MANA P2: control:land:35 #522 -> (1, 0, 0)
    MANA P2: control:land:36 #524 -> (1, 0, 0)
  P2 (control) casts control:medium:0 [creature] for 4; mana=4.
    STACK +3 [spell] P2: control:medium:0.
    MANA P0: Island #468 -> (0, 1, 0)
    MANA P0: Island #470 -> (0, 1, 0)
  P0 (magnus) casts Counterspell [instant] for 2; mana=7.
    STACK +4 [spell] P0: Counterspell.
    STACK +5 [triggered] P0: Harmonic Prodigy: pump_self.
    PROWESS #561: now 2/4 until cleanup.
    STACK -3: control:medium:0 countered.
    STACK +6 [triggered] P0: Baral, Chief of Compliance: optional_loot.
    STACK +7 [triggered] P0: Baral, Chief of Compliance: optional_loot.
    CHOICE baral_discard P0: ['Frantic Search']; {}.
    BARAL LOOT P0: accepted=True.
    BARAL LOOT P0: accepted=False.
```
