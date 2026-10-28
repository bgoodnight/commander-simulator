# V7 narrated test: 02_pressure
**Seed:** 104  · **Opponents:** aggro, tokens, ramp_stompy  · **Opening:** natural
**Result:** combat; winner 3; rounds 10
**Magnus:** -5 life; 4 spells; commander cast 1×; 0 creature tokens.
**V7 rules:** 4 trigger instances; 3 cost checks; safety stop = none.

## Round-level state
| Round | Magnus life / tokens / spells cast | Others life (P1/P2/P3) |
|---:|---|---|
| 1 | 40 / 0 / 1 | 40 / 40 / 40 |
| 2 | 39 / 0 / 2 | 40 / 40 / 40 |
| 3 | 39 / 0 / 2 | 40 / 36 / 40 |
| 4 | 39 / 0 / 2 | 40 / 36 / 36 |
| 5 | 34 / 0 / 3 | 40 / 27 / 36 |
| 6 | 22 / 1 / 3 | 40 / 23 / 31 |
| 7 | 17 / 1 / 3 | 40 / 13 / 29 |
| 8 | 6 / 2 / 4 | 36 / 13 / 29 |
| 9 | -5 / 0 / 4 | 18 / -6 / 25 |
| 10 | -5 / 0 / 4 | 0 / -6 / 25 |

## Full action narrative
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P1 (aggro) casts small creature [creature] cost 1, mana left 0.
  P0 plays Island (1 lands).
  P0 (magnus) casts Brainstorm instant [named_selection] cost 1, mana left 0.
    Brainstorm: partial card selection (3 cards drawn; exact look/scry not modeled).
  P3 land -> 1 lands.
  P2 land -> 1 lands.
  End round: P0 magnus life=40 board=0 sources=1, P1 aggro life=40 board=1 sources=1, P2 tokens life=40 board=0 sources=1, P3 ramp_stompy life=40 board=0 sources=1

========== ROUND 2 ==========
  P1 land -> 2 lands.
  P1 (aggro) casts small creature [creature] cost 2, mana left 0.
    COMBAT P1 aggro:small:14 attacks P0 unblocked for 1.
  P0 plays Mountain (2 lands).
  P0 (magnus) casts Pongify instant [named_pongify] cost 1, mana left 1.
    Pongify destroys aggro:small:14; P1 gets a 3/3 Ape.
  P3 land -> 2 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 2, mana left 0.
  P2 land -> 2 lands.
  P2 (tokens) casts ramp artifact [ramp] cost 2, mana left 0.
  End round: P0 magnus life=39 board=0 sources=2, P1 aggro life=40 board=4 sources=2, P2 tokens life=40 board=0 sources=3, P3 ramp_stompy life=40 board=0 sources=3

========== ROUND 3 ==========
  P1 land -> 3 lands.
  P1 (aggro) casts small creature [creature] cost 1, mana left 2.
  P1 (aggro) casts buff sorcery [buff] cost 2, mana left 0.
    COMBAT P1 Ape (Pongify) attacks P2 unblocked for 4.
  P0 plays Stormcarved Coast (3 lands).
  P3 land -> 3 lands.
  P3 (ramp_stompy) casts engine enchantment [engine] cost 4, mana left 0.
  P2 land -> 3 lands.
  P2 (tokens) casts engine enchantment [engine] cost 2, mana left 2.
  P2 (tokens) casts small creature [creature] cost 2, mana left 0.
  End round: P0 magnus life=39 board=0 sources=3, P1 aggro life=40 board=8 sources=3, P2 tokens life=36 board=5 sources=4, P3 ramp_stompy life=40 board=0 sources=4

========== ROUND 4 ==========
  P1 (aggro) casts medium creature [creature] cost 3, mana left 0.
    COMBAT P1 aggro:small:13 2/2 into P2 tokens:engine:1 2/3.
    COMBAT P1 Ape (Pongify) attacks P3 unblocked for 4.
    COMBAT P1 aggro:small:10 2/3 into P2 tokens:small:0 3/1.
  P0 plays Command Tower (4 lands).
  P3 land -> 4 lands.
  P3 (ramp_stompy) casts medium creature [creature] cost 4, mana left 1.
  P2 (tokens) casts engine enchantment [engine] cost 3, mana left 1.
    COMBAT P2 tokens:engine:1 2/3 into P3 ramp_stompy:medium:6 4/3.
  End round: P0 magnus life=39 board=0 sources=4, P1 aggro life=40 board=9 sources=3, P2 tokens life=36 board=0 sources=4, P3 ramp_stompy life=36 board=5 sources=5

========== ROUND 5 ==========
  P1 land -> 4 lands.
  P1 (aggro) casts medium creature [creature] cost 3, mana left 1.
    COMBAT P1 Ape (Pongify) attacks P0 unblocked for 4.
    COMBAT P1 aggro:medium:1 attacks P2 unblocked for 5.
  P0 plays Riptide Laboratory (5 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 5, mana left 0.
    Magnus the Red enters battlefield (4/5).
  P3 land -> 5 lands.
  P3 (ramp_stompy) casts medium creature [creature] cost 4, mana left 2.
    COMBAT P3 engine token attacks P0 unblocked for 1.
    COMBAT P3 ramp_stompy:medium:6 attacks P2 unblocked for 4.
  P2 land -> 4 lands.
  P2 (tokens) casts tokens sorcery [tokens] cost 5, mana left 0.
  End round: P0 magnus life=34 board=4 sources=5, P1 aggro life=40 board=14 sources=4, P2 tokens life=27 board=4 sources=5, P3 ramp_stompy life=36 board=9 sources=6

========== ROUND 6 ==========
  P1 land -> 5 lands.
  P1 (aggro) casts tokens sorcery [tokens] cost 4, mana left 1.
    COMBAT P1 Ape (Pongify) 4/3 into P3 ramp_stompy:medium:6 4/3.
    COMBAT P1 aggro:medium:1 attacks P0 unblocked for 5.
    COMBAT P1 aggro:medium:5 attacks P3 unblocked for 5.
  P0 plays Riverglide Pathway (6 lands).
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
  P3 land -> 6 lands.
  P3 (ramp_stompy) casts large creature [creature] cost 7, mana left 0.
    COMBAT P3 engine token 1/1 into P2 Token 1/1.
    COMBAT P3 ramp_stompy:medium:1 attacks P0 unblocked for 4.
  P2 land -> 5 lands.
  P2 (tokens) casts buff sorcery [buff] cost 3, mana left 3.
  P2 (tokens) casts removal instant [remove] cost 2, mana left 1.
    COMBAT P2 Token attacks P0 unblocked for 3.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:medium:1 4/4.
  End round: P0 magnus life=22 board=7 sources=6, P1 aggro life=40 board=13 sources=5, P2 tokens life=23 board=9 sources=6, P3 ramp_stompy life=31 board=10 sources=7

========== ROUND 7 ==========
  P1 land -> 6 lands.
  P1 (aggro) casts engine enchantment [engine] cost 2, mana left 4.
    COMBAT P1 aggro:medium:5 5/5 into P3 ramp_stompy:large:4 6/6.
    COMBAT P1 Token 2/2 into P2 Token 3/1.
    COMBAT P1 Token 2/2 into P3 ramp_stompy:medium:1 4/4.
    COMBAT P1 Token attacks P0 unblocked for 2.
    COMBAT P1 Token attacks P3 unblocked for 2.
  P0 misses land drop.
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    COMBAT P0 Spawn 3/3 into P2 Token 3/1.
  P3 land -> 7 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 2, mana left 6.
  P3 (ramp_stompy) casts large creature [creature] cost 5, mana left 1.
    COMBAT P3 ramp_stompy:large:4 attacks P2 unblocked for 6.
  P2 (tokens) casts engine enchantment [engine] cost 2, mana left 4.
  P2 (tokens) casts removal instant [remove] cost 3, mana left 1.
    COMBAT P2 engine token attacks P0 unblocked for 3.
  End round: P0 magnus life=17 board=7 sources=6, P1 aggro life=40 board=2 sources=6, P2 tokens life=13 board=4 sources=6, P3 ramp_stompy life=29 board=17 sources=10

========== ROUND 8 ==========
  P1 land -> 7 lands.
  P1 (aggro) casts tokens sorcery [tokens] cost 4, mana left 3.
    COMBAT P1 Token 2/2 into P3 ramp_stompy:medium:1 4/4.
  P0 misses land drop.
  P0 (magnus) casts Baral, Chief of Compliance creature [named_creature] cost 2, mana left 4.
    Baral, Chief of Compliance enters battlefield (1/3).
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
  P3 land -> 8 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 8.
  P3 (ramp_stompy) casts medium creature [creature] cost 4, mana left 4.
  P3 (ramp_stompy) casts tokens sorcery [tokens] cost 3, mana left 1.
    COMBAT P3 ramp_stompy:medium:1 attacks P0 unblocked for 4.
    COMBAT P3 ramp_stompy:large:2 attacks P0 unblocked for 7.
  P2 land -> 6 lands.
  P2 (tokens) casts small creature [creature] cost 2, mana left 5.
    COMBAT P2 engine token 3/1 into P3 ramp_stompy:medium:1 4/4.
  End round: P0 magnus life=6 board=11 sources=6, P1 aggro life=36 board=5 sources=7, P2 tokens life=13 board=2 sources=7, P3 ramp_stompy life=29 board=26 sources=13

========== ROUND 9 ==========
  P1 (aggro) casts medium creature [creature] cost 4, mana left 3.
    COMBAT P1 engine token attacks P0 unblocked for 1.
    COMBAT P1 Token 1/1 into P3 Token 2/2.
    COMBAT P1 Token attacks P0 unblocked for 1.
    COMBAT P1 Token attacks P0 unblocked for 1.
    COMBAT P1 Token attacks P0 unblocked for 1.
  P0 misses land drop.
    COMBAT P0 Magnus the Red attacks P3 unblocked for 4.
    COMBAT P0 Spawn 3/3 into P1 aggro:medium:4 3/2.
  P3 (ramp_stompy) casts finisher sorcery [finisher] cost 5, mana left 8.
    P3 overrun grants +3 power permanently (simplified).
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 5.
  P3 (ramp_stompy) casts removal instant [remove] cost 2, mana left 3.
    COMBAT P3 ramp_stompy:medium:1 attacks P0 unblocked for 7.
    ELIMINATED P0 (magnus) round 9: combat.
    COMBAT P3 ramp_stompy:large:4 attacks P2 unblocked for 9.
    COMBAT P3 ramp_stompy:large:2 attacks P2 unblocked for 10.
    ELIMINATED P2 (tokens) round 9: combat.
    COMBAT P3 ramp_stompy:medium:4 attacks P1 unblocked for 8.
    COMBAT P3 Token attacks P1 unblocked for 5.
    COMBAT P3 Token attacks P1 unblocked for 5.
  End round: P1 aggro life=18 board=4 sources=7, P3 ramp_stompy life=25 board=48 sources=14

========== ROUND 10 ==========
  P1 land -> 8 lands.
  P1 (aggro) casts large creature [creature] cost 7, mana left 1.
    COMBAT P1 Token 1/1 into P3 Token 5/2.
    COMBAT P1 Token 1/1 into P3 Token 5/2.
    COMBAT P1 Token 1/1 into P3 ramp_stompy:medium:1 7/4.
    COMBAT P1 engine token 1/1 into P3 ramp_stompy:medium:4 8/5.
  P3 land -> 9 lands.
  P3 (ramp_stompy) casts draw sorcery [draw] cost 3, mana left 12.
  P3 (ramp_stompy) casts draw sorcery [draw] cost 3, mana left 9.
  P3 (ramp_stompy) casts engine enchantment [engine] cost 3, mana left 6.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 3.
    COMBAT P3 ramp_stompy:large:4 9/6 into P1 aggro:large:0 9/5.
    COMBAT P3 ramp_stompy:large:2 attacks P1 unblocked for 10.
    COMBAT P3 ramp_stompy:medium:4 attacks P1 unblocked for 8.
    ELIMINATED P1 (aggro) round 10: combat.
  End round: P3 ramp_stompy life=25 board=42 sources=16
```

## Important scope note
This is a synthetic mixed-table diagnostic, not a validated Magnus win-rate game. The v7 rules kernel currently centralizes cost/trigger/keyword/target primitives via an adapter. The full stack, commander damage, exact card effects, and opponent card behavior remain unfinished.
