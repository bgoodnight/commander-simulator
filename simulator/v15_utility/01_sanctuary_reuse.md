# Sanctuary returns Ponder for a second cast

Forced conserved setup; actual sources; synthetic response explicitly marked where used.

Three other Islands let Sanctuary enter untapped. Its triggered ability targeted the previously cast Ponder in the graveyard and put it on top. The diagnostic draw and a second source-paid cast produced another Pyromancer Elemental: two in total.

```text
FORCED DIAGNOSTIC: declared actual card/source layout; not a natural opening.
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #461; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Mountain #461 -> (0, 0, 1)
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=2.
    STACK +1 [spell] P0: Young Pyromancer.
    Young Pyromancer enters battlefield (2/1).
    MANA P0: Island #457 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=1.
    STACK +2 [spell] P0: Ponder.
    STACK +3 [triggered] P0: Young Pyromancer: create_token.
    CHOICE ponder_order P0: ['Preordain', 'Mountain', 'Island']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
    LAND ENTERS P0: Mystic Sanctuary #471; tapped=False; life_paid=0; cause=declared_fixture.
    SANCTUARY #471: untapped entry triggered; target chosen at stack placement.
    STACK +4 [triggered] P0: Mystic Sanctuary: sanctuary_return.
    SANCTUARY: target #469; return to library top=True.
    MANA P0: Island #459 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=1.
    STACK +5 [spell] P0: Ponder.
    STACK +6 [triggered] P0: Young Pyromancer: create_token.
    CHOICE ponder_order P0: ['Mountain', 'Island', 'Spirebluff Canal']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': True}.
```
