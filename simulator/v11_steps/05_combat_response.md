# Combat: response after blocks and persistent blocked status

**Forced-board interaction diagnostic; not an unbiased opening.**

Goblin Electromancer was blocked. Capsize bounced the blocker in the post-block priority window. The attacker remained blocked and dealt zero player damage (no trample).

## Branch 1

```text
FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Mountain #460 -> (0, 0, 1)
  P0 (magnus) casts Goblin Electromancer [creature] for 2; mana=8.
    STACK +1 [spell] P0: Goblin Electromancer.
    Goblin Electromancer enters battlefield (2/2).
    MANA P1: aggro:land:26 #475 -> (1, 0, 0)
    MANA P1: aggro:land:14 #477 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:8 [creature] for 2; mana=6.
    STACK +2 [spell] P1: aggro:small:8.
  DIAGNOSTIC NEXT TURN: untap the detailed seat's actual sources.
    ATTACK: P0 Goblin Electromancer #538 -> P1.
    BLOCK: #541 blocks #538.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Island #450 -> (0, 1, 0)
    MANA P0: Island #452 -> (0, 1, 0)
    MANA P0: Island #454 -> (0, 1, 0)
    MANA P0: Island #456 -> (0, 1, 0)
  P0 (magnus) casts Capsize [instant] for 5; mana=5.
    STACK +3 [spell] P0: Capsize.
    Capsize returns aggro:small:8 to its owner's hand.
    Buyback paid: Capsize returns to hand after successful resolution.
    BLOCKED: #538 has no remaining blocker; no player damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={}.
```
