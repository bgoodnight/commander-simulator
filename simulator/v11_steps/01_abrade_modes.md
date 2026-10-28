# Abrade: announced modes, damage and artifact destruction

**Forced-board interaction diagnostic; not an unbiased opening.**

Creature mode marked 3 damage on a 1-toughness creature (survived=False); artifact mode destroyed its chosen ramp permanent.

## Branch 1

```text
FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.
    MANA P1: aggro:land:23 #475 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:0 [creature] for 1; mana=7.
    STACK +1 [spell] P1: aggro:small:0.
    MANA P0: Island #448 -> (0, 1, 0)
    MANA P0: Mountain #460 -> (0, 0, 1)
  P0 (magnus) casts Abrade [instant] for 2; mana=8.
    STACK +2 [spell] P0: Abrade.
    Abrade damage mode: 3 damage to aggro:small:0.
```

## Branch 2

```text
FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.
    MANA P2: control:land:20 #484 -> (1, 0, 0)
    MANA P2: control:land:15 #486 -> (1, 0, 0)
    MANA P2: control:land:29 #488 -> (1, 0, 0)
  P2 (control) casts control:ramp:1 [artifact] for 3; mana=5.
    STACK +1 [spell] P2: control:ramp:1.
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Mountain #446 -> (0, 0, 1)
  P0 (magnus) casts Abrade [instant] for 2; mana=8.
    STACK +2 [spell] P0: Abrade.
    Abrade artifact mode: control:ramp:1; destroyed=True.
```
