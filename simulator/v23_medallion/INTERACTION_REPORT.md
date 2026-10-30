# Sapphire Medallion and Capsize buyback

Forced fixture with actual Islands. Sapphire Medallion was cast for two generic mana. Capsize with buyback then cost 3UU instead of 4UU, bounced the token target, and returned to hand.

```text
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #461; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #463; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #465; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #467; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #455 -> (0, 1, 0)
    MANA P0: Island #457 -> (0, 1, 0)
  P0 (magnus) casts Sapphire Medallion [artifact] for 2; mana=0.
    STACK +1 [spell] P0: Sapphire Medallion.
    MANA P0: Island #459 -> (0, 1, 0)
    MANA P0: Island #461 -> (0, 1, 0)
    MANA P0: Island #463 -> (0, 1, 0)
    MANA P0: Island #465 -> (0, 1, 0)
    MANA P0: Island #467 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 5; mana=0.
    STACK +2 [spell] P0: Capsize.
    Capsize returns fixture target to its owner's hand.
    Buyback paid: Capsize returns to hand after successful resolution.
```
