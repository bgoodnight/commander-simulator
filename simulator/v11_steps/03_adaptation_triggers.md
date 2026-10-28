# Arcane Adaptation: live Wizard types and captured triggers

**Forced-board interaction diagnostic; not an unbiased opening.**

Adaptation made Iconoclast a Wizard. Harmonic Prodigy doubled triggers from Preordain and the responding Capsize (4 Soldiers). Capsize bounced Adaptation; already queued triggers survived. A later Ponder produced only 1 Soldier.

## Branch 1

```text
FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Mountain #460 -> (0, 0, 1)
  P0 (magnus) casts Third Path Iconoclast [creature] for 2; mana=8.
    STACK +1 [spell] P0: Third Path Iconoclast.
    Third Path Iconoclast enters battlefield (1/1).
    MANA P0: Island #450 -> (0, 1, 0)
    MANA P0: Mountain #462 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=6.
    STACK +2 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P0: Island #452 -> (0, 1, 0)
    MANA P0: Island #454 -> (0, 1, 0)
    MANA P0: Island #456 -> (0, 1, 0)
  P0 (magnus) casts Arcane Adaptation [enchantment] for 3; mana=3.
    STACK +3 [spell] P0: Arcane Adaptation.
    STACK +4 [triggered] P0: Third Path Iconoclast: create_token.
    Arcane Adaptation enters: Wizard chosen; additive types apply in all declared zones.
  DIAGNOSTIC NEXT TURN: untap the detailed seat's actual sources.
    MANA P0: Island #448 -> (0, 1, 0)
  P0 (magnus) casts Preordain [sorcery] for 1; mana=9.
    STACK +5 [spell] P0: Preordain.
    STACK +6 [triggered] P0: Third Path Iconoclast: create_token.
    STACK +7 [triggered] P0: Third Path Iconoclast: create_token.
    MANA P0: Island #450 -> (0, 1, 0)
    MANA P0: Island #452 -> (0, 1, 0)
    MANA P0: Island #454 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 3; mana=6.
    STACK +8 [spell] P0: Capsize.
    STACK +9 [triggered] P0: Third Path Iconoclast: create_token.
    STACK +10 [triggered] P0: Third Path Iconoclast: create_token.
    Capsize returns Arcane Adaptation to its owner's hand.
    Preordain: partial card selection (1 drawn; exact look/scry/untap not modeled).
    MANA P0: Island #456 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=5.
    STACK +11 [spell] P0: Ponder.
    STACK +12 [triggered] P0: Third Path Iconoclast: create_token.
    Ponder: partial card selection (1 drawn; exact look/scry/untap not modeled).
```
