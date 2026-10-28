# Capsize after first hit prevents the second hit

Forced diagnostic with declared synthetic combat setup. Physical decks remain conserved; spell responses use actual sources.

The first 4-damage hit resolved its Spawn trigger. Capsize then returned Magnus to hand using actual lands and the token discount. The scheduled normal damage step still occurred, but the departed attacker dealt nothing: 4 damage, 1 Spawn.

## Narrative

```text
FORCED DIAGNOSTIC: actual deck source layout; declared synthetic combat tokens/keyword grants. Not a natural opening or newly supported named card.
    MANA P0: Island #476 -> (0, 1, 0)
    MANA P0: Island #478 -> (0, 1, 0)
    MANA P0: Island #480 -> (0, 1, 0)
    MANA P0: Island #482 -> (0, 1, 0)
    MANA P0: Mountain #488 -> (0, 0, 1)
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=5.
    STACK +1 [spell] P0: Magnus the Red.
    Magnus the Red enters battlefield (4/5).
SYNTHETIC KEYWORD GRANT: double_strike on Magnus; source-paid self-bounce is the interruption under test.
    ATTACK: P0 Magnus the Red #565 -> P1.
  STEP P0: first_strike_damage.
    COMBAT DAMAGE first_strike_damage: creatures={}; players={1: 4}.
    STACK +2 [triggered] P0: Magnus the Red: create_token.
    MANA P0: Island #484 -> (0, 1, 0)
    MANA P0: Island #486 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 2; mana=3.
    STACK +3 [spell] P0: Capsize.
    Capsize returns Magnus the Red to its owner's hand.
  STEP P0: combat_damage.
    COMBAT DAMAGE combat_damage: creatures={}; players={}.
```
