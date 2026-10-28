# Double strike uses damage marked in the first step

Forced diagnostic with declared synthetic combat setup. Physical decks remain conserved; spell responses use actual sources.

First-strike damage marked 4 on the 1/6 blocker. In the normal damage step, another 2 was lethal; the remaining 2 trampled through. The blocker dealt 1 back only in the normal step.

## Narrative

```text
FORCED DIAGNOSTIC: actual deck source layout; declared synthetic combat tokens/keyword grants. Not a natural opening or newly supported named card.
    ATTACK: P0 Synthetic attacker #536 -> P1.
    BLOCK: #537 blocks #536.
  STEP P0: first_strike_damage.
    COMBAT DAMAGE first_strike_damage: creatures={537: 4}; players={1: 0}.
  STEP P0: combat_damage.
    COMBAT DAMAGE combat_damage: creatures={537: 2, 536: 1}; players={1: 2}.
```
