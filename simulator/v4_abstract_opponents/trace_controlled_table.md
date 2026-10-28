# Trace Controlled Table

**Seed:** 20261029  
**Archetypes:** aggro, control, ramp_stompy  
**Fourth seat:** passive Magnus (40 life, no board, no responses).

## Paired outcomes (exact same abstract decks/draw order at initialization)

| Seat | Without interaction: life / power / threat | With interaction: life / power / threat |
|---|---|---|
| 0: magnus_passive | 40 / 0 / 2.4 | 27 / 0 / 1.6 |
| 1: aggro | 40 / 31 / 39.9 | 26 / 0 / 6.7 |
| 2: control | 40 / 24 / 47.2 | 15 / 0 / 9.4 |
| 3: ramp_stompy | 40 / 30 / 51.5 | 31 / 0 / 15.8 |

## Main run — full event trace

```text

===== ROUND 1 =====

P1 (aggro) starts life=40, cards=7, sources=0, power=0
  P1 (aggro) land drop; lands=1.
  P1 (aggro) CAST small for 1 mana; 0 left.
    Adds a 3/3 small creature (next turn attacks).

P2 (control) starts life=40, cards=7, sources=0, power=0
  P2 (control) land drop; lands=1.

P3 (ramp_stompy) starts life=40, cards=7, sources=0, power=0
  P3 (ramp_stompy) land drop; lands=1.
  P3 (ramp_stompy) CAST small for 1 mana; 0 left.
    Adds a 3/2 small creature (next turn attacks).
END ROUND ranks (high to low): P3:ramp_stompy (7.9, 40 life) > P1:aggro (7.9, 40 life) > P2:control (5.1, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 2 =====

P1 (aggro) starts life=40, cards=6, sources=1, power=3
  P1 (aggro) land drop; lands=2.
  P1 (aggro) CAST small for 1 mana; 1 left.
    Adds a 2/3 small creature (next turn attacks).
  P1 (aggro) CAST small for 1 mana; 0 left.
    Adds a 1/1 small creature (next turn attacks).
    ATTACK P1 -> P2: 3 unblocked; life=37.

P2 (control) starts life=37, cards=7, sources=1, power=0
  P2 (control) land drop; lands=2.
  P2 (control) CAST engine for 2 mana; 0 left.
    Persistent draw/token engine enters as 2/3 creature.

P3 (ramp_stompy) starts life=40, cards=6, sources=1, power=3
  P3 (ramp_stompy) land drop; lands=2.
  P3 (ramp_stompy) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 3.
    BLOCK P1 2/3 vs P3 3/2 -> attacker_dead=True, blocker_dead=True.
END ROUND ranks (high to low): P2:control (10.7, 37 life) > P1:aggro (9.5, 40 life) > P3:ramp_stompy (6.2, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 3 =====

P1 (aggro) starts life=40, cards=4, sources=2, power=4
  P1 (aggro) land drop; lands=3.
  P1 (aggro) CAST medium for 3 mana; 0 left.
    Adds a 4/2 medium creature (next turn attacks).
    ATTACK P1 -> P2: 3 unblocked; life=34.
    BLOCK P2 2/3 vs P1 1/1 -> attacker_dead=True, blocker_dead=False.

P2 (control) starts life=34, cards=6, sources=2, power=2
  P2 (control) land drop; lands=3.
  P2 engine generated 1/1 token.
  P2 (control) CAST draw for 3 mana; 0 left.
    Draws 3 extra abstract cards.
    ATTACK P2 -> P1: 2 unblocked; life=38.

P3 (ramp_stompy) starts life=40, cards=5, sources=3, power=0
  P3 (ramp_stompy) land drop; lands=3.
  P3 (ramp_stompy) CAST ramp for 3 mana; 1 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.
END ROUND ranks (high to low): P2:control (13.0, 34 life) > P1:aggro (12.6, 38 life) > P3:ramp_stompy (7.7, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 4 =====

P1 (aggro) starts life=38, cards=3, sources=3, power=7
  P1 (aggro) MISSED land drop; lands=3.
  P1 (aggro) CAST small for 1 mana; 2 left.
    Adds a 3/2 small creature (next turn attacks).
  P1 (aggro) CAST burn for 2 mana; 0 left.
    P2 takes 4 direct damage; life=30.
    ATTACK P1 -> P2: 3 unblocked; life=27.
    ATTACK P1 -> P2: 4 unblocked; life=23.

P2 (control) starts life=23, cards=7, sources=3, power=3
  P2 (control) land drop; lands=4.
  P2 (control) CAST ramp for 3 mana; 1 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.

P3 (ramp_stompy) starts life=40, cards=4, sources=5, power=0
  P3 (ramp_stompy) land drop; lands=4.
  P3 (ramp_stompy) CAST ramp for 3 mana; 3 left.
    Permanent ramp +1 mana/turn; next-turn capacity 7.
  P3 (ramp_stompy) CAST medium for 3 mana; 0 left.
    Adds a 3/3 medium creature (next turn attacks).
END ROUND ranks (high to low): P1:aggro (15.3, 38 life) > P2:control (14.0, 23 life) > P3:ramp_stompy (11.9, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 5 =====

P1 (aggro) starts life=38, cards=2, sources=3, power=10
  P1 (aggro) land drop; lands=4.
  P1 (aggro) CAST medium for 4 mana; 0 left.
    Adds a 4/2 medium creature (next turn attacks).
    ATTACK P1 -> P0: 3 unblocked; life=37.
    ATTACK P1 -> P0: 4 unblocked; life=33.
    BLOCK P2 2/3 vs P1 3/2 -> attacker_dead=True, blocker_dead=True.

P2 (control) starts life=23, cards=7, sources=5, power=1
  P2 (control) land drop; lands=5.
  P2 (control) CAST engine for 3 mana; 3 left.
    Persistent draw/token engine enters as 2/3 creature.
  P2 (control) CAST draw for 2 mana; 1 left.
    Draws 3 extra abstract cards.

P3 (ramp_stompy) starts life=40, cards=2, sources=7, power=3
  P3 (ramp_stompy) land drop; lands=5.
  P3 (ramp_stompy) CAST engine for 4 mana; 4 left.
    Persistent draw/token engine enters as noncreature permanent.
  P3 (ramp_stompy) CAST tokens for 4 mana; 0 left.
    Generates 3 1/1 creatures.
    ATTACK P3 -> P2: 3 unblocked; life=20.
END ROUND ranks (high to low): P3:ramp_stompy (19.3, 40 life) > P1:aggro (16.8, 38 life) > P2:control (14.7, 20 life) > P0:magnus_passive (2.0, 33 life)

===== ROUND 6 =====

P1 (aggro) starts life=38, cards=1, sources=4, power=11
  P1 (aggro) MISSED land drop; lands=4.
  P1 (aggro) CAST small for 2 mana; 2 left.
    Adds a 2/3 small creature (next turn attacks).
    ATTACK P1 -> P3: 3 unblocked; life=37.
    BLOCK P2 2/3 vs P1 4/2 -> attacker_dead=True, blocker_dead=True.
    ATTACK P1 -> P3: 4 unblocked; life=33.

P2 (control) starts life=20, cards=7, sources=6, power=1
  P2 (control) MISSED land drop; lands=5.
  P2 (control) CAST ramp for 3 mana; 3 left.
    Permanent ramp +1 mana/turn; next-turn capacity 7.
  P2 (control) CAST draw for 2 mana; 1 left.
    Draws 3 extra abstract cards.
    BLOCK P3 1/1 vs P2 1/1 -> attacker_dead=True, blocker_dead=True.

P3 (ramp_stompy) starts life=33, cards=0, sources=8, power=5
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 engine generated 1/1 token.
  P3 (ramp_stompy) CAST large for 6 mana; 2 left.
    Adds a 7/9 large creature (next turn attacks).
    ATTACK P3 -> P2: 1 unblocked; life=19.
    ATTACK P3 -> P2: 1 unblocked; life=18.
END ROUND ranks (high to low): P3:ramp_stompy (25.6, 33 life) > P1:aggro (15.1, 38 life) > P2:control (8.8, 18 life) > P0:magnus_passive (2.0, 33 life)

===== ROUND 7 =====

P1 (aggro) starts life=38, cards=1, sources=4, power=9
  P1 (aggro) MISSED land drop; lands=4.
  P1 (aggro) CAST burn for 3 mana; 1 left.
    P2 takes 3 direct damage; life=15.
    BLOCK P3 7/9 vs P1 3/3 -> attacker_dead=True, blocker_dead=False.
    ATTACK P1 -> P0: 4 unblocked; life=29.
    ATTACK P1 -> P0: 2 unblocked; life=27.

P2 (control) starts life=15, cards=7, sources=7, power=0
  P2 (control) land drop; lands=6.
  P2 (control) CAST medium for 3 mana; 5 left.
    Adds a 4/3 medium creature (next turn attacks).
  P2 (control) CAST small for 2 mana; 3 left.
    Adds a 1/3 small creature (next turn attacks).

P3 (ramp_stompy) starts life=33, cards=1, sources=8, power=13
  P3 (ramp_stompy) MISSED land drop; lands=5.
    RESPONSE: P2 (control) counters P3's ramp (ramp threat severity 2.0); 2 mana spent.
  P3 (ramp_stompy) CAST ramp for 3 mana; 2 left.
    Permanent ramp +1 mana/turn; next-turn capacity 9.
    ATTACK P3 -> P1: 3 unblocked; life=35.
    ATTACK P3 -> P1: 1 unblocked; life=34.
    ATTACK P3 -> P1: 1 unblocked; life=33.
    ATTACK P3 -> P1: 7 unblocked; life=26.
END ROUND ranks (high to low): P3:ramp_stompy (26.4, 33 life) > P2:control (14.0, 15 life) > P1:aggro (11.3, 26 life) > P0:magnus_passive (1.6, 27 life)

===== ROUND 8 =====

P1 (aggro) starts life=26, cards=1, sources=4, power=6
  P1 (aggro) MISSED land drop; lands=4.
  P1 (aggro) CAST small for 2 mana; 2 left.
    Adds a 2/1 small creature (next turn attacks).
    BLOCK P2 4/3 vs P1 4/2 -> attacker_dead=True, blocker_dead=True.
    ATTACK P1 -> P3: 2 unblocked; life=31.

P2 (control) starts life=15, cards=4, sources=8, power=1
  P2 (control) land drop; lands=7.
  P2 (control) CAST medium for 4 mana; 5 left.
    Adds a 4/2 medium creature (next turn attacks).
  P2 (control) CAST wipe for 5 mana; 0 left.
    WIPE: 9 creatures across all players destroyed.

P3 (ramp_stompy) starts life=31, cards=1, sources=9, power=0
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 (ramp_stompy) CAST large for 6 mana; 3 left.
    Adds a 8/5 large creature (next turn attacks).
  P3 (ramp_stompy) CAST medium for 3 mana; 0 left.
    Adds a 3/5 medium creature (next turn attacks).
END ROUND ranks (high to low): P3:ramp_stompy (22.9, 31 life) > P2:control (9.1, 15 life) > P1:aggro (5.2, 26 life) > P0:magnus_passive (1.6, 27 life)

===== ROUND 9 =====

P1 (aggro) starts life=26, cards=1, sources=4, power=0
  P1 (aggro) land drop; lands=5.
  P1 (aggro) CAST tokens for 5 mana; 0 left.
    Generates 2 1/1 creatures.

P2 (control) starts life=15, cards=2, sources=9, power=0
  P2 (control) land drop; lands=8.
  P2 (control) CAST wipe for 6 mana; 4 left.
    WIPE: 4 creatures across all players destroyed.

P3 (ramp_stompy) starts life=31, cards=0, sources=9, power=0
  P3 (ramp_stompy) MISSED land drop; lands=5.
END ROUND ranks (high to low): P3:ramp_stompy (12.8, 31 life) > P2:control (9.7, 15 life) > P1:aggro (5.8, 26 life) > P0:magnus_passive (1.6, 27 life)

===== ROUND 10 =====

P1 (aggro) starts life=26, cards=0, sources=5, power=0
  P1 (aggro) land drop; lands=6.

P2 (control) starts life=15, cards=1, sources=10, power=0
  P2 (control) MISSED land drop; lands=8.
  P2 (control) CAST removal for 2 mana; 8 left.

P3 (ramp_stompy) starts life=31, cards=1, sources=9, power=0
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 (ramp_stompy) CAST engine for 2 mana; 7 left.
    Persistent draw/token engine enters as noncreature permanent.
    RESPONSE: P2 (control) counters P3's engine (engine threat severity 4.0); 2 mana spent.
END ROUND ranks (high to low): P3:ramp_stompy (15.8, 31 life) > P2:control (9.4, 15 life) > P1:aggro (6.7, 26 life) > P0:magnus_passive (1.6, 27 life)
```

## No-interaction run — full event trace

```text

===== ROUND 1 =====

P1 (aggro) starts life=40, cards=7, sources=0, power=0
  P1 (aggro) land drop; lands=1.
  P1 (aggro) CAST small for 1 mana; 0 left.
    Adds a 3/3 small creature (next turn attacks).

P2 (control) starts life=40, cards=7, sources=0, power=0
  P2 (control) land drop; lands=1.

P3 (ramp_stompy) starts life=40, cards=7, sources=0, power=0
  P3 (ramp_stompy) land drop; lands=1.
  P3 (ramp_stompy) CAST small for 1 mana; 0 left.
    Adds a 3/2 small creature (next turn attacks).
END ROUND ranks (high to low): P3:ramp_stompy (7.9, 40 life) > P1:aggro (7.9, 40 life) > P2:control (5.1, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 2 =====

P1 (aggro) starts life=40, cards=6, sources=1, power=3
  P1 (aggro) land drop; lands=2.
  P1 (aggro) CAST small for 1 mana; 1 left.
    Adds a 2/3 small creature (next turn attacks).
  P1 (aggro) CAST small for 1 mana; 0 left.
    Adds a 1/1 small creature (next turn attacks).

P2 (control) starts life=40, cards=7, sources=1, power=0
  P2 (control) land drop; lands=2.
  P2 (control) CAST engine for 2 mana; 0 left.
    Persistent draw/token engine enters as 2/3 creature.

P3 (ramp_stompy) starts life=40, cards=6, sources=1, power=3
  P3 (ramp_stompy) land drop; lands=2.
  P3 (ramp_stompy) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 3.
END ROUND ranks (high to low): P1:aggro (11.7, 40 life) > P2:control (10.9, 40 life) > P3:ramp_stompy (9.3, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 3 =====

P1 (aggro) starts life=40, cards=4, sources=2, power=6
  P1 (aggro) land drop; lands=3.
  P1 (aggro) CAST medium for 3 mana; 0 left.
    Adds a 5/3 medium creature (next turn attacks).

P2 (control) starts life=40, cards=6, sources=2, power=2
  P2 (control) land drop; lands=3.
  P2 engine generated 1/1 token.
  P2 (control) CAST draw for 3 mana; 0 left.
    Draws 3 extra abstract cards.

P3 (ramp_stompy) starts life=40, cards=5, sources=3, power=3
  P3 (ramp_stompy) land drop; lands=3.
  P3 (ramp_stompy) CAST ramp for 3 mana; 1 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.
END ROUND ranks (high to low): P1:aggro (17.1, 40 life) > P2:control (13.3, 40 life) > P3:ramp_stompy (10.7, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 4 =====

P1 (aggro) starts life=40, cards=3, sources=3, power=11
  P1 (aggro) MISSED land drop; lands=3.
  P1 (aggro) CAST small for 1 mana; 2 left.
    Adds a 2/3 small creature (next turn attacks).
  P1 (aggro) CAST burn for 2 mana; 0 left.

P2 (control) starts life=40, cards=7, sources=3, power=3
  P2 (control) land drop; lands=4.
  P2 engine generated 1/1 token.
  P2 (control) CAST ramp for 3 mana; 1 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.

P3 (ramp_stompy) starts life=40, cards=4, sources=5, power=3
  P3 (ramp_stompy) land drop; lands=4.
  P3 (ramp_stompy) CAST ramp for 3 mana; 3 left.
    Permanent ramp +1 mana/turn; next-turn capacity 7.
  P3 (ramp_stompy) CAST medium for 3 mana; 0 left.
    Adds a 4/3 medium creature (next turn attacks).
END ROUND ranks (high to low): P1:aggro (19.0, 40 life) > P2:control (16.4, 40 life) > P3:ramp_stompy (15.8, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 5 =====

P1 (aggro) starts life=40, cards=2, sources=3, power=13
  P1 (aggro) land drop; lands=4.
  P1 (aggro) CAST medium for 4 mana; 0 left.
    Adds a 5/2 medium creature (next turn attacks).

P2 (control) starts life=40, cards=7, sources=5, power=4
  P2 (control) land drop; lands=5.
  P2 (control) CAST engine for 3 mana; 3 left.
    Persistent draw/token engine enters as noncreature permanent.
  P2 (control) CAST draw for 2 mana; 1 left.
    Draws 2 extra abstract cards.

P3 (ramp_stompy) starts life=40, cards=2, sources=7, power=7
  P3 (ramp_stompy) land drop; lands=5.
  P3 (ramp_stompy) CAST engine for 4 mana; 4 left.
    Persistent draw/token engine enters as noncreature permanent.
  P3 (ramp_stompy) CAST tokens for 4 mana; 0 left.
    Generates 2 1/1 creatures.
END ROUND ranks (high to low): P1:aggro (24.4, 40 life) > P3:ramp_stompy (21.9, 40 life) > P2:control (20.2, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 6 =====

P1 (aggro) starts life=40, cards=1, sources=4, power=18
  P1 (aggro) MISSED land drop; lands=4.
  P1 (aggro) CAST small for 2 mana; 2 left.
    Adds a 3/3 small creature (next turn attacks).

P2 (control) starts life=40, cards=7, sources=6, power=4
  P2 (control) land drop; lands=6.
  P2 engine generated 1/1 token.
  P2 (control) CAST ramp for 3 mana; 4 left.
    Permanent ramp +1 mana/turn; next-turn capacity 8.
  P2 (control) CAST draw for 2 mana; 2 left.
    Draws 3 extra abstract cards.
  P2 (control) CAST small for 2 mana; 0 left.
    Adds a 1/2 small creature (next turn attacks).

P3 (ramp_stompy) starts life=40, cards=0, sources=8, power=9
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 engine generated 1/1 token.
  P3 (ramp_stompy) CAST large for 6 mana; 2 left.
    Adds a 6/8 large creature (next turn attacks).
END ROUND ranks (high to low): P3:ramp_stompy (28.8, 40 life) > P1:aggro (27.4, 40 life) > P2:control (24.6, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 7 =====

P1 (aggro) starts life=40, cards=1, sources=4, power=21
  P1 (aggro) MISSED land drop; lands=4.
  P1 (aggro) CAST burn for 3 mana; 1 left.

P2 (control) starts life=40, cards=7, sources=8, power=6
  P2 (control) land drop; lands=7.
  P2 engine generated 1/1 token.
  P2 (control) CAST medium for 3 mana; 6 left.
    Adds a 4/2 medium creature (next turn attacks).
  P2 (control) CAST medium for 4 mana; 2 left.
    Adds a 3/5 medium creature (next turn attacks).

P3 (ramp_stompy) starts life=40, cards=0, sources=8, power=16
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 (ramp_stompy) CAST ramp for 3 mana; 5 left.
    Permanent ramp +1 mana/turn; next-turn capacity 9.
END ROUND ranks (high to low): P2:control (33.8, 40 life) > P3:ramp_stompy (29.9, 40 life) > P1:aggro (27.4, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 8 =====

P1 (aggro) starts life=40, cards=1, sources=4, power=21
  P1 (aggro) MISSED land drop; lands=4.
  P1 (aggro) CAST small for 2 mana; 2 left.
    Adds a 2/1 small creature (next turn attacks).

P2 (control) starts life=40, cards=7, sources=9, power=14
  P2 (control) land drop; lands=8.
  P2 engine generated 1/1 token.

P3 (ramp_stompy) starts life=40, cards=1, sources=9, power=16
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 (ramp_stompy) CAST large for 6 mana; 3 left.
    Adds a 6/8 large creature (next turn attacks).
  P3 (ramp_stompy) CAST ramp for 3 mana; 0 left.
    Permanent ramp +2 mana/turn; next-turn capacity 11.
END ROUND ranks (high to low): P3:ramp_stompy (37.0, 40 life) > P2:control (36.0, 40 life) > P1:aggro (29.6, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 9 =====

P1 (aggro) starts life=40, cards=1, sources=4, power=23
  P1 (aggro) land drop; lands=5.
  P1 (aggro) CAST tokens for 5 mana; 0 left.
    Generates 4 2/2 creatures.

P2 (control) starts life=40, cards=7, sources=10, power=15
  P2 (control) land drop; lands=9.
  P2 engine generated 1/1 token.
  P2 (control) CAST ramp for 3 mana; 8 left.
    Permanent ramp +1 mana/turn; next-turn capacity 12.
  P2 (control) CAST large for 5 mana; 3 left.
    Adds a 8/9 large creature (next turn attacks).

P3 (ramp_stompy) starts life=40, cards=0, sources=11, power=22
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 (ramp_stompy) CAST medium for 3 mana; 8 left.
    Adds a 5/5 medium creature (next turn attacks).
END ROUND ranks (high to low): P2:control (46.3, 40 life) > P3:ramp_stompy (42.0, 40 life) > P1:aggro (39.0, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 10 =====

P1 (aggro) starts life=40, cards=0, sources=5, power=31
  P1 (aggro) land drop; lands=6.

P2 (control) starts life=40, cards=7, sources=12, power=24
  P2 (control) land drop; lands=10.

P3 (ramp_stompy) starts life=40, cards=1, sources=11, power=27
  P3 (ramp_stompy) MISSED land drop; lands=5.
  P3 engine generated 1/1 token.
  P3 (ramp_stompy) CAST engine for 2 mana; 9 left.
    Persistent draw/token engine enters as 2/3 creature.
  P3 (ramp_stompy) CAST engine for 2 mana; 7 left.
    Persistent draw/token engine enters as noncreature permanent.
END ROUND ranks (high to low): P3:ramp_stompy (51.5, 40 life) > P2:control (47.2, 40 life) > P1:aggro (39.9, 40 life) > P0:magnus_passive (2.4, 40 life)
```