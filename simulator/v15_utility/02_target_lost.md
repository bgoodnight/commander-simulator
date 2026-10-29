# Sanctuary target leaving the graveyard causes the trigger to fail

Forced conserved setup; actual sources; synthetic response explicitly marked where used.

The trigger chose Ponder when placed on the stack. A declared synthetic response moved that exact graveyard object to exile; on resolution the trigger had no legal target and did not return it. No printed graveyard-exile card was added by this scenario.

```text
FORCED DIAGNOSTIC: declared actual card/source layout; not a natural opening.
    LAND ENTERS P0: Island #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #473; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #469 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=2.
    STACK +1 [spell] P0: Ponder.
    CHOICE ponder_order P0: ['Pongify', 'Third Path Iconoclast', 'Reiterate']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
    LAND ENTERS P0: Mystic Sanctuary #479; tapped=False; life_paid=0; cause=declared_fixture.
    SANCTUARY #479: untapped entry triggered; target chosen at stack placement.
    STACK +2 [triggered] P0: Mystic Sanctuary: sanctuary_return.
SYNTHETIC RESPONSE FIXTURE: move the targeted graveyard card to exile while the trigger is waiting.
    FIZZLE: Sanctuary target #477 is no longer legal.
```
