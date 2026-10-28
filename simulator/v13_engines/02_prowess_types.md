# Prowess, trigger doubling and Wizard adaptation

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

Ponder gave Harmonic exactly +1/+1, doubled Pyromancer to 2 Elementals, and created 1 Iconoclast Soldier. After Adaptation resolved, Preordain doubled Iconoclast too. Totals: 4 Elementals, 4 Soldiers. Harmonic reached 4/6 after three noncreature casts, then returned to 1/3 in cleanup.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Mountain #450 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=11.
    STACK +1 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P0: Island #436 -> (0, 1, 0)
    MANA P0: Mountain #452 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=9.
    STACK +2 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #438 -> (0, 1, 0)
    MANA P0: Mountain #454 -> (0, 0, 1)
  P0 (magnus) casts Third Path Iconoclast [creature] for 2; mana=7.
    STACK +3 [spell] P0: Third Path Iconoclast.
    Third Path Iconoclast enters battlefield (1/1).
    MANA P0: Island #440 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=6.
    STACK +4 [spell] P0: Ponder.
    STACK +5 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +6 [triggered] P0: Young Pyromancer: create_token.
    STACK +7 [triggered] P0: Young Pyromancer: create_token.
    STACK +8 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #530: now 2/4 until cleanup.
    CHOICE ponder_order P0: ['Storm-Kiln Artist', 'Sorcerer Class', 'Cyclonic Rift']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
    MANA P0: Island #442 -> (0, 1, 0)
    MANA P0: Island #444 -> (0, 1, 0)
    MANA P0: Island #446 -> (0, 1, 0)
  P0 (magnus) casts Arcane Adaptation [enchantment] for 3; mana=3.
    STACK +9 [spell] P0: Arcane Adaptation.
    STACK +10 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +11 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #530: now 3/5 until cleanup.
    Arcane Adaptation enters: Wizard chosen; additive types apply in all declared zones.
    MANA P0: Island #448 -> (0, 1, 0)
  P0 (magnus) casts Preordain [sorcery] for 1; mana=2.
    STACK +12 [spell] P0: Preordain.
    STACK +13 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +14 [triggered] P0: Young Pyromancer: create_token.
    STACK +15 [triggered] P0: Young Pyromancer: create_token.
    STACK +16 [triggered] P0: Third Path Iconoclast: create_token.
    STACK +17 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #530: now 4/6 until cleanup.
    CHOICE scry P0: ['Sorcerer Class', 'Cyclonic Rift']; {'top': [], 'bottom': [432, 431]}.
```
