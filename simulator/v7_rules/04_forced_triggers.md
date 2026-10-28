# V7 narrated test: 04_forced_triggers
**Seed:** 404  · **Opponents:** control, combo, tokens  · **Opening:** FORCED test fixture
**Result:** turn_limit; winner None; rounds 10
**Magnus:** 28 life; 7 spells; commander cast 1×; 7 creature tokens.
**V7 rules:** 9 trigger instances; 16 cost checks; safety stop = none.

## Round-level state
| Round | Magnus life / tokens / spells cast | Others life (P1/P2/P3) |
|---:|---|---|
| 1 | 40 / 0 / 1 | 40 / 40 / 40 |
| 2 | 40 / 0 / 2 | 40 / 40 / 40 |
| 3 | 40 / 2 / 4 | 40 / 40 / 40 |
| 4 | 38 / 2 / 5 | 40 / 40 / 40 |
| 5 | 36 / 5 / 6 | 36 / 40 / 40 |
| 6 | 32 / 6 / 6 | 36 / 40 / 36 |
| 7 | 30 / 6 / 6 | 33 / 33 / 36 |
| 8 | 28 / 7 / 7 | 32 / 29 / 36 |
| 9 | 28 / 7 / 7 | 22 / 29 / 31 |
| 10 | 28 / 7 / 7 | 16 / 29 / 28 |

## Full action narrative
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  P3 land -> 1 lands.
  P0 plays Mountain (1 lands).
  P0 (magnus) casts Sol Ring artifact [named_rock] cost 1, mana left 0.
    Sol Ring increases available mana next turn.
  End round: P0 magnus life=40 board=0 sources=3, P1 control life=40 board=0 sources=1, P2 combo life=40 board=0 sources=1, P3 tokens life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (combo) casts engine enchantment [engine] cost 2, mana left 0.
  P3 land -> 2 lands.
  P0 plays Island (2 lands).
  P0 (magnus) casts Young Pyromancer creature [named_creature] cost 2, mana left 2.
    Young Pyromancer enters battlefield (2/1).
  End round: P0 magnus life=40 board=2 sources=4, P1 control life=40 board=0 sources=1, P2 combo life=40 board=2 sources=2, P3 tokens life=40 board=0 sources=2

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (combo) casts engine enchantment [engine] cost 3, mana left 0.
  P3 land -> 3 lands.
  P0 plays Spirebluff Canal (3 lands).
  P0 (magnus) casts Harmonic Prodigy creature [named_creature] cost 2, mana left 3.
    Harmonic Prodigy enters battlefield (1/3).
  P0 (magnus) casts Ponder sorcery [named_selection] cost 1, mana left 2.
    Ponder: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=40 board=5 sources=5, P1 control life=40 board=0 sources=1, P2 combo life=40 board=5 sources=3, P3 tokens life=40 board=0 sources=3

========== ROUND 4 ==========
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 1.
    COMBAT P2 combo:engine:7 attacks P0 unblocked for 2.
  P3 land -> 4 lands.
  P3 (tokens) casts engine enchantment [engine] cost 4, mana left 0.
  P0 plays Mountain (4 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 5, mana left 1.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=38 board=9 sources=6, P1 control life=40 board=0 sources=1, P2 combo life=40 board=5 sources=3, P3 tokens life=40 board=0 sources=4

========== ROUND 5 ==========
  P2 land -> 4 lands.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 2.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 0.
    COMBAT P2 combo:engine:2 attacks P0 unblocked for 2.
  P3 land -> 5 lands.
  P3 (tokens) casts engine enchantment [engine] cost 4, mana left 1.
  P3 (tokens) casts small creature [creature] cost 1, mana left 0.
  P0 plays Mountain (5 lands).
  P0 (magnus) casts Preordain sorcery [named_selection] cost 1, mana left 6.
    Preordain: partial card selection (1 cards drawn; exact look/scry not modeled).
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
  End round: P0 magnus life=36 board=14 sources=7, P1 control life=36 board=0 sources=1, P2 combo life=40 board=5 sources=6, P3 tokens life=40 board=3 sources=5

========== ROUND 6 ==========
  P2 land -> 5 lands.
  P2 (combo) casts ramp artifact [ramp] cost 3, mana left 4.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 2.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT P2 engine token 1/1 into P3 tokens:small:4 3/2.
  P3 land -> 6 lands.
  P3 (tokens) casts engine enchantment [engine] cost 3, mana left 3.
  P3 (tokens) casts buff sorcery [buff] cost 2, mana left 1.
    COMBAT P3 tokens:small:4 attacks P0 unblocked for 4.
  P0 plays Cascade Bluffs (6 lands).
    COMBAT P0 Magnus the Red attacks P3 unblocked for 4.
  End round: P0 magnus life=32 board=17 sources=8, P1 control life=36 board=0 sources=1, P2 combo life=40 board=4 sources=8, P3 tokens life=36 board=4 sources=6

========== ROUND 7 ==========
  P1 land -> 2 lands.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P2 land -> 6 lands.
  P2 (combo) casts draw sorcery [draw] cost 3, mana left 6.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 4.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 2.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 2, mana left 0.
    COMBAT P2 combo:engine:2 attacks P1 unblocked for 2.
    COMBAT P2 combo:engine:7 attacks P0 unblocked for 2.
  P3 (tokens) casts engine enchantment [engine] cost 4, mana left 2.
  P0 plays Island (7 lands).
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    COMBAT P0 Elemental attacks P1 unblocked for 1.
    COMBAT P0 Spawn attacks P2 unblocked for 3.
    COMBAT P0 Spawn 3/3 into P3 tokens:small:4 4/2.
  End round: P0 magnus life=30 board=17 sources=9, P1 control life=33 board=0 sources=3, P2 combo life=33 board=4 sources=11, P3 tokens life=36 board=2 sources=6

========== ROUND 8 ==========
  P1 (control) casts ramp artifact [ramp] cost 3, mana left 0.
  P2 land -> 7 lands.
  P2 (combo) casts draw sorcery [draw] cost 3, mana left 9.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 7.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 3, mana left 4.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 4, mana left 0.
    COMBAT P2 combo:engine:2 attacks P0 unblocked for 2.
  P3 (tokens) casts tokens sorcery [tokens] cost 3, mana left 3.
  P3 (tokens) casts draw sorcery [draw] cost 2, mana left 1.
  P3 (tokens) casts small creature [creature] cost 1, mana left 0.
    COMBAT P3 engine token 1/1 into P2 combo:engine:2 2/3.
  P0 misses land drop.
  P0 (magnus) casts Mind Stone artifact [named_rock] cost 2, mana left 7.
    Mind Stone increases available mana next turn.
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    COMBAT P0 Elemental attacks P1 unblocked for 1.
  End round: P0 magnus life=28 board=20 sources=10, P1 control life=32 board=0 sources=5, P2 combo life=29 board=6 sources=13, P3 tokens life=36 board=5 sources=6

========== ROUND 9 ==========
  P1 land -> 3 lands.
  P1 (control) casts engine enchantment [engine] cost 3, mana left 3.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 1.
  P2 land -> 8 lands.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 12.
  P2 (combo) casts medium creature [creature] cost 3, mana left 9.
  P2 (combo) casts large creature [creature] cost 7, mana left 2.
  P2 (combo) casts removal instant [remove] cost 2, mana left 0.
    COMBAT P2 combo:engine:2 attacks P1 unblocked for 2.
    COMBAT P2 combo:engine:7 attacks P3 unblocked for 2.
    COMBAT P2 engine token 1/1 into P3 tokens:small:1 1/3.
  P3 land -> 7 lands.
  P3 (tokens) casts tokens sorcery [tokens] cost 4, mana left 3.
  P3 (tokens) casts small creature [creature] cost 2, mana left 1.
    COMBAT P3 engine token 1/1 into P2 combo:engine:2 2/3.
    COMBAT P3 engine token attacks P1 unblocked for 1.
    COMBAT P3 Token 1/1 into P2 combo:engine:7 2/3.
    COMBAT P3 Token 1/1 into P2 combo:medium:2 4/3.
    COMBAT P3 tokens:small:1 1/3 into P2 combo:large:0 9/8.
  P0 misses land drop.
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
    COMBAT P0 Spawn attacks P3 unblocked for 3.
    COMBAT P0 Spawn attacks P1 unblocked for 3.
  End round: P0 magnus life=28 board=22 sources=10, P1 control life=22 board=0 sources=6, P2 combo life=29 board=18 sources=14, P3 tokens life=31 board=4 sources=7

========== ROUND 10 ==========
  P1 (control) casts engine enchantment [engine] cost 4, mana left 2.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 0.
  P2 land -> 9 lands.
  P2 (combo) casts removal instant [remove] cost 2, mana left 13.
  P2 (combo) casts large creature [creature] cost 6, mana left 7.
  P3 land -> 8 lands.
  P3 (tokens) casts engine enchantment [engine] cost 2, mana left 6.
  P3 (tokens) casts tokens sorcery [tokens] cost 4, mana left 2.
  P3 (tokens) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT P3 Token 1/1 into P1 control:engine:0 2/3.
    COMBAT P3 tokens:small:3 1/1 into P2 combo:engine:2 2/3.
  P0 plays Island (8 lands).
    COMBAT P0 Spawn attacks P1 unblocked for 3.
    COMBAT P0 Spawn attacks P1 unblocked for 3.
    COMBAT P0 Spawn attacks P3 unblocked for 3.
  End round: P0 magnus life=28 board=22 sources=11, P1 control life=16 board=3 sources=6, P2 combo life=29 board=24 sources=15, P3 tokens life=28 board=8 sources=8
```

## Important scope note
This is a synthetic mixed-table diagnostic, not a validated Magnus win-rate game. The v7 rules kernel currently centralizes cost/trigger/keyword/target primitives via an adapter. The full stack, commander damage, exact card effects, and opponent card behavior remain unfinished.
