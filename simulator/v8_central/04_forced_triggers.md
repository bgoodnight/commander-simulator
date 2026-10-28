# V8 narrated game: 04_forced_triggers
**Seed:** 404 | **Seats:** Magnus vs control, combo, tokens | **Opening:** forced diagnostic
**Result:** turn_limit; winner seat None; Magnus life 28 after 10 rounds

## Player scoreboard
| Seat | Pilot | Life | Casts | Creatures left | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | magnus | 28 | 8 | 5 | 10 |
| 1 | control | 34 | 6 | 2 | 6 |
| 2 | combo | 40 | 21 | 5 | 15 |
| 3 | tokens | 25 | 13 | 5 | 8 |

## Shared-rule diagnostics
- Persistent-kernel vs legacy-view consistency: **True**
- Shared-stack max depth: **1**; countered frames: **0**
- Game-object zone transitions: **15**; simultaneous combat-damage batches: **8**
- Trigger instances: **4**; cost queries: **14**
- Safety stop: **None**
- Magnus unsupported cards held: {'Heralds of Tzeentch': 10, "Jace, Vryn's Prodigy": 10, 'Mathemagics': 9, 'Mana Geyser': 7, 'Reiterate': 5, 'Underworld Breach': 2}

## Round-by-round comparison
| Round | Magnus life | Token count | P1 life | P2 life | P3 life |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 0 | 40 | 40 | 40 |
| 2 | 40 | 0 | 40 | 40 | 40 |
| 3 | 38 | 0 | 40 | 40 | 40 |
| 4 | 38 | 0 | 40 | 40 | 40 |
| 5 | 36 | 0 | 40 | 40 | 40 |
| 6 | 35 | 2 | 40 | 40 | 40 |
| 7 | 33 | 2 | 40 | 40 | 36 |
| 8 | 33 | 2 | 39 | 40 | 36 |
| 9 | 30 | 2 | 37 | 40 | 32 |
| 10 | 28 | 2 | 34 | 40 | 25 |

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  P3 land -> 1 lands.
  P0 plays Island (1 lands).
  P0 (magnus) casts Sol Ring [artifact] for 1; mana=0.
    Sol Ring increases available mana next turn.
  End round: P0 magnus life=40 board=0 sources=3, P1 control life=40 board=0 sources=1, P2 combo life=40 board=0 sources=1, P3 tokens life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (combo) casts combo:engine:2 [enchantment] for 2; mana=0.
  P3 land -> 2 lands.
  P0 misses land drop.
  P0 (magnus) casts Preordain [sorcery] for 1; mana=2.
    Preordain: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=40 board=0 sources=3, P1 control life=40 board=0 sources=1, P2 combo life=40 board=2 sources=2, P3 tokens life=40 board=0 sources=2

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (combo) casts combo:engine:7 [enchantment] for 3; mana=0.
    COMBAT P2 combo:engine:2 hits P0 for 2.
  P3 land -> 3 lands.
  P0 plays Spirebluff Canal (2 lands).
  P0 (magnus) casts Young Pyromancer [creature] for 2; mana=2.
    Young Pyromancer enters battlefield (2/1).
  End round: P0 magnus life=38 board=2 sources=4, P1 control life=40 board=0 sources=1, P2 combo life=40 board=5 sources=3, P3 tokens life=40 board=0 sources=3

========== ROUND 4 ==========
  P2 (combo) casts combo:draw:8 [sorcery] for 2; mana=1.
  P3 land -> 4 lands.
  P3 (tokens) casts tokens:engine:2 [enchantment] for 4; mana=0.
  P0 plays Mountain (3 lands).
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=3.
    Harmonic Prodigy enters battlefield (1/3).
  End round: P0 magnus life=38 board=3 sources=5, P1 control life=40 board=0 sources=1, P2 combo life=40 board=5 sources=3, P3 tokens life=40 board=0 sources=4

========== ROUND 5 ==========
  P2 land -> 4 lands.
  P2 (combo) casts combo:draw:10 [sorcery] for 2; mana=2.
  P2 (combo) casts combo:ramp:6 [artifact] for 2; mana=0.
    COMBAT P2 combo:engine:7 hits P0 for 2.
  P3 land -> 5 lands.
  P3 (tokens) casts tokens:engine:8 [enchantment] for 4; mana=1.
  P3 (tokens) casts tokens:small:4 [creature] for 1; mana=0.
  P0 plays Mountain (4 lands).
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=1.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=36 board=7 sources=6, P1 control life=40 board=0 sources=1, P2 combo life=40 board=6 sources=6, P3 tokens life=40 board=3 sources=5

========== ROUND 6 ==========
  P2 land -> 5 lands.
  P2 (combo) casts combo:ramp:4 [artifact] for 3; mana=4.
  P2 (combo) casts combo:draw:3 [sorcery] for 2; mana=2.
  P2 (combo) casts combo:draw:9 [sorcery] for 2; mana=0.
    COMBAT P2 engine token hits P0 for 1.
  P3 land -> 6 lands.
  P3 (tokens) casts tokens:engine:1 [enchantment] for 3; mana=3.
  P3 (tokens) casts tokens:buff:3 [sorcery] for 2; mana=1.
    COMBAT P3 tokens:small:4 4/2 into P2 combo:engine:2 2/3.
  P0 misses land drop.
  P0 (magnus) casts Ponder [sorcery] for 1; mana=5.
    Ponder: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=35 board=9 sources=6, P1 control life=40 board=0 sources=1, P2 combo life=40 board=4 sources=8, P3 tokens life=40 board=0 sources=6

========== ROUND 7 ==========
  P1 land -> 2 lands.
  P1 (control) casts control:ramp:1 [artifact] for 2; mana=0.
  P2 land -> 6 lands.
  P2 (combo) casts combo:draw:0 [sorcery] for 3; mana=6.
  P2 (combo) casts combo:ramp:7 [artifact] for 2; mana=4.
  P2 (combo) casts combo:ramp:0 [artifact] for 2; mana=2.
    COMBAT P2 combo:engine:7 hits P0 for 2.
  P3 (tokens) casts tokens:engine:4 [enchantment] for 4; mana=2.
  P0 plays Cascade Bluffs (5 lands).
    COMBAT P0 Magnus the Red hits P3 for 4.
    COMBAT P0 Elemental 1/1 into P2 engine token 1/1.
  End round: P0 magnus life=33 board=11 sources=7, P1 control life=40 board=0 sources=3, P2 combo life=40 board=3 sources=11, P3 tokens life=36 board=2 sources=6

========== ROUND 8 ==========
  P1 (control) casts control:ramp:7 [artifact] for 3; mana=0.
  P2 land -> 7 lands.
  P2 (combo) casts combo:ramp:8 [artifact] for 2; mana=10.
  P2 (combo) casts combo:draw:5 [sorcery] for 3; mana=7.
  P2 (combo) casts combo:draw:11 [sorcery] for 2; mana=5.
  P2 (combo) casts combo:combo_piece:1 [artifact] for 3; mana=2.
  P2 (combo) casts combo:removal:2 [instant] for 2; mana=0.
    COMBAT P2 engine token 1/1 into P3 engine token 1/1.
  P3 (tokens) casts tokens:tokens:0 [sorcery] for 3; mana=3.
  P3 (tokens) casts tokens:small:1 [creature] for 1; mana=2.
  P0 plays Island (6 lands).
  P0 (magnus) casts Magnus the Red [creature] for 7; mana=1.
    Magnus the Red enters battlefield (4/5).
    COMBAT P0 Elemental hits P1 for 1.
  End round: P0 magnus life=33 board=11 sources=8, P1 control life=39 board=0 sources=5, P2 combo life=40 board=3 sources=13, P3 tokens life=36 board=4 sources=6

========== ROUND 9 ==========
  P1 land -> 3 lands.
  P1 (control) casts control:engine:9 [enchantment] for 3; mana=3.
  P1 (control) casts control:draw:3 [sorcery] for 2; mana=1.
  P2 land -> 8 lands.
  P2 (combo) casts combo:combo_piece:0 [artifact] for 4; mana=10.
  P2 (combo) casts combo:medium:2 [creature] for 3; mana=7.
  P2 (combo) casts combo:large:0 [creature] for 7; mana=0.
    COMBAT P2 combo:engine:7 hits P0 for 2.
  P3 land -> 7 lands.
  P3 (tokens) casts tokens:tokens:9 [sorcery] for 4; mana=3.
  P3 (tokens) casts tokens:draw:3 [sorcery] for 2; mana=1.
    COMBAT P3 engine token 1/1 into P2 combo:medium:2 4/3.
    COMBAT P3 Token hits P1 for 1.
    COMBAT P3 Token hits P0 for 1.
    COMBAT P3 tokens:small:1 hits P1 for 1.
  P0 misses land drop.
  P0 (magnus) casts Mind Stone [artifact] for 2; mana=6.
    Mind Stone increases available mana next turn.
    COMBAT P0 Elemental 1/1 into P3 Token 1/1.
    COMBAT P0 Magnus the Red hits P3 for 4.
  End round: P0 magnus life=30 board=13 sources=9, P1 control life=37 board=0 sources=6, P2 combo life=40 board=17 sources=14, P3 tokens life=32 board=4 sources=7

========== ROUND 10 ==========
  P1 (control) casts control:engine:0 [enchantment] for 4; mana=2.
  P1 (control) casts control:draw:5 [sorcery] for 2; mana=0.
  P2 land -> 9 lands.
  P2 (combo) casts combo:removal:4 [instant] for 2; mana=13.
  P2 (combo) casts combo:large:1 [creature] for 6; mana=7.
    COMBAT P2 engine token 1/1 into P3 Token 1/1.
    COMBAT P2 engine token hits P0 for 1.
    COMBAT P2 combo:medium:2 hits P3 for 4.
  P3 land -> 8 lands.
  P3 (tokens) casts tokens:engine:6 [enchantment] for 2; mana=6.
  P3 (tokens) casts tokens:tokens:16 [sorcery] for 4; mana=2.
  P3 (tokens) casts tokens:draw:0 [sorcery] for 2; mana=0.
    COMBAT P3 Token 1/1 into P1 control:engine:0 2/3.
    COMBAT P3 Token 1/1 into P2 combo:engine:7 2/3.
    COMBAT P3 tokens:small:1 hits P0 for 1.
  P0 plays Island (7 lands).
    COMBAT P0 Spawn hits P3 for 3.
    COMBAT P0 Spawn hits P1 for 3.
  End round: P0 magnus life=28 board=13 sources=10, P1 control life=34 board=3 sources=6, P2 combo life=40 board=22 sources=15, P3 tokens life=25 board=8 sources=8
```

## Scope reminder
This is an infrastructure diagnostic. v8 does not claim accurate deck win rates. Counterspell response priority is bounded and simplified; selection, several lands, and unimplemented real cards remain partial.
