# Two damage steps create two Magnus triggers

Forced diagnostic with declared synthetic combat setup. Physical decks remain conserved; spell responses use actual sources.

Actual Magnus received an explicitly synthetic double-strike grant. Each 4-damage hit queued its own printed token trigger. Priority resolved one Spawn after each step: 8 player damage, 2 Spawn total.

## Narrative

```text
FORCED DIAGNOSTIC: actual deck source layout; declared synthetic combat tokens/keyword grants. Not a natural opening or newly supported named card.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Island #436 -> (0, 1, 0)
    MANA P0: Island #438 -> (0, 1, 0)
    MANA P0: Island #440 -> (0, 1, 0)
    MANA P0: Mountain #446 -> (0, 0, 1)
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=5.
    STACK +1 [spell] P0: Magnus the Red.
    Magnus the Red enters battlefield (4/5).
SYNTHETIC KEYWORD GRANT: double_strike added to the actual Magnus object for trigger testing; no printed grant card claimed.
    ATTACK: P0 Magnus the Red #523 -> P1.
  STEP P0: first_strike_damage.
    COMBAT DAMAGE first_strike_damage: creatures={}; players={1: 4}.
    STACK +2 [triggered] P0: Magnus the Red: create_token.
  STEP P0: combat_damage.
    COMBAT DAMAGE combat_damage: creatures={}; players={1: 4}.
    STACK +3 [triggered] P0: Magnus the Red: create_token.
```
