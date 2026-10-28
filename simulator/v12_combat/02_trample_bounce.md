# Trample recalculates after blocker bounce

Forced diagnostic with declared synthetic combat setup. Physical decks remain conserved; spell responses use actual sources.

After two blockers were declared, Capsize bounced the 3/3 token (it ceased to exist). The 8-power trampler assigned 2 to the remaining 2/2 and 6 to the defending player. Capsize paid from actual lands.

## Narrative

```text
FORCED DIAGNOSTIC: actual deck source layout; declared synthetic combat tokens/keyword grants. Not a natural opening or newly supported named card.
    ATTACK: P0 Synthetic attacker #536 -> P1.
    BLOCK: #537 blocks #536.
    BLOCK: #538 blocks #536.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Island #450 -> (0, 1, 0)
    MANA P0: Island #452 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 3; mana=7.
    STACK +1 [spell] P0: Capsize.
    Capsize returns Synthetic blocker to its owner's hand.
  STEP P0: combat_damage.
    COMBAT DAMAGE combat_damage: creatures={537: 2, 536: 2}; players={1: 6}.
```
