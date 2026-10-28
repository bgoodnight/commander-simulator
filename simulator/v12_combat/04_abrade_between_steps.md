# Abrade between damage steps preserves blocked status

Forced diagnostic with declared synthetic combat setup. Physical decks remain conserved; spell responses use actual sources.

The double-striker marked 3 in the first step. Abrade then dealt 3 using actual source mana, killing the 1/5 blocker before it could retaliate. The attacker remained blocked and had no trample, so its second step dealt no player damage.

## Narrative

```text
FORCED DIAGNOSTIC: actual deck source layout; declared synthetic combat tokens/keyword grants. Not a natural opening or newly supported named card.
    ATTACK: P0 Synthetic attacker #564 -> P1.
    BLOCK: #565 blocks #564.
  STEP P0: first_strike_damage.
    COMBAT DAMAGE first_strike_damage: creatures={565: 3}; players={}.
    MANA P0: Island #476 -> (0, 1, 0)
    MANA P0: Mountain #488 -> (0, 0, 1)
  P0 (magnus) casts Abrade [instant] for 2; mana=8.
    STACK +1 [spell] P0: Abrade.
    Abrade damage mode: 3 damage to Synthetic blocker.
  STEP P0: combat_damage.
    COMBAT DAMAGE combat_damage: creatures={}; players={}.
```
