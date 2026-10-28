# Trace Random Table

**Seed:** 20261028  
**Archetypes:** combo, tokens, spellslinger  
**Fourth seat:** passive Magnus (40 life, no board, no responses).

## Paired outcomes (exact same abstract decks/draw order at initialization)

| Seat | Without interaction: life / power / threat | With interaction: life / power / threat |
|---|---|---|
| 0: magnus_passive | 40 / 0 / 2.4 | 24 / 0 / 1.4 |
| 1: combo | 40 / 13 / 53.3 | 29 / 0 / 34.5 |
| 2: tokens | 40 / 62 / 88.9 | 28 / 3 / 18.3 |
| 3: spellslinger | 40 / 31 / 55.3 | 24 / 3 / 18.6 |

## Main run — full event trace

```text

===== ROUND 1 =====

P1 (combo) starts life=40, cards=7, sources=0, power=0
  P1 (combo) land drop; lands=1.

P2 (tokens) starts life=40, cards=7, sources=0, power=0
  P2 (tokens) land drop; lands=1.
  P2 (tokens) CAST small for 1 mana; 0 left.
    Adds a 3/2 small creature (next turn attacks).

P3 (spellslinger) starts life=40, cards=7, sources=0, power=0
  P3 (spellslinger) land drop; lands=1.
END ROUND ranks (high to low): P2:tokens (7.9, 40 life) > P3:spellslinger (5.1, 40 life) > P1:combo (5.1, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 2 =====

P1 (combo) starts life=40, cards=7, sources=1, power=0
  P1 (combo) land drop; lands=2.
  P1 (combo) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 3.

P2 (tokens) starts life=40, cards=6, sources=1, power=3
  P2 (tokens) land drop; lands=2.
  P2 (tokens) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 3.

P3 (spellslinger) starts life=40, cards=7, sources=1, power=0
  P3 (spellslinger) land drop; lands=2.
  P3 (spellslinger) CAST removal for 2 mana; 0 left.
    REMOVES P2's small; remaining power=0.
END ROUND ranks (high to low): P1:combo (6.5, 40 life) > P2:tokens (6.2, 40 life) > P3:spellslinger (5.7, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 3 =====

P1 (combo) starts life=40, cards=6, sources=3, power=0
  P1 (combo) land drop; lands=3.
  P1 (combo) CAST engine for 3 mana; 1 left.
    Persistent draw/token engine enters as noncreature permanent.

P2 (tokens) starts life=40, cards=5, sources=3, power=0
  P2 (tokens) land drop; lands=3.
  P2 (tokens) CAST engine for 2 mana; 2 left.
    Persistent draw/token engine enters as noncreature permanent.

P3 (spellslinger) starts life=40, cards=6, sources=2, power=0
  P3 (spellslinger) land drop; lands=3.
  P3 (spellslinger) CAST ramp for 3 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 4.
END ROUND ranks (high to low): P1:combo (10.1, 40 life) > P2:tokens (9.8, 40 life) > P3:spellslinger (7.1, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 4 =====

P1 (combo) starts life=40, cards=5, sources=4, power=0
  P1 (combo) MISSED land drop; lands=3.
  P1 (combo) CAST draw for 2 mana; 2 left.
    Draws 2 extra abstract cards.
  P1 (combo) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.

P2 (tokens) starts life=40, cards=4, sources=4, power=0
  P2 (tokens) MISSED land drop; lands=3.
  P2 (tokens) CAST engine for 3 mana; 1 left.
    Persistent draw/token engine enters as 2/3 creature.

P3 (spellslinger) starts life=40, cards=5, sources=4, power=0
  P3 (spellslinger) land drop; lands=4.
  P3 (spellslinger) CAST engine for 3 mana; 2 left.
    Persistent draw/token engine enters as 2/3 creature.
END ROUND ranks (high to low): P2:tokens (15.0, 40 life) > P3:spellslinger (12.9, 40 life) > P1:combo (11.2, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 5 =====

P1 (combo) starts life=40, cards=6, sources=5, power=0
  P1 (combo) land drop; lands=4.
  P1 engine generated 1/1 token.
  P1 (combo) CAST draw for 3 mana; 3 left.
    Draws 3 extra abstract cards.
  P1 (combo) CAST draw for 3 mana; 0 left.
    Draws 3 extra abstract cards.

P2 (tokens) starts life=40, cards=4, sources=4, power=2
  P2 (tokens) MISSED land drop; lands=3.
  P2 (tokens) CAST ramp for 2 mana; 2 left.
    Permanent ramp +2 mana/turn; next-turn capacity 6.
  P2 (tokens) CAST small for 1 mana; 1 left.
    Adds a 2/1 small creature (next turn attacks).
    ATTACK P2 -> P1: 2 unblocked; life=38.

P3 (spellslinger) starts life=40, cards=4, sources=5, power=2
  P3 (spellslinger) land drop; lands=5.
  P3 (spellslinger) CAST engine for 4 mana; 2 left.
    Persistent draw/token engine enters as noncreature permanent.
END ROUND ranks (high to low): P2:tokens (19.2, 40 life) > P3:spellslinger (16.7, 40 life) > P1:combo (13.6, 38 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 6 =====

P1 (combo) starts life=38, cards=7, sources=6, power=1
  P1 (combo) land drop; lands=5.
  P1 (combo) CAST engine for 4 mana; 3 left.
    Persistent draw/token engine enters as 2/3 creature.
  P1 (combo) CAST draw for 3 mana; 0 left.
    Draws 3 extra abstract cards.

P2 (tokens) starts life=40, cards=5, sources=6, power=4
  P2 (tokens) land drop; lands=4.
  P2 (tokens) CAST engine for 3 mana; 4 left.
    Persistent draw/token engine enters as 2/3 creature.
  P2 (tokens) CAST engine for 4 mana; 0 left.
    Persistent draw/token engine enters as 2/3 creature.
    BLOCK P1 2/3 vs P2 2/1 -> attacker_dead=True, blocker_dead=False.

P3 (spellslinger) starts life=40, cards=4, sources=6, power=2
  P3 (spellslinger) land drop; lands=6.
  P3 (spellslinger) CAST tokens for 4 mana; 3 left.
    Generates 2 1/1 creatures.
  P3 (spellslinger) CAST burn for 3 mana; 0 left.
    P1 takes 5 direct damage; life=33.
    ATTACK P3 -> P2: 2 unblocked; life=38.
END ROUND ranks (high to low): P2:tokens (27.6, 38 life) > P3:spellslinger (20.0, 40 life) > P1:combo (19.3, 33 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 7 =====

P1 (combo) starts life=33, cards=7, sources=7, power=3
  P1 (combo) land drop; lands=6.
  P1 (combo) CAST combo_piece for 3 mana; 5 left.
    Combo setup pieces now 1.
  P1 (combo) CAST medium for 3 mana; 2 left.
    Adds a 5/5 medium creature (next turn attacks).

P2 (tokens) starts life=38, cards=3, sources=7, power=6
  P2 (tokens) land drop; lands=5.
  P2 engine generated 1/1 token.
  P2 engine generated 1/1 token.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST tokens for 3 mana; 5 left.
    Generates 4 2/2 creatures.
  P2 (tokens) CAST tokens for 5 mana; 0 left.
    Generates 4 1/1 creatures.
    ATTACK P2 -> P3: 2 unblocked; life=38.
    ATTACK P2 -> P3: 2 unblocked; life=36.

P3 (spellslinger) starts life=36, cards=3, sources=7, power=4
  P3 (spellslinger) MISSED land drop; lands=6.
  P3 engine generated 1/1 token.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST engine for 3 mana; 4 left.
    Persistent draw/token engine enters as noncreature permanent.
  P3 (spellslinger) CAST tokens for 4 mana; 0 left.
    Generates 3 1/1 creatures.
    BLOCK P1 5/5 vs P3 2/3 -> attacker_dead=True, blocker_dead=False.
    BLOCK P1 2/3 vs P3 1/1 -> attacker_dead=True, blocker_dead=False.
END ROUND ranks (high to low): P2:tokens (46.2, 38 life) > P1:combo (31.6, 33 life) > P3:spellslinger (22.7, 36 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 8 =====

P1 (combo) starts life=33, cards=6, sources=8, power=8
  P1 (combo) MISSED land drop; lands=6.
  P1 (combo) CAST combo_piece for 2 mana; 6 left.
    Combo setup pieces now 2.
  P1 (combo) CAST small for 1 mana; 5 left.
    Adds a 1/3 small creature (next turn attacks).
  P1 (combo) CAST removal for 3 mana; 2 left.
    REMOVES P3's engine token; remaining power=5.
    ATTACK P1 -> P0: 2 unblocked; life=38.

P2 (tokens) starts life=38, cards=1, sources=8, power=21
  P2 (tokens) land drop; lands=6.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST buff for 3 mana; 6 left.
    Board buff: +1 power counters to current creatures (simplified lasting effect).
    ATTACK P2 -> P0: 3 unblocked; life=35.
    BLOCK P1 5/5 vs P2 3/3 -> attacker_dead=True, blocker_dead=False.
    BLOCK P3 1/1 vs P2 2/1 -> attacker_dead=True, blocker_dead=True.
    BLOCK P3 1/1 vs P2 2/1 -> attacker_dead=True, blocker_dead=True.
    BLOCK P1 1/3 vs P2 2/1 -> attacker_dead=True, blocker_dead=False.
    ATTACK P2 -> P3: 3 unblocked; life=33.
    ATTACK P2 -> P3: 3 unblocked; life=30.
    ATTACK P2 -> P3: 3 unblocked; life=27.
    ATTACK P2 -> P0: 3 unblocked; life=32.
    BLOCK P1 1/1 vs P2 2/1 -> attacker_dead=True, blocker_dead=True.
    ATTACK P2 -> P1: 2 unblocked; life=31.
    ATTACK P2 -> P1: 2 unblocked; life=29.

P3 (spellslinger) starts life=27, cards=2, sources=7, power=3
  P3 (spellslinger) land drop; lands=7.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST large for 7 mana; 1 left.
    Adds a 9/9 large creature (next turn attacks).
    ATTACK P3 -> P0: 1 unblocked; life=31.
    BLOCK P2 3/3 vs P3 1/1 -> attacker_dead=True, blocker_dead=False.
END ROUND ranks (high to low): P2:tokens (46.0, 38 life) > P1:combo (38.1, 29 life) > P3:spellslinger (27.1, 27 life) > P0:magnus_passive (1.9, 31 life)

===== ROUND 9 =====

P1 (combo) starts life=29, cards=5, sources=8, power=8
  P1 (combo) MISSED land drop; lands=6.
  P1 (combo) CAST ramp for 2 mana; 6 left.
    Permanent ramp +1 mana/turn; next-turn capacity 9.
  P1 (combo) CAST ramp for 3 mana; 3 left.
    Permanent ramp +1 mana/turn; next-turn capacity 10.
    ATTACK P1 -> P2: 2 unblocked; life=36.

P2 (tokens) starts life=36, cards=0, sources=9, power=26
  P2 (tokens) land drop; lands=7.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST tokens for 3 mana; 7 left.
    Generates 4 2/2 creatures.
    BLOCK P3 9/9 vs P2 3/3 -> attacker_dead=True, blocker_dead=False.
    ATTACK P2 -> P0: 3 unblocked; life=28.
    BLOCK P1 5/5 vs P2 3/2 -> attacker_dead=True, blocker_dead=False.
    ATTACK P2 -> P3: 3 unblocked; life=24.
    ATTACK P2 -> P0: 2 unblocked; life=26.
    BLOCK P3 1/1 vs P2 2/1 -> attacker_dead=True, blocker_dead=True.
    BLOCK P1 1/3 vs P2 2/1 -> attacker_dead=True, blocker_dead=False.
    ATTACK P2 -> P0: 2 unblocked; life=24.

P3 (spellslinger) starts life=24, cards=2, sources=8, power=11
  P3 (spellslinger) land drop; lands=8.
  P3 engine generated 1/1 token.
    RESPONSE: P1 (combo) counters P3's small (small threat severity 1.0); 2 mana spent.
  P3 (spellslinger) CAST small for 1 mana; 7 left.
    Adds a 1/2 small creature (next turn attacks).
  P3 (spellslinger) CAST wipe for 6 mana; 1 left.
    WIPE: 19 creatures across all players destroyed.
END ROUND ranks (high to low): P1:combo (28.3, 29 life) > P3:spellslinger (15.1, 24 life) > P2:tokens (13.9, 36 life) > P0:magnus_passive (1.4, 24 life)

===== ROUND 10 =====

P1 (combo) starts life=29, cards=4, sources=10, power=0
  P1 (combo) MISSED land drop; lands=6.
  P1 (combo) CAST draw for 2 mana; 8 left.
    Draws 2 extra abstract cards.
  P1 (combo) CAST engine for 4 mana; 4 left.
    Persistent draw/token engine enters as noncreature permanent.
  P1 (combo) CAST engine for 4 mana; 0 left.
    Persistent draw/token engine enters as noncreature permanent.

P2 (tokens) starts life=36, cards=1, sources=10, power=0
  P2 (tokens) land drop; lands=8.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST tokens for 5 mana; 6 left.
    Generates 2 1/1 creatures.

P3 (spellslinger) starts life=24, cards=0, sources=9, power=0
  P3 (spellslinger) MISSED land drop; lands=8.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST small for 1 mana; 8 left.
    Adds a 2/2 small creature (next turn attacks).
  P3 (spellslinger) CAST finisher for 6 mana; 2 left.
    P2 takes 8 direct damage; life=28.
END ROUND ranks (high to low): P1:combo (34.5, 29 life) > P3:spellslinger (18.6, 24 life) > P2:tokens (18.3, 28 life) > P0:magnus_passive (1.4, 24 life)
```

## No-interaction run — full event trace

```text

===== ROUND 1 =====

P1 (combo) starts life=40, cards=7, sources=0, power=0
  P1 (combo) land drop; lands=1.

P2 (tokens) starts life=40, cards=7, sources=0, power=0
  P2 (tokens) land drop; lands=1.
  P2 (tokens) CAST small for 1 mana; 0 left.
    Adds a 3/2 small creature (next turn attacks).

P3 (spellslinger) starts life=40, cards=7, sources=0, power=0
  P3 (spellslinger) land drop; lands=1.
END ROUND ranks (high to low): P2:tokens (7.9, 40 life) > P3:spellslinger (5.1, 40 life) > P1:combo (5.1, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 2 =====

P1 (combo) starts life=40, cards=7, sources=1, power=0
  P1 (combo) land drop; lands=2.
  P1 (combo) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 3.

P2 (tokens) starts life=40, cards=6, sources=1, power=3
  P2 (tokens) land drop; lands=2.
  P2 (tokens) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 3.

P3 (spellslinger) starts life=40, cards=7, sources=1, power=0
  P3 (spellslinger) land drop; lands=2.
END ROUND ranks (high to low): P2:tokens (9.3, 40 life) > P1:combo (6.5, 40 life) > P3:spellslinger (5.9, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 3 =====

P1 (combo) starts life=40, cards=6, sources=3, power=0
  P1 (combo) land drop; lands=3.
  P1 (combo) CAST engine for 3 mana; 1 left.
    Persistent draw/token engine enters as noncreature permanent.

P2 (tokens) starts life=40, cards=5, sources=3, power=3
  P2 (tokens) land drop; lands=3.
  P2 (tokens) CAST engine for 2 mana; 2 left.
    Persistent draw/token engine enters as noncreature permanent.

P3 (spellslinger) starts life=40, cards=7, sources=2, power=0
  P3 (spellslinger) land drop; lands=3.
  P3 (spellslinger) CAST ramp for 3 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 4.
END ROUND ranks (high to low): P2:tokens (12.9, 40 life) > P1:combo (10.1, 40 life) > P3:spellslinger (7.4, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 4 =====

P1 (combo) starts life=40, cards=5, sources=4, power=0
  P1 (combo) MISSED land drop; lands=3.
  P1 (combo) CAST draw for 2 mana; 2 left.
    Draws 2 extra abstract cards.
  P1 (combo) CAST ramp for 2 mana; 0 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.

P2 (tokens) starts life=40, cards=4, sources=4, power=3
  P2 (tokens) MISSED land drop; lands=3.
  P2 (tokens) CAST engine for 3 mana; 1 left.
    Persistent draw/token engine enters as noncreature permanent.

P3 (spellslinger) starts life=40, cards=6, sources=4, power=0
  P3 (spellslinger) land drop; lands=4.
  P3 (spellslinger) CAST engine for 3 mana; 2 left.
    Persistent draw/token engine enters as noncreature permanent.
END ROUND ranks (high to low): P2:tokens (15.9, 40 life) > P1:combo (11.2, 40 life) > P3:spellslinger (10.9, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 5 =====

P1 (combo) starts life=40, cards=6, sources=5, power=0
  P1 (combo) land drop; lands=4.
  P1 engine generated 1/1 token.
  P1 (combo) CAST draw for 3 mana; 3 left.
    Draws 3 extra abstract cards.
  P1 (combo) CAST draw for 3 mana; 0 left.
    Draws 3 extra abstract cards.

P2 (tokens) starts life=40, cards=4, sources=4, power=3
  P2 (tokens) MISSED land drop; lands=3.
  P2 (tokens) CAST ramp for 2 mana; 2 left.
    Permanent ramp +1 mana/turn; next-turn capacity 5.
  P2 (tokens) CAST small for 1 mana; 1 left.
    Adds a 1/1 small creature (next turn attacks).

P3 (spellslinger) starts life=40, cards=5, sources=5, power=0
  P3 (spellslinger) land drop; lands=5.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST engine for 4 mana; 2 left.
    Persistent draw/token engine enters as 2/3 creature.
END ROUND ranks (high to low): P3:spellslinger (18.4, 40 life) > P2:tokens (18.4, 40 life) > P1:combo (13.7, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 6 =====

P1 (combo) starts life=40, cards=7, sources=6, power=1
  P1 (combo) land drop; lands=5.
  P1 (combo) CAST engine for 4 mana; 3 left.
    Persistent draw/token engine enters as 2/3 creature.
  P1 (combo) CAST draw for 3 mana; 0 left.
    Draws 3 extra abstract cards.

P2 (tokens) starts life=40, cards=5, sources=5, power=4
  P2 (tokens) land drop; lands=4.
  P2 (tokens) CAST engine for 3 mana; 3 left.
    Persistent draw/token engine enters as noncreature permanent.
  P2 (tokens) CAST tokens for 3 mana; 0 left.
    Generates 4 2/2 creatures.

P3 (spellslinger) starts life=40, cards=5, sources=6, power=3
  P3 (spellslinger) land drop; lands=6.
  P3 (spellslinger) CAST tokens for 4 mana; 3 left.
    Generates 3 2/2 creatures.
  P3 (spellslinger) CAST burn for 3 mana; 0 left.
END ROUND ranks (high to low): P2:tokens (31.0, 40 life) > P3:spellslinger (25.5, 40 life) > P1:combo (19.7, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 7 =====

P1 (combo) starts life=40, cards=7, sources=7, power=3
  P1 (combo) land drop; lands=6.
  P1 (combo) CAST combo_piece for 3 mana; 5 left.
    Combo setup pieces now 1.
  P1 (combo) CAST medium for 3 mana; 2 left.
    Adds a 4/5 medium creature (next turn attacks).

P2 (tokens) starts life=40, cards=5, sources=6, power=12
  P2 (tokens) land drop; lands=5.
  P2 (tokens) CAST engine for 4 mana; 3 left.
    Persistent draw/token engine enters as noncreature permanent.
  P2 (tokens) CAST tokens for 3 mana; 0 left.
    Generates 2 1/1 creatures.

P3 (spellslinger) starts life=40, cards=4, sources=7, power=9
  P3 (spellslinger) land drop; lands=7.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST engine for 3 mana; 5 left.
    Persistent draw/token engine enters as noncreature permanent.
  P3 (spellslinger) CAST tokens for 4 mana; 1 left.
    Generates 3 1/1 creatures.
END ROUND ranks (high to low): P2:tokens (37.5, 40 life) > P3:spellslinger (34.5, 40 life) > P1:combo (31.2, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 8 =====

P1 (combo) starts life=40, cards=6, sources=8, power=7
  P1 (combo) MISSED land drop; lands=6.
  P1 (combo) CAST combo_piece for 2 mana; 6 left.
    Combo setup pieces now 2.
  P1 (combo) CAST small for 1 mana; 5 left.
    Adds a 1/1 small creature (next turn attacks).
  P1 (combo) CAST finisher for 5 mana; 0 left.
    ABSTRACT COMBO WIN ATTEMPT by P1; record only (not resolved as win).

P2 (tokens) starts life=40, cards=5, sources=7, power=14
  P2 (tokens) land drop; lands=6.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST tokens for 5 mana; 3 left.
    Generates 2 1/1 creatures.
  P2 (tokens) CAST buff for 2 mana; 1 left.
    Board buff: +2 power counters to current creatures (simplified lasting effect).

P3 (spellslinger) starts life=40, cards=3, sources=8, power=13
  P3 (spellslinger) land drop; lands=8.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST large for 7 mana; 2 left.
    Adds a 7/6 large creature (next turn attacks).
  P3 (spellslinger) CAST small for 1 mana; 1 left.
    Adds a 3/3 small creature (next turn attacks).
END ROUND ranks (high to low): P2:tokens (61.1, 40 life) > P3:spellslinger (46.0, 40 life) > P1:combo (39.3, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 9 =====

P1 (combo) starts life=40, cards=5, sources=8, power=8
  P1 (combo) MISSED land drop; lands=6.
  P1 (combo) CAST ramp for 2 mana; 6 left.
    Permanent ramp +1 mana/turn; next-turn capacity 9.
  P1 (combo) CAST ramp for 3 mana; 3 left.
    Permanent ramp +1 mana/turn; next-turn capacity 10.

P2 (tokens) starts life=40, cards=5, sources=8, power=39
  P2 (tokens) land drop; lands=7.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST tokens for 5 mana; 4 left.
    Generates 3 1/1 creatures.
  P2 (tokens) CAST buff for 3 mana; 1 left.
    Board buff: +1 power counters to current creatures (simplified lasting effect).

P3 (spellslinger) starts life=40, cards=2, sources=9, power=24
  P3 (spellslinger) MISSED land drop; lands=8.
  P3 engine generated 1/1 token.
  P3 (spellslinger) CAST small for 1 mana; 8 left.
    Adds a 2/3 small creature (next turn attacks).
  P3 (spellslinger) CAST small for 1 mana; 7 left.
    Adds a 3/2 small creature (next turn attacks).
  P3 (spellslinger) CAST finisher for 6 mana; 1 left.
END ROUND ranks (high to low): P2:tokens (79.9, 40 life) > P3:spellslinger (52.6, 40 life) > P1:combo (41.0, 40 life) > P0:magnus_passive (2.4, 40 life)

===== ROUND 10 =====

P1 (combo) starts life=40, cards=5, sources=10, power=8
  P1 (combo) MISSED land drop; lands=6.
  P1 engine generated 1/1 token.
  P1 (combo) CAST engine for 4 mana; 6 left.
    Persistent draw/token engine enters as 2/3 creature.
  P1 (combo) CAST draw for 2 mana; 4 left.
    Draws 3 extra abstract cards.
  P1 (combo) CAST engine for 4 mana; 0 left.
    Persistent draw/token engine enters as 2/3 creature.

P2 (tokens) starts life=40, cards=4, sources=9, power=58
  P2 (tokens) land drop; lands=8.
  P2 engine generated 1/1 token.
  P2 (tokens) CAST engine for 4 mana; 6 left.
    Persistent draw/token engine enters as noncreature permanent.
  P2 (tokens) CAST tokens for 4 mana; 2 left.
    Generates 3 1/1 creatures.

P3 (spellslinger) starts life=40, cards=2, sources=9, power=30
  P3 (spellslinger) land drop; lands=9.
  P3 engine generated 1/1 token.
END ROUND ranks (high to low): P2:tokens (88.9, 40 life) > P3:spellslinger (55.3, 40 life) > P1:combo (53.3, 40 life) > P0:magnus_passive (2.4, 40 life)
```