# v9 infrastructure narrative: 02_right_of_aggro
**Seed:** 104 · **Magnus seat:** 1 · **Forced opening:** False
**Result:** combat; winner 3; Magnus life -1 after 10 rounds

| Seat | Provider | Life | Casts | Creatures | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | aggro | -7 | 10 | 0 | 7 |
| 1 | magnus | -1 | 4 | 0 | 6 |
| 2 | tokens | -1 | 12 | 0 | 7 |
| 3 | ramp_stompy | 10 | 13 | 6 | 14 |

## Diagnostics
- Kernel views consistent: **True**
- Safety stop: **None**
- Shared-stack depth: **1**
- Casts resolved: **39**; countered: **0**
- Unsupported named cards seen: `{'Cyclonic Rift': 8, 'Chaos Mutation': 9, 'Dualcaster Mage': 9, 'Maskwood Nexus': 6, 'The Lost and the Damned': 5, 'Abrade': 4, 'Phyrexian Altar': 3, 'Heralds of Tzeentch': 1}`
- Same-seed v8 Magnus at seat zero: life 0; spells 4
- Different seat numbering changes turn ordering, random choice and response behavior; this is not a deck-strength comparison.

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P1 plays Island (1 lands).
  P1 (magnus) casts Brainstorm [instant] for 1; mana=0.
    Brainstorm: partial card selection (3 cards drawn; exact look/scry not modeled).
  P0 land -> 1 lands.
  P0 (aggro) casts aggro:small:14 [creature] for 1; mana=0.
  P3 land -> 1 lands.
  P2 land -> 1 lands.
  End round: P0 aggro life=40 board=1 sources=1, P1 magnus life=40 board=0 sources=1, P2 tokens life=40 board=0 sources=1, P3 ramp_stompy life=40 board=0 sources=1

========== ROUND 2 ==========
  P1 plays Mountain (2 lands).
  P1 (magnus) casts Pongify [instant] for 1; mana=1.
    Pongify destroys aggro:small:14; P0 gets a 3/3 Ape.
  P0 land -> 2 lands.
  P0 (aggro) casts aggro:small:13 [creature] for 2; mana=0.
  P3 land -> 2 lands.
  P3 (ramp_stompy) casts ramp_stompy:ramp:14 [artifact] for 2; mana=0.
  P2 land -> 2 lands.
  P2 (tokens) casts tokens:ramp:5 [artifact] for 2; mana=0.
  End round: P0 aggro life=40 board=4 sources=2, P1 magnus life=40 board=0 sources=2, P2 tokens life=40 board=0 sources=3, P3 ramp_stompy life=40 board=0 sources=3

========== ROUND 3 ==========
  P1 plays Stormcarved Coast (3 lands).
  P0 land -> 3 lands.
  P0 (aggro) casts aggro:small:10 [creature] for 1; mana=2.
  P0 (aggro) casts aggro:buff:0 [sorcery] for 2; mana=0.
    COMBAT P0 Ape (Pongify) hits P1 for 4.
  P3 land -> 3 lands.
  P3 (ramp_stompy) casts ramp_stompy:engine:0 [enchantment] for 4; mana=0.
  P2 land -> 3 lands.
  P2 (tokens) casts tokens:engine:1 [enchantment] for 2; mana=2.
  P2 (tokens) casts tokens:small:0 [creature] for 2; mana=0.
  End round: P0 aggro life=40 board=8 sources=3, P1 magnus life=36 board=0 sources=3, P2 tokens life=40 board=5 sources=4, P3 ramp_stompy life=40 board=0 sources=4

========== ROUND 4 ==========
  P1 plays Command Tower (4 lands).
  P0 (aggro) casts aggro:medium:1 [creature] for 3; mana=0.
    COMBAT P0 Ape (Pongify) 4/3 into P2 tokens:small:0 3/1.
    COMBAT P0 aggro:small:13 2/2 into P2 tokens:engine:1 2/3.
    COMBAT P0 aggro:small:10 hits P3 for 2.
  P3 land -> 4 lands.
  P3 (ramp_stompy) casts ramp_stompy:medium:6 [creature] for 4; mana=1.
  P2 (tokens) casts tokens:engine:2 [enchantment] for 3; mana=1.
  End round: P0 aggro life=40 board=7 sources=3, P1 magnus life=36 board=0 sources=4, P2 tokens life=40 board=2 sources=4, P3 ramp_stompy life=38 board=5 sources=5

========== ROUND 5 ==========
  P1 plays Riptide Laboratory (5 lands).
  P1 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    Magnus the Red enters battlefield (4/5).
  P0 land -> 4 lands.
  P0 (aggro) casts aggro:medium:5 [creature] for 3; mana=1.
    COMBAT P0 aggro:small:10 hits P2 for 2.
    COMBAT P0 aggro:medium:1 hits P3 for 5.
  P3 land -> 5 lands.
  P3 (ramp_stompy) casts ramp_stompy:medium:1 [creature] for 4; mana=2.
    COMBAT P3 engine token 1/1 into P0 aggro:medium:5 5/5.
    COMBAT P3 ramp_stompy:medium:6 hits P1 for 4.
  P2 land -> 4 lands.
  P2 (tokens) casts tokens:tokens:2 [sorcery] for 5; mana=0.
    COMBAT P2 tokens:engine:1 2/3 into P0 aggro:medium:5 5/5.
  End round: P0 aggro life=40 board=12 sources=4, P1 magnus life=32 board=4 sources=5, P2 tokens life=38 board=5 sources=5, P3 ramp_stompy life=33 board=8 sources=6

========== ROUND 6 ==========
  P1 plays Riverglide Pathway (6 lands).
    COMBAT P1 Magnus the Red hits P3 for 4.
  P0 land -> 5 lands.
  P0 (aggro) casts aggro:tokens:3 [sorcery] for 4; mana=1.
    COMBAT P0 aggro:small:10 2/3 into P3 ramp_stompy:medium:1 4/4.
    COMBAT P0 aggro:medium:1 hits P1 for 5.
    COMBAT P0 aggro:medium:5 hits P3 for 5.
  P3 land -> 6 lands.
  P3 (ramp_stompy) casts ramp_stompy:large:4 [creature] for 7; mana=0.
    COMBAT P3 ramp_stompy:medium:6 hits P1 for 4.
    COMBAT P3 ramp_stompy:medium:1 hits P2 for 4.
  P2 land -> 5 lands.
  P2 (tokens) casts tokens:buff:1 [sorcery] for 3; mana=3.
  P2 (tokens) casts tokens:removal:2 [instant] for 2; mana=1.
    COMBAT P2 engine token 3/1 into P0 Token 2/2.
    COMBAT P2 Token 3/1 into P0 Token 2/2.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:large:4 6/6.
    COMBAT P2 Token hits P3 for 3.
    COMBAT P2 Token hits P1 for 3.
  End round: P0 aggro life=40 board=12 sources=5, P1 magnus life=20 board=7 sources=6, P2 tokens life=34 board=6 sources=6, P3 ramp_stompy life=21 board=14 sources=7

========== ROUND 7 ==========
  P1 misses land drop.
    COMBAT P1 Magnus the Red hits P3 for 4.
    COMBAT P1 Spawn hits P0 for 3.
  P0 land -> 6 lands.
  P0 (aggro) casts aggro:engine:2 [enchantment] for 2; mana=4.
    COMBAT P0 aggro:medium:1 hits P3 for 5.
    COMBAT P0 aggro:medium:5 hits P2 for 5.
    COMBAT P0 Token hits P2 for 2.
  P3 land -> 7 lands.
  P3 (ramp_stompy) casts ramp_stompy:ramp:5 [artifact] for 2; mana=6.
  P3 (ramp_stompy) casts ramp_stompy:large:2 [creature] for 5; mana=1.
    COMBAT P3 ramp_stompy:medium:1 hits P2 for 4.
    COMBAT P3 ramp_stompy:large:4 hits P0 for 6.
  P2 (tokens) casts tokens:engine:8 [enchantment] for 2; mana=4.
  P2 (tokens) casts tokens:removal:3 [instant] for 3; mana=1.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:large:2 7/6.
  End round: P0 aggro life=31 board=7 sources=6, P1 magnus life=20 board=10 sources=6, P2 tokens life=23 board=4 sources=6, P3 ramp_stompy life=12 board=21 sources=10

========== ROUND 8 ==========
  P1 misses land drop.
  P1 (magnus) casts Baral, Chief of Compliance [creature] for 2; mana=4.
    Baral, Chief of Compliance enters battlefield (1/3).
    COMBAT P1 Magnus the Red hits P0 for 4.
    COMBAT P1 Spawn 3/3 into P2 Token 3/1.
  P0 land -> 7 lands.
  P0 (aggro) casts aggro:tokens:1 [sorcery] for 4; mana=3.
    COMBAT P0 aggro:medium:1 hits P1 for 5.
    COMBAT P0 Token 2/2 into P3 ramp_stompy:medium:6 4/3.
  P3 (ramp_stompy) casts ramp_stompy:ramp:7 [artifact] for 3; mana=7.
  P3 (ramp_stompy) casts ramp_stompy:medium:4 [creature] for 4; mana=3.
  P3 (ramp_stompy) casts ramp_stompy:tokens:1 [sorcery] for 3; mana=0.
    COMBAT P3 ramp_stompy:medium:1 hits P0 for 4.
    COMBAT P3 ramp_stompy:large:4 hits P1 for 6.
    COMBAT P3 ramp_stompy:large:2 hits P0 for 7.
  P2 land -> 6 lands.
  P2 (tokens) casts tokens:small:7 [creature] for 2; mana=5.
    COMBAT P2 engine token hits P1 for 1.
  End round: P0 aggro life=16 board=9 sources=7, P1 magnus life=8 board=11 sources=6, P2 tokens life=23 board=2 sources=7, P3 ramp_stompy life=12 board=30 sources=12

========== ROUND 9 ==========
  P1 misses land drop.
    COMBAT P1 Magnus the Red hits P0 for 4.
  P0 (aggro) casts aggro:medium:4 [creature] for 4; mana=3.
    COMBAT P0 aggro:medium:1 5/3 into P3 ramp_stompy:medium:4 5/5.
    COMBAT P0 Token hits P1 for 1.
    COMBAT P0 Token 1/1 into P2 tokens:small:7 1/2.
    COMBAT P0 Token 1/1 into P3 Token 2/2.
    COMBAT P0 Token hits P1 for 1.
  P3 land -> 8 lands.
  P3 (ramp_stompy) casts ramp_stompy:finisher:0 [sorcery] for 5; mana=8.
    COMBAT P3 ramp_stompy:medium:6 hits P1 for 7.
    ELIMINATED P1 (magnus) round 9: combat.
    COMBAT P3 ramp_stompy:medium:1 hits P2 for 7.
    COMBAT P3 ramp_stompy:large:4 hits P0 for 9.
    COMBAT P3 ramp_stompy:large:2 hits P0 for 10.
    ELIMINATED P0 (aggro) round 9: combat.
    COMBAT P3 Token hits P2 for 5.
    COMBAT P3 Token hits P2 for 5.
  P2 land -> 7 lands.
  P2 (tokens) casts tokens:draw:3 [sorcery] for 2; mana=6.
  P2 (tokens) casts tokens:ramp:0 [artifact] for 3; mana=3.
    COMBAT P2 engine token hits P3 for 1.
    COMBAT P2 tokens:small:7 hits P3 for 1.
  End round: P2 tokens life=6 board=3 sources=9, P3 ramp_stompy life=10 board=43 sources=13

========== ROUND 10 ==========
  P3 (ramp_stompy) casts ramp_stompy:ramp:3 [artifact] for 3; mana=10.
  P3 (ramp_stompy) casts ramp_stompy:removal:2 [instant] for 2; mana=8.
    COMBAT P3 ramp_stompy:medium:6 hits P2 for 7.
    ELIMINATED P2 (tokens) round 10: combat.
  End round: P3 ramp_stompy life=10 board=43 sources=14
```

## Boundaries
Card-zone and typed-source services are tested separately; this live replay still uses legacy hand/library, mana, counter-only priority, and incomplete named-card effects.
