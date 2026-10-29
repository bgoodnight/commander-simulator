# Removing Adaptation makes the Riptide target illegal

Forced conserved setup; actual sources; synthetic response explicitly marked where used.

Capsize returned Adaptation while the Riptide ability waited. Iconoclast remained on the battlefield but lost the Wizard subtype; Riptide rechecked its target and failed without returning it.

```text
FORCED DIAGNOSTIC: declared actual card/source layout; not a natural opening.
    LAND ENTERS P0: Island #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #473; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #475; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #477; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #479; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #481; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #487; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #489; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #491; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #469 -> (0, 1, 0)
    MANA P0: Island #471 -> (0, 1, 0)
    MANA P0: Island #473 -> (0, 1, 0)
  P0 (magnus) casts Arcane Adaptation [enchantment] for 3; mana=9.
    STACK +1 [spell] P0: Arcane Adaptation.
    Arcane Adaptation enters: Wizard chosen; additive types apply in all declared zones.
    MANA P0: Island #475 -> (0, 1, 0)
    MANA P0: Mountain #485 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=7.
    STACK +2 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P0: Island #477 -> (0, 1, 0)
    MANA P0: Mountain #487 -> (0, 0, 1)
  P0 (magnus) casts Third Path Iconoclast [creature] for 2; mana=5.
    STACK +3 [spell] P0: Third Path Iconoclast.
    Third Path Iconoclast enters battlefield (1/1).
    LAND ENTERS P0: Riptide Laboratory #502; tapped=False; life_paid=0; cause=declared_fixture.
DIAGNOSTIC NEXT OWN TURN: actual land sources untapped.
    MANA P0: Island #469 -> (0, 1, 0)
    MANA P0: Island #471 -> (0, 1, 0)
    STACK +4 [activated] P0: Riptide Laboratory: riptide_wizard_bounce.
    MANA P0: Island #473 -> (0, 1, 0)
    MANA P0: Island #475 -> (0, 1, 0)
    MANA P0: Island #477 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 3; mana=7.
    STACK +5 [spell] P0: Capsize.
    STACK +6 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +7 [triggered] P0: Third Path Iconoclast: create_token.
    STACK +8 [triggered] P0: Third Path Iconoclast: create_token.
    PROWESS #497: now 2/4 until cleanup.
    Capsize returns Arcane Adaptation to its owner's hand.
```
