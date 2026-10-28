# V8 narrated game: 02_pressure
**Seed:** 104 | **Seats:** Magnus vs aggro, tokens, ramp_stompy | **Opening:** shuffled
**Result:** combat; winner seat 3; Magnus life 0 after 10 rounds

## Player scoreboard
| Seat | Pilot | Life | Casts | Creatures left | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | magnus | 0 | 4 | 0 | 6 |
| 1 | aggro | -2 | 11 | 0 | 8 |
| 2 | tokens | -7 | 12 | 0 | 7 |
| 3 | ramp_stompy | 17 | 13 | 6 | 14 |

## Shared-rule diagnostics
- Persistent-kernel vs legacy-view consistency: **True**
- Shared-stack max depth: **1**; countered frames: **0**
- Game-object zone transitions: **50**; simultaneous combat-damage batches: **17**
- Trigger instances: **4**; cost queries: **3**
- Safety stop: **None**
- Magnus unsupported cards held: {'Cyclonic Rift': 8, 'Chaos Mutation': 9, 'Dualcaster Mage': 9, 'Maskwood Nexus': 6, 'The Lost and the Damned': 5, 'Abrade': 4, 'Phyrexian Altar': 3, 'Heralds of Tzeentch': 1}

## Round-by-round comparison
| Round | Magnus life | Token count | P1 life | P2 life | P3 life |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 0 | 40 | 40 | 40 |
| 2 | 39 | 0 | 40 | 40 | 40 |
| 3 | 39 | 0 | 40 | 36 | 40 |
| 4 | 39 | 0 | 40 | 36 | 36 |
| 5 | 32 | 0 | 40 | 36 | 36 |
| 6 | 26 | 1 | 30 | 31 | 31 |
| 7 | 17 | 1 | 26 | 22 | 26 |
| 8 | 12 | 2 | 17 | 17 | 26 |
| 9 | 1 | 3 | 10 | -7 | 22 |
| 10 | 0 | 0 | -2 | -7 | 17 |

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P1 (aggro) casts aggro:small:14 [creature] for 1; mana=0.
  P0 plays Island (1 lands).
  P0 (magnus) casts Brainstorm [instant] for 1; mana=0.
    Brainstorm: partial card selection (3 cards drawn; exact look/scry not modeled).
  P3 land -> 1 lands.
  P2 land -> 1 lands.
  End round: P0 magnus life=40 board=0 sources=1, P1 aggro life=40 board=1 sources=1, P2 tokens life=40 board=0 sources=1, P3 ramp_stompy life=40 board=0 sources=1

========== ROUND 2 ==========
  P1 land -> 2 lands.
  P1 (aggro) casts aggro:small:13 [creature] for 2; mana=0.
    COMBAT P1 aggro:small:14 hits P0 for 1.
  P0 plays Mountain (2 lands).
  P0 (magnus) casts Pongify [instant] for 1; mana=1.
    Pongify destroys aggro:small:14; P1 gets a 3/3 Ape.
  P3 land -> 2 lands.
  P3 (ramp_stompy) casts ramp_stompy:ramp:14 [artifact] for 2; mana=0.
  P2 land -> 2 lands.
  P2 (tokens) casts tokens:ramp:5 [artifact] for 2; mana=0.
  End round: P0 magnus life=39 board=0 sources=2, P1 aggro life=40 board=4 sources=2, P2 tokens life=40 board=0 sources=3, P3 ramp_stompy life=40 board=0 sources=3

========== ROUND 3 ==========
  P1 land -> 3 lands.
  P1 (aggro) casts aggro:small:10 [creature] for 1; mana=2.
  P1 (aggro) casts aggro:buff:0 [sorcery] for 2; mana=0.
    COMBAT P1 Ape (Pongify) hits P2 for 4.
  P0 plays Stormcarved Coast (3 lands).
  P3 land -> 3 lands.
  P3 (ramp_stompy) casts ramp_stompy:engine:0 [enchantment] for 4; mana=0.
  P2 land -> 3 lands.
  P2 (tokens) casts tokens:engine:1 [enchantment] for 2; mana=2.
  P2 (tokens) casts tokens:small:0 [creature] for 2; mana=0.
  End round: P0 magnus life=39 board=0 sources=3, P1 aggro life=40 board=8 sources=3, P2 tokens life=36 board=5 sources=4, P3 ramp_stompy life=40 board=0 sources=4

========== ROUND 4 ==========
  P1 (aggro) casts aggro:medium:1 [creature] for 3; mana=0.
    COMBAT P1 aggro:small:13 2/2 into P2 tokens:engine:1 2/3.
    COMBAT P1 Ape (Pongify) hits P3 for 4.
    COMBAT P1 aggro:small:10 2/3 into P2 tokens:small:0 3/1.
  P0 plays Command Tower (4 lands).
  P3 land -> 4 lands.
  P3 (ramp_stompy) casts ramp_stompy:medium:6 [creature] for 4; mana=1.
  P2 (tokens) casts tokens:engine:2 [enchantment] for 3; mana=1.
  End round: P0 magnus life=39 board=0 sources=4, P1 aggro life=40 board=9 sources=3, P2 tokens life=36 board=2 sources=4, P3 ramp_stompy life=36 board=5 sources=5

========== ROUND 5 ==========
  P1 land -> 4 lands.
  P1 (aggro) casts aggro:medium:5 [creature] for 3; mana=1.
    COMBAT P1 Ape (Pongify) 4/3 into P3 ramp_stompy:medium:6 4/3.
    COMBAT P1 aggro:medium:1 hits P0 for 5.
  P0 plays Riptide Laboratory (5 lands).
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    Magnus the Red enters battlefield (4/5).
  P3 land -> 5 lands.
  P3 (ramp_stompy) casts ramp_stompy:medium:1 [creature] for 4; mana=2.
    COMBAT P3 engine token 1/1 into P1 aggro:medium:5 5/5.
  P2 land -> 4 lands.
  P2 (tokens) casts tokens:tokens:2 [sorcery] for 5; mana=0.
    COMBAT P2 tokens:engine:1 hits P0 for 2.
  End round: P0 magnus life=32 board=4 sources=5, P1 aggro life=40 board=10 sources=4, P2 tokens life=36 board=7 sources=5, P3 ramp_stompy life=36 board=4 sources=6

========== ROUND 6 ==========
  P1 land -> 5 lands.
  P1 (aggro) casts aggro:tokens:3 [sorcery] for 4; mana=1.
    COMBAT P1 aggro:medium:1 hits P3 for 5.
    COMBAT P1 aggro:medium:5 hits P2 for 5.
  P0 plays Riverglide Pathway (6 lands).
    COMBAT P0 Magnus the Red hits P1 for 4.
  P3 land -> 6 lands.
  P3 (ramp_stompy) casts ramp_stompy:large:4 [creature] for 7; mana=0.
    COMBAT P3 ramp_stompy:medium:1 hits P1 for 4.
  P2 land -> 5 lands.
  P2 (tokens) casts tokens:engine:8 [enchantment] for 2; mana=4.
  P2 (tokens) casts tokens:buff:1 [sorcery] for 3; mana=1.
    COMBAT P2 tokens:engine:1 hits P1 for 2.
    COMBAT P2 engine token 3/1 into P3 ramp_stompy:large:4 6/6.
    COMBAT P2 Token hits P0 for 3.
    COMBAT P2 Token hits P0 for 3.
  End round: P0 magnus life=26 board=7 sources=6, P1 aggro life=30 board=18 sources=5, P2 tokens life=31 board=14 sources=6, P3 ramp_stompy life=31 board=11 sources=7

========== ROUND 7 ==========
  P1 land -> 6 lands.
  P1 (aggro) casts aggro:engine:2 [enchantment] for 2; mana=4.
    COMBAT P1 aggro:medium:1 hits P3 for 5.
    COMBAT P1 aggro:medium:5 hits P2 for 5.
    COMBAT P1 Token hits P0 for 2.
    COMBAT P1 Token 2/2 into P2 Token 3/1.
    COMBAT P1 Token hits P0 for 2.
    COMBAT P1 Token 2/2 into P3 ramp_stompy:large:4 6/6.
  P0 misses land drop.
    COMBAT P0 Magnus the Red hits P2 for 4.
    COMBAT P0 Spawn 3/3 into P2 Token 3/1.
  P3 land -> 7 lands.
  P3 (ramp_stompy) casts ramp_stompy:medium:4 [creature] for 4; mana=4.
  P3 (ramp_stompy) casts ramp_stompy:tokens:1 [sorcery] for 3; mana=1.
    COMBAT P3 ramp_stompy:medium:1 hits P1 for 4.
  P2 land -> 6 lands.
  P2 (tokens) casts tokens:removal:2 [instant] for 2; mana=5.
  P2 (tokens) casts tokens:removal:3 [instant] for 3; mana=2.
  P2 (tokens) casts tokens:small:7 [creature] for 2; mana=0.
    COMBAT P2 tokens:engine:1 hits P0 for 2.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:large:4 6/6.
    COMBAT P2 Token hits P0 for 3.
  End round: P0 magnus life=17 board=7 sources=6, P1 aggro life=26 board=9 sources=6, P2 tokens life=22 board=7 sources=7, P3 ramp_stompy life=26 board=15 sources=8

========== ROUND 8 ==========
  P1 land -> 7 lands.
  P1 (aggro) casts aggro:tokens:1 [sorcery] for 4; mana=3.
    COMBAT P1 aggro:medium:5 hits P2 for 5.
    COMBAT P1 Token hits P0 for 2.
    COMBAT P1 Token 2/2 into P3 ramp_stompy:large:4 6/6.
  P0 misses land drop.
  P0 (magnus) casts Baral, Chief of Compliance [creature] for 2; mana=4.
    Baral, Chief of Compliance enters battlefield (1/3).
    COMBAT P0 Magnus the Red hits P1 for 4.
  P3 (ramp_stompy) casts ramp_stompy:ramp:5 [artifact] for 2; mana=6.
  P3 (ramp_stompy) casts ramp_stompy:large:2 [creature] for 5; mana=1.
    COMBAT P3 engine token 1/1 into P2 tokens:small:7 1/2.
    COMBAT P3 Token hits P0 for 2.
    COMBAT P3 Token hits P1 for 2.
  P2 land -> 7 lands.
  P2 (tokens) casts tokens:draw:3 [sorcery] for 2; mana=6.
  P2 (tokens) casts tokens:ramp:0 [artifact] for 3; mana=3.
    COMBAT P2 tokens:engine:1 hits P1 for 2.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:medium:1 4/4.
    COMBAT P2 engine token hits P0 for 1.
    COMBAT P2 tokens:small:7 hits P1 for 1.
  End round: P0 magnus life=12 board=11 sources=6, P1 aggro life=17 board=12 sources=7, P2 tokens life=17 board=5 sources=9, P3 ramp_stompy life=26 board=22 sources=10

========== ROUND 9 ==========
  P1 (aggro) casts aggro:medium:4 [creature] for 4; mana=3.
    COMBAT P1 aggro:medium:5 5/5 into P3 ramp_stompy:large:4 6/6.
    COMBAT P1 Token hits P0 for 2.
    COMBAT P1 engine token 1/1 into P3 ramp_stompy:medium:1 4/4.
    COMBAT P1 Token 1/1 into P2 engine token 1/1.
    COMBAT P1 Token 1/1 into P3 ramp_stompy:large:2 7/6.
    COMBAT P1 Token hits P2 for 1.
    COMBAT P1 Token 1/1 into P3 engine token 1/1.
  P0 misses land drop.
    COMBAT P0 Magnus the Red hits P3 for 4.
    COMBAT P0 Spawn hits P2 for 3.
  P3 land -> 8 lands.
  P3 (ramp_stompy) casts ramp_stompy:finisher:0 [sorcery] for 5; mana=6.
  P3 (ramp_stompy) casts ramp_stompy:ramp:7 [artifact] for 3; mana=3.
    COMBAT P3 ramp_stompy:medium:1 hits P1 for 7.
    COMBAT P3 ramp_stompy:large:4 hits P0 for 9.
    COMBAT P3 Token hits P2 for 5.
    COMBAT P3 Token hits P2 for 5.
    COMBAT P3 ramp_stompy:large:2 hits P2 for 10.
    ELIMINATED P2 (tokens) round 9: combat.
  End round: P0 magnus life=1 board=14 sources=6, P1 aggro life=10 board=6 sources=7, P3 ramp_stompy life=22 board=36 sources=13

========== ROUND 10 ==========
  P1 land -> 8 lands.
  P1 (aggro) casts aggro:large:0 [creature] for 7; mana=1.
    COMBAT P1 Token hits P3 for 2.
    COMBAT P1 Token hits P0 for 1.
    ELIMINATED P0 (magnus) round 10: combat.
    COMBAT P1 aggro:medium:4 hits P3 for 3.
  P3 (ramp_stompy) casts ramp_stompy:removal:2 [instant] for 2; mana=11.
  P3 (ramp_stompy) casts ramp_stompy:ramp:3 [artifact] for 3; mana=8.
    COMBAT P3 ramp_stompy:medium:1 hits P1 for 7.
    COMBAT P3 Token hits P1 for 5.
    ELIMINATED P1 (aggro) round 10: combat.
  End round: P3 ramp_stompy life=17 board=37 sources=14
```

## Scope reminder
This is an infrastructure diagnostic. v8 does not claim accurate deck win rates. Counterspell response priority is bounded and simplified; selection, several lands, and unimplemented real cards remain partial.
