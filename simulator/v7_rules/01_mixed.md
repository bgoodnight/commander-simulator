# V7 narrated test: 01_mixed
**Seed:** 102  · **Opponents:** aggro, control, combo  · **Opening:** natural
**Result:** turn_limit; winner None; rounds 10
**Magnus:** 19 life; 9 spells; commander cast 2×; 2 creature tokens.
**V7 rules:** 4 trigger instances; 39 cost checks; safety stop = none.

## Round-level state
| Round | Magnus life / tokens / spells cast | Others life (P1/P2/P3) |
|---:|---|---|
| 1 | 40 / 0 / 0 | 40 / 40 / 40 |
| 2 | 40 / 0 / 1 | 40 / 39 / 40 |
| 3 | 36 / 0 / 2 | 40 / 36 / 40 |
| 4 | 36 / 0 / 3 | 40 / 33 / 40 |
| 5 | 36 / 1 / 4 | 40 / 27 / 40 |
| 6 | 33 / 3 / 6 | 40 / 27 / 37 |
| 7 | 30 / 3 / 7 | 40 / 27 / 33 |
| 8 | 26 / 4 / 8 | 40 / 27 / 28 |
| 9 | 20 / 3 / 9 | 40 / 27 / 28 |
| 10 | 19 / 2 / 9 | 40 / 27 / 21 |

## Full action narrative
```text

========== ROUND 1 ==========
  P2 land -> 1 lands.
  P1 land -> 1 lands.
  P1 (aggro) casts small creature [creature] cost 1, mana left 0.
  P3 land -> 1 lands.
  P0 plays Island (1 lands).
  End round: P0 magnus life=40 board=0 sources=1, P1 aggro life=40 board=1 sources=1, P2 control life=40 board=0 sources=1, P3 combo life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 0.
  P1 land -> 2 lands.
  P1 (aggro) casts small creature [creature] cost 2, mana left 0.
    COMBAT P1 aggro:small:8 attacks P2 unblocked for 1.
  P3 land -> 2 lands.
  P3 (combo) casts ramp artifact [ramp] cost 2, mana left 0.
  P0 plays Sokenzan, Crucible of Defiance (2 lands).
  P0 (magnus) casts Third Path Iconoclast creature [named_creature] cost 2, mana left 0.
    Third Path Iconoclast enters battlefield (1/1).
  End round: P0 magnus life=40 board=1 sources=2, P1 aggro life=40 board=3 sources=2, P2 control life=39 board=0 sources=2, P3 combo life=40 board=0 sources=3

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (control) casts engine enchantment [engine] cost 3, mana left 0.
  P1 land -> 3 lands.
  P1 (aggro) casts buff sorcery [buff] cost 2, mana left 1.
    COMBAT P1 aggro:small:8 attacks P2 unblocked for 3.
    COMBAT P1 aggro:small:4 attacks P0 unblocked for 4.
  P3 land -> 3 lands.
  P3 (combo) casts engine enchantment [engine] cost 2, mana left 2.
  P3 (combo) casts draw sorcery [draw] cost 2, mana left 0.
  P0 plays Mountain (3 lands).
  P0 (magnus) casts Goblin Electromancer creature [named_creature] cost 2, mana left 1.
    Goblin Electromancer enters battlefield (2/2).
  End round: P0 magnus life=36 board=3 sources=3, P1 aggro life=40 board=7 sources=3, P2 control life=36 board=0 sources=3, P3 combo life=40 board=2 sources=4

========== ROUND 4 ==========
  P2 land -> 4 lands.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 2.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 0.
  P1 land -> 4 lands.
  P1 (aggro) casts medium creature [creature] cost 4, mana left 0.
    COMBAT P1 aggro:small:8 attacks P2 unblocked for 3.
    COMBAT P1 aggro:small:4 4/1 into P3 combo:engine:3 2/3.
  P3 land -> 4 lands.
  P3 (combo) casts ramp artifact [ramp] cost 2, mana left 3.
  P0 misses land drop.
  P0 (magnus) casts Baral, Chief of Compliance creature [named_creature] cost 2, mana left 1.
    Baral, Chief of Compliance enters battlefield (1/3).
  End round: P0 magnus life=36 board=4 sources=3, P1 aggro life=40 board=6 sources=4, P2 control life=33 board=1 sources=4, P3 combo life=40 board=0 sources=6

========== ROUND 5 ==========
  P2 land -> 5 lands.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 3.
  P2 (control) casts draw sorcery [draw] cost 3, mana left 0.
  P1 (aggro) casts medium creature [creature] cost 4, mana left 0.
    COMBAT P1 aggro:small:8 attacks P2 unblocked for 3.
    COMBAT P1 aggro:medium:1 attacks P2 unblocked for 3.
  P3 land -> 5 lands.
  P3 (combo) casts engine enchantment [engine] cost 4, mana left 3.
  P0 misses land drop.
  P0 (magnus) casts Izzet Signet artifact [named_rock] cost 2, mana left 1.
    Izzet Signet increases available mana next turn.
  End round: P0 magnus life=36 board=5 sources=4, P1 aggro life=40 board=9 sources=4, P2 control life=27 board=2 sources=5, P3 combo life=40 board=0 sources=7

========== ROUND 6 ==========
  P2 land -> 6 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 4.
  P2 (control) casts engine enchantment [engine] cost 4, mana left 0.
    P3 counters control:engine:7 with combo:counter:4.
  P1 (aggro) casts medium creature [creature] cost 4, mana left 0.
    COMBAT P1 aggro:small:8 attacks P0 unblocked for 3.
    COMBAT P1 aggro:medium:0 attacks P3 unblocked for 3.
  P3 land -> 6 lands.
  P3 (combo) casts ramp artifact [ramp] cost 3, mana left 5.
  P0 misses land drop.
  P0 (magnus) casts Pongify instant [named_pongify] cost 1, mana left 4.
    Pongify destroys aggro:medium:3; P1 gets a 3/3 Ape.
  P0 (magnus) casts Impulse instant [named_selection] cost 1, mana left 2.
    Impulse: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=33 board=7 sources=4, P1 aggro life=40 board=12 sources=4, P2 control life=27 board=6 sources=6, P3 combo life=37 board=0 sources=9

========== ROUND 7 ==========
  P2 land -> 7 lands.
  P2 (control) casts medium creature [creature] cost 4, mana left 3.
    COMBAT P2 engine token attacks P3 unblocked for 1.
  P1 (aggro) casts tokens sorcery [tokens] cost 4, mana left 0.
    COMBAT P1 aggro:small:8 attacks P3 unblocked for 3.
    COMBAT P1 aggro:medium:0 attacks P0 unblocked for 3.
    COMBAT P1 Ape (Pongify) 3/3 into P2 control:medium:4 3/3.
  P3 land -> 7 lands.
  P3 (combo) casts ramp artifact [ramp] cost 3, mana left 7.
  P3 (combo) casts large creature [creature] cost 6, mana left 1.
  P0 plays Island (4 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 5, mana left 0.
    P2 counters Magnus the Red with control:counter:6.
  End round: P0 magnus life=30 board=7 sources=5, P1 aggro life=40 board=11 sources=4, P2 control life=27 board=6 sources=7, P3 combo life=33 board=6 sources=11

========== ROUND 8 ==========
  P2 land -> 8 lands.
  P2 (control) casts large creature [creature] cost 5, mana left 3.
  P2 (control) casts small creature [creature] cost 1, mana left 2.
    COMBAT P2 engine token attacks P0 unblocked for 1.
    COMBAT P2 engine token 1/1 into P3 combo:large:1 6/6.
    COMBAT P2 engine token attacks P3 unblocked for 1.
  P1 land -> 5 lands.
  P1 (aggro) casts draw sorcery [draw] cost 2, mana left 3.
    P2 counters aggro:draw:2 with control:counter:2.
  P1 (aggro) casts engine enchantment [engine] cost 3, mana left 0.
    COMBAT P1 aggro:small:8 attacks P0 unblocked for 3.
    COMBAT P1 aggro:medium:1 3/2 into P3 combo:large:1 6/6.
    COMBAT P1 aggro:medium:0 attacks P3 unblocked for 3.
    COMBAT P1 Token 1/1 into P2 control:engine:9 2/3.
    COMBAT P1 Token attacks P3 unblocked for 1.
  P3 land -> 8 lands.
  P3 (combo) casts engine enchantment [engine] cost 2, mana left 10.
  P0 plays Island (5 lands).
  P0 (magnus) casts Brainstorm instant [named_selection] cost 1, mana left 6.
    Brainstorm: partial card selection (3 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=26 board=8 sources=6, P1 aggro life=40 board=7 sources=5, P2 control life=27 board=13 sources=8, P3 combo life=28 board=7 sources=12

========== ROUND 9 ==========
  P2 land -> 9 lands.
    COMBAT P2 engine token 1/1 into P3 combo:large:1 6/6.
    COMBAT P2 control:large:0 attacks P0 unblocked for 6.
  P1 (aggro) casts medium creature [creature] cost 4, mana left 1.
    COMBAT P1 aggro:small:8 3/3 into P2 control:large:0 6/7.
    COMBAT P1 Token 1/1 into P2 control:engine:9 2/3.
  P3 land -> 9 lands.
  P3 (combo) casts engine enchantment [engine] cost 3, mana left 10.
    COMBAT P3 combo:large:1 6/6 into P2 control:large:0 6/7.
  P0 plays Sulfur Falls (6 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 7, mana left 0.
    Magnus the Red enters battlefield (4/5).
    COMBAT P0 Soldier 1/1 into P3 engine token 1/1.
  End round: P0 magnus life=20 board=11 sources=7, P1 aggro life=40 board=8 sources=5, P2 control life=27 board=14 sources=9, P3 combo life=28 board=0 sources=13

========== ROUND 10 ==========
  P2 land -> 10 lands.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 8.
  P2 (control) casts ramp artifact [ramp] cost 2, mana left 6.
  P2 (control) casts removal instant [remove] cost 3, mana left 3.
    COMBAT P2 engine token attacks P0 unblocked for 1.
  P1 (aggro) casts small creature [creature] cost 1, mana left 4.
  P1 (aggro) casts small creature [creature] cost 2, mana left 2.
    COMBAT P1 aggro:medium:0 attacks P3 unblocked for 3.
    COMBAT P1 engine token 1/1 into P2 control:engine:9 2/3.
    COMBAT P1 aggro:medium:5 attacks P3 unblocked for 4.
  P3 land -> 10 lands.
  P3 (combo) casts tokens sorcery [tokens] cost 3, mana left 11.
    P2 counters combo:tokens:0 with control:counter:4.
  P3 (combo) casts ramp artifact [ramp] cost 2, mana left 9.
  P0 misses land drop.
    COMBAT P0 Soldier 1/1 into P3 engine token 1/1.
  End round: P0 magnus life=19 board=6 sources=7, P1 aggro life=40 board=13 sources=5, P2 control life=27 board=15 sources=11, P3 combo life=21 board=1 sources=15
```

## Important scope note
This is a synthetic mixed-table diagnostic, not a validated Magnus win-rate game. The v7 rules kernel currently centralizes cost/trigger/keyword/target primitives via an adapter. The full stack, commander damage, exact card effects, and opponent card behavior remain unfinished.
