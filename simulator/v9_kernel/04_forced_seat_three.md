# v9 infrastructure narrative: 04_forced_seat_three
**Seed:** 404 · **Magnus seat:** 3 · **Forced opening:** True
**Result:** turn_limit; winner None; Magnus life 35 after 10 rounds

| Seat | Provider | Life | Casts | Creatures | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | control | 24 | 6 | 2 | 6 |
| 1 | combo | 35 | 20 | 4 | 15 |
| 2 | tokens | 34 | 12 | 7 | 7 |
| 3 | magnus | 35 | 8 | 4 | 10 |

## Diagnostics
- Kernel views consistent: **True**
- Safety stop: **None**
- Shared-stack depth: **1**
- Casts resolved: **46**; countered: **0**
- Unsupported named cards seen: `{'Heralds of Tzeentch': 10, "Jace, Vryn's Prodigy": 10, 'Mathemagics': 9, 'Mana Geyser': 7, 'Reiterate': 5, 'Underworld Breach': 2}`
- Same-seed v8 Magnus at seat zero: life 28; spells 8
- Different seat numbering changes turn ordering, random choice and response behavior; this is not a deck-strength comparison.

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  P3 plays Island (1 lands).
  P3 (magnus) casts Sol Ring [artifact] for 1; mana=0.
    Sol Ring increases available mana next turn.
  P0 land -> 1 lands.
  End round: P0 control life=40 board=0 sources=1, P1 combo life=40 board=0 sources=1, P2 tokens life=40 board=0 sources=1, P3 magnus life=40 board=0 sources=3

========== ROUND 2 ==========
  P1 land -> 2 lands.
  P1 (combo) casts combo:engine:2 [enchantment] for 2; mana=0.
  P2 land -> 2 lands.
  P3 misses land drop.
  P3 (magnus) casts Preordain [sorcery] for 1; mana=2.
    Preordain: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 control life=40 board=0 sources=1, P1 combo life=40 board=2 sources=2, P2 tokens life=40 board=0 sources=2, P3 magnus life=40 board=0 sources=3

========== ROUND 3 ==========
  P1 land -> 3 lands.
  P1 (combo) casts combo:engine:7 [enchantment] for 3; mana=0.
    COMBAT P1 combo:engine:2 hits P0 for 2.
  P2 land -> 3 lands.
  P3 plays Spirebluff Canal (2 lands).
  P3 (magnus) casts Young Pyromancer [creature] for 2; mana=2.
    Young Pyromancer enters battlefield (2/1).
  End round: P0 control life=38 board=0 sources=1, P1 combo life=40 board=5 sources=3, P2 tokens life=40 board=0 sources=3, P3 magnus life=40 board=2 sources=4

========== ROUND 4 ==========
  P1 (combo) casts combo:draw:8 [sorcery] for 2; mana=1.
  P2 land -> 4 lands.
  P2 (tokens) casts tokens:engine:2 [enchantment] for 4; mana=0.
  P3 plays Mountain (3 lands).
  P3 (magnus) casts Harmonic Prodigy [creature] for 2; mana=3.
    Harmonic Prodigy enters battlefield (1/3).
  End round: P0 control life=38 board=0 sources=1, P1 combo life=40 board=5 sources=3, P2 tokens life=40 board=0 sources=4, P3 magnus life=40 board=3 sources=5

========== ROUND 5 ==========
  P1 land -> 4 lands.
  P1 (combo) casts combo:draw:10 [sorcery] for 2; mana=2.
  P1 (combo) casts combo:ramp:6 [artifact] for 2; mana=0.
    COMBAT P1 combo:engine:7 hits P2 for 2.
  P2 land -> 5 lands.
  P2 (tokens) casts tokens:engine:8 [enchantment] for 4; mana=1.
  P2 (tokens) casts tokens:small:4 [creature] for 1; mana=0.
  P3 plays Mountain (4 lands).
  P3 (magnus) casts Magnus the Red [creature] for 5; mana=1.
    Magnus the Red enters battlefield (4/5).
  End round: P0 control life=38 board=0 sources=1, P1 combo life=40 board=6 sources=6, P2 tokens life=38 board=3 sources=5, P3 magnus life=40 board=7 sources=6

========== ROUND 6 ==========
  P1 land -> 5 lands.
  P1 (combo) casts combo:ramp:4 [artifact] for 3; mana=4.
  P1 (combo) casts combo:draw:3 [sorcery] for 2; mana=2.
  P1 (combo) casts combo:draw:9 [sorcery] for 2; mana=0.
    COMBAT P1 engine token hits P0 for 1.
  P2 land -> 6 lands.
  P2 (tokens) casts tokens:engine:1 [enchantment] for 3; mana=3.
  P2 (tokens) casts tokens:buff:3 [sorcery] for 2; mana=1.
    COMBAT P2 tokens:small:4 4/2 into P1 combo:engine:2 2/3.
  P3 misses land drop.
  P3 (magnus) casts Ponder [sorcery] for 1; mana=5.
    Ponder: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 control life=37 board=0 sources=1, P1 combo life=40 board=4 sources=8, P2 tokens life=38 board=0 sources=6, P3 magnus life=40 board=9 sources=6

========== ROUND 7 ==========
  P1 land -> 6 lands.
  P1 (combo) casts combo:draw:0 [sorcery] for 3; mana=6.
  P1 (combo) casts combo:ramp:7 [artifact] for 2; mana=4.
  P1 (combo) casts combo:ramp:0 [artifact] for 2; mana=2.
    COMBAT P1 combo:engine:7 hits P0 for 2.
  P2 (tokens) casts tokens:engine:4 [enchantment] for 4; mana=2.
  P3 plays Cascade Bluffs (5 lands).
    COMBAT P3 Magnus the Red hits P2 for 4.
    COMBAT P3 Elemental 1/1 into P1 engine token 1/1.
  P0 land -> 2 lands.
  P0 (control) casts control:ramp:1 [artifact] for 2; mana=0.
  End round: P0 control life=35 board=0 sources=3, P1 combo life=40 board=3 sources=11, P2 tokens life=34 board=2 sources=6, P3 magnus life=40 board=11 sources=7

========== ROUND 8 ==========
  P1 land -> 7 lands.
  P1 (combo) casts combo:ramp:8 [artifact] for 2; mana=10.
  P1 (combo) casts combo:draw:5 [sorcery] for 3; mana=7.
  P1 (combo) casts combo:draw:11 [sorcery] for 2; mana=5.
  P1 (combo) casts combo:combo_piece:1 [artifact] for 3; mana=2.
  P1 (combo) casts combo:removal:2 [instant] for 2; mana=0.
    COMBAT P1 engine token hits P3 for 1.
  P2 (tokens) casts tokens:tokens:0 [sorcery] for 3; mana=3.
  P2 (tokens) casts tokens:small:1 [creature] for 1; mana=2.
    COMBAT P2 engine token hits P0 for 1.
  P3 plays Island (6 lands).
  P3 (magnus) casts Magnus the Red [creature] for 7; mana=1.
    Magnus the Red enters battlefield (4/5).
    COMBAT P3 Elemental hits P0 for 1.
  P0 (control) casts control:ramp:7 [artifact] for 3; mana=0.
  End round: P0 control life=33 board=0 sources=5, P1 combo life=40 board=4 sources=13, P2 tokens life=34 board=5 sources=6, P3 magnus life=39 board=11 sources=8

========== ROUND 9 ==========
  P1 land -> 8 lands.
  P1 (combo) casts combo:combo_piece:0 [artifact] for 4; mana=10.
  P1 (combo) casts combo:medium:2 [creature] for 3; mana=7.
  P1 (combo) casts combo:large:0 [creature] for 7; mana=0.
    COMBAT P1 combo:engine:7 hits P3 for 2.
    COMBAT P1 engine token 1/1 into P2 tokens:small:1 1/3.
  P2 (tokens) casts tokens:tokens:9 [sorcery] for 4; mana=2.
  P2 (tokens) casts tokens:draw:3 [sorcery] for 2; mana=0.
    COMBAT P2 engine token hits P0 for 1.
    COMBAT P2 engine token 1/1 into P1 combo:medium:2 4/3.
    COMBAT P2 Token hits P3 for 1.
    COMBAT P2 Token 1/1 into P1 combo:large:0 9/8.
    COMBAT P2 tokens:small:1 hits P1 for 1.
  P3 misses land drop.
  P3 (magnus) casts Mind Stone [artifact] for 2; mana=6.
    Mind Stone increases available mana next turn.
    COMBAT P3 Elemental 1/1 into P2 engine token 1/1.
    COMBAT P3 Magnus the Red hits P1 for 4.
  P0 land -> 3 lands.
  P0 (control) casts control:engine:9 [enchantment] for 3; mana=3.
  P0 (control) casts control:draw:3 [sorcery] for 2; mana=1.
  End round: P0 control life=32 board=0 sources=6, P1 combo life=35 board=17 sources=14, P2 tokens life=34 board=6 sources=6, P3 magnus life=36 board=13 sources=9

========== ROUND 10 ==========
  P1 land -> 9 lands.
  P1 (combo) casts combo:removal:4 [instant] for 2; mana=13.
    COMBAT P1 engine token 1/1 into P2 engine token 1/1.
    COMBAT P1 engine token hits P3 for 1.
    COMBAT P1 combo:medium:2 hits P0 for 4.
  P2 land -> 7 lands.
  P2 (tokens) casts tokens:engine:6 [enchantment] for 2; mana=5.
  P2 (tokens) casts tokens:tokens:16 [sorcery] for 4; mana=1.
    COMBAT P2 tokens:small:1 1/3 into P1 combo:large:0 9/8.
    COMBAT P2 Token hits P0 for 1.
  P3 plays Island (7 lands).
    COMBAT P3 Spawn hits P0 for 3.
  P0 (control) casts control:engine:0 [enchantment] for 4; mana=2.
  P0 (control) casts control:draw:5 [sorcery] for 2; mana=0.
  End round: P0 control life=24 board=3 sources=6, P1 combo life=35 board=16 sources=15, P2 tokens life=34 board=10 sources=7, P3 magnus life=35 board=10 sources=10
```

## Boundaries
Card-zone and typed-source services are tested separately; this live replay still uses legacy hand/library, mana, counter-only priority, and incomplete named-card effects.
