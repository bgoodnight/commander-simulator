# Mage Siege, Harmonic, and Lindblum

Forced fixture using actual land-source payments. Mage Siege created a black Wizard token and exiled Lindblum. Casting Consider caused that Wizard to damage each opponent twice because Harmonic Prodigy doubled the triggered ability. Lindblum was then played tapped from Adventure exile.

```text
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #461; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #463; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #465; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #467; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #473; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #475; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #477; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Mountain #467 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=0.
    STACK +1 [spell] P0: Harmonic Prodigy.
    Harmonic Prodigy enters battlefield (1/3).
    MANA P0: Island #457 -> (0, 1, 0)
    MANA P0: Island #459 -> (0, 1, 0)
    MANA P0: Mountain #469 -> (0, 0, 1)
  P0 casts Mage Siege as Adventure for 3.
    STACK +2 [spell] P0: Mage Siege.
    STACK +3 [triggered] P0: Harmonic Prodigy: pump_self.
    PROWESS #480: now 2/4 until cleanup.
    MAGE SIEGE: create a 0/1 black Wizard token.
    Mage Siege resolves: Lindblum is exiled on Adventure.
    MANA P0: Island #461 -> (0, 1, 0)
  P0 (magnus) casts Consider [instant] for 1; mana=0.
    STACK +4 [spell] P0: Consider.
    STACK +5 [triggered] P0: Harmonic Prodigy: pump_self.
    STACK +6 [triggered] P0: Wizard: mage_siege_damage.
    STACK +7 [triggered] P0: Wizard: mage_siege_damage.
    PROWESS #480: now 3/5 until cleanup.
    CONSIDER P0: surveil card #432, move to graveyard=False; draw one.
    LAND ENTERS P0: Lindblum, Industrial Regency #489; tapped=True; life_paid=0; cause=land_play.
```
