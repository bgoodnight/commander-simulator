# V8 narrated game: 01_mixed
**Seed:** 102 | **Seats:** Magnus vs aggro, control, combo | **Opening:** shuffled
**Result:** turn_limit; winner seat None; Magnus life 9 after 10 rounds

## Player scoreboard
| Seat | Pilot | Life | Casts | Creatures left | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | magnus | 9 | 9 | 10 | 7 |
| 1 | aggro | 39 | 13 | 5 | 6 |
| 2 | control | 20 | 17 | 10 | 11 |
| 3 | combo | 16 | 10 | 1 | 13 |

## Shared-rule diagnostics
- Persistent-kernel vs legacy-view consistency: **True**
- Shared-stack max depth: **3**; countered frames: **4**
- Game-object zone transitions: **15**; simultaneous combat-damage batches: **8**
- Trigger instances: **8**; cost queries: **36**
- Safety stop: **None**
- Magnus unsupported cards held: {'Chaos Warp': 9, 'Mathemagics': 10, 'Resonating Lute': 10, 'Phyrexian Altar': 2, 'Sigil Tracer': 2}

## Round-by-round comparison
| Round | Magnus life | Token count | P1 life | P2 life | P3 life |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 0 | 40 | 40 | 40 |
| 2 | 40 | 0 | 40 | 39 | 40 |
| 3 | 36 | 0 | 40 | 36 | 40 |
| 4 | 36 | 0 | 40 | 33 | 40 |
| 5 | 36 | 1 | 40 | 27 | 40 |
| 6 | 33 | 3 | 40 | 27 | 37 |
| 7 | 30 | 3 | 40 | 27 | 33 |
| 8 | 26 | 4 | 40 | 20 | 28 |
| 9 | 19 | 5 | 39 | 20 | 24 |
| 10 | 9 | 6 | 39 | 20 | 16 |

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P2 land -> 1 lands.
  P1 land -> 1 lands.
  P1 (aggro) casts aggro:small:8 [creature] for 1; mana=0.
  P3 land -> 1 lands.
  P0 plays Island (1 lands).
  End round: P0 magnus life=40 board=0 sources=1, P1 aggro life=40 board=1 sources=1, P2 control life=40 board=0 sources=1, P3 combo life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (control) casts control:engine:1 [enchantment] for 2; mana=0.
  P1 land -> 2 lands.
  P1 (aggro) casts aggro:small:4 [creature] for 2; mana=0.
    COMBAT P1 aggro:small:8 hits P2 for 1.
  P3 land -> 2 lands.
  P3 (combo) casts combo:ramp:4 [artifact] for 2; mana=0.
  P0 plays Sokenzan, Crucible of Defiance (2 lands).
  P0 (magnus) casts Third Path Iconoclast [creature] for 2; mana=0.
    Third Path Iconoclast enters battlefield (1/1).
  End round: P0 magnus life=40 board=1 sources=2, P1 aggro life=40 board=3 sources=2, P2 control life=39 board=0 sources=2, P3 combo life=40 board=0 sources=3

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (control) casts control:engine:3 [enchantment] for 3; mana=0.
  P1 land -> 3 lands.
  P1 (aggro) casts aggro:buff:1 [sorcery] for 2; mana=1.
    COMBAT P1 aggro:small:8 hits P2 for 3.
    COMBAT P1 aggro:small:4 hits P0 for 4.
  P3 land -> 3 lands.
  P3 (combo) casts combo:engine:3 [enchantment] for 2; mana=2.
  P3 (combo) casts combo:draw:2 [sorcery] for 2; mana=0.
  P0 plays Mountain (3 lands).
  P0 (magnus) casts Goblin Electromancer [creature] for 2; mana=1.
    Goblin Electromancer enters battlefield (2/2).
  End round: P0 magnus life=36 board=3 sources=3, P1 aggro life=40 board=7 sources=3, P2 control life=36 board=0 sources=3, P3 combo life=40 board=2 sources=4

========== ROUND 4 ==========
  P2 land -> 4 lands.
  P2 (control) casts control:draw:2 [sorcery] for 2; mana=2.
  P2 (control) casts control:draw:6 [sorcery] for 2; mana=0.
  P1 land -> 4 lands.
  P1 (aggro) casts aggro:medium:1 [creature] for 4; mana=0.
    COMBAT P1 aggro:small:8 hits P2 for 3.
    COMBAT P1 aggro:small:4 4/1 into P3 combo:engine:3 2/3.
  P3 land -> 4 lands.
  P3 (combo) casts combo:ramp:5 [artifact] for 2; mana=3.
  P0 misses land drop.
  P0 (magnus) casts Baral, Chief of Compliance [creature] for 2; mana=1.
    Baral, Chief of Compliance enters battlefield (1/3).
  End round: P0 magnus life=36 board=4 sources=3, P1 aggro life=40 board=6 sources=4, P2 control life=33 board=1 sources=4, P3 combo life=40 board=0 sources=6

========== ROUND 5 ==========
  P2 land -> 5 lands.
  P2 (control) casts control:draw:0 [sorcery] for 2; mana=3.
  P2 (control) casts control:draw:4 [sorcery] for 3; mana=0.
  P1 (aggro) casts aggro:medium:0 [creature] for 4; mana=0.
    COMBAT P1 aggro:small:8 hits P2 for 3.
    COMBAT P1 aggro:medium:1 hits P2 for 3.
  P3 land -> 5 lands.
  P3 (combo) casts combo:engine:2 [enchantment] for 4; mana=3.
  P0 misses land drop.
  P0 (magnus) casts Izzet Signet [artifact] for 2; mana=1.
    Izzet Signet increases available mana next turn.
  End round: P0 magnus life=36 board=5 sources=4, P1 aggro life=40 board=9 sources=4, P2 control life=27 board=2 sources=5, P3 combo life=40 board=0 sources=7

========== ROUND 6 ==========
  P2 land -> 6 lands.
  P2 (control) casts control:engine:9 [enchantment] for 2; mana=4.
  P2 (control) casts control:engine:7 [enchantment] for 4; mana=0.
  P3 (combo) casts combo:counter:4 [instant] for 2; mana=1.
    STACK: P3 casts combo:counter:4 targeting control:engine:7.
    STACK: combo:counter:4 counters control:engine:7.
    STACK: control:engine:7 is countered.
  P1 (aggro) casts aggro:medium:3 [creature] for 4; mana=0.
    COMBAT P1 aggro:small:8 hits P0 for 3.
    COMBAT P1 aggro:medium:0 hits P3 for 3.
  P3 land -> 6 lands.
  P3 (combo) casts combo:ramp:0 [artifact] for 3; mana=5.
  P0 misses land drop.
  P0 (magnus) casts Pongify [instant] for 1; mana=4.
    Pongify destroys aggro:medium:3; P1 gets a 3/3 Ape.
  P0 (magnus) casts Impulse [instant] for 1; mana=2.
    Impulse: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=33 board=7 sources=4, P1 aggro life=40 board=12 sources=4, P2 control life=27 board=6 sources=6, P3 combo life=37 board=0 sources=9

========== ROUND 7 ==========
  P2 land -> 7 lands.
  P2 (control) casts control:medium:4 [creature] for 4; mana=3.
    COMBAT P2 engine token hits P3 for 1.
  P1 (aggro) casts aggro:tokens:0 [sorcery] for 4; mana=0.
    COMBAT P1 aggro:small:8 hits P3 for 3.
    COMBAT P1 aggro:medium:0 hits P0 for 3.
    COMBAT P1 Ape (Pongify) 3/3 into P2 control:medium:4 3/3.
  P3 land -> 7 lands.
  P3 (combo) casts combo:large:1 [creature] for 6; mana=4.
  P2 (control) casts control:counter:6 [instant] for 2; mana=1.
    STACK: P2 casts control:counter:6 targeting combo:large:1.
    STACK: control:counter:6 counters combo:large:1.
    STACK: combo:large:1 is countered.
  P0 plays Island (4 lands).
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=30 board=11 sources=5, P1 aggro life=40 board=11 sources=4, P2 control life=27 board=7 sources=7, P3 combo life=33 board=0 sources=10

========== ROUND 8 ==========
  P2 land -> 8 lands.
  P2 (control) casts control:large:0 [creature] for 5; mana=3.
  P2 (control) casts control:small:2 [creature] for 1; mana=2.
    COMBAT P2 engine token 1/1 into P1 aggro:medium:1 3/2.
    COMBAT P2 engine token hits P0 for 1.
    COMBAT P2 engine token 1/1 into P1 Token 1/1.
    COMBAT P2 control:engine:9 hits P3 for 2.
  P1 land -> 5 lands.
  P1 (aggro) casts aggro:draw:2 [sorcery] for 2; mana=3.
  P2 (control) casts control:counter:2 [instant] for 2; mana=0.
    STACK: P2 casts control:counter:2 targeting aggro:draw:2.
    STACK: control:counter:2 counters aggro:draw:2.
    STACK: aggro:draw:2 is countered.
  P1 (aggro) casts aggro:engine:1 [enchantment] for 3; mana=0.
    COMBAT P1 aggro:small:8 hits P0 for 3.
    COMBAT P1 aggro:medium:1 hits P3 for 3.
    COMBAT P1 aggro:medium:0 hits P2 for 3.
    COMBAT P1 Token 1/1 into P2 control:small:2 2/2.
  P3 land -> 8 lands.
  P3 (combo) casts combo:ramp:9 [artifact] for 3; mana=8.
  P0 plays Island (5 lands).
  P0 (magnus) casts Brainstorm [instant] for 1; mana=6.
    Brainstorm: partial card selection (3 cards drawn; exact look/scry not modeled).
    COMBAT P0 Soldier 1/1 into P3 engine token 1/1.
    COMBAT P0 Magnus the Red hits P2 for 4.
  End round: P0 magnus life=26 board=14 sources=6, P1 aggro life=40 board=9 sources=5, P2 control life=20 board=14 sources=8, P3 combo life=28 board=0 sources=12

========== ROUND 9 ==========
  P2 land -> 9 lands.
    COMBAT P2 engine token hits P1 for 1.
    COMBAT P2 engine token hits P0 for 1.
  P1 (aggro) casts aggro:medium:5 [creature] for 4; mana=1.
    COMBAT P1 aggro:small:8 hits P0 for 3.
    COMBAT P1 aggro:medium:1 hits P0 for 3.
  P3 land -> 9 lands.
  P0 plays Sulfur Falls (6 lands).
    COMBAT P0 Magnus the Red hits P3 for 4.
  End round: P0 magnus life=19 board=17 sources=7, P1 aggro life=39 board=13 sources=5, P2 control life=20 board=16 sources=9, P3 combo life=24 board=1 sources=13

========== ROUND 10 ==========
  P2 land -> 10 lands.
  P2 (control) casts control:draw:5 [sorcery] for 2; mana=8.
  P2 (control) casts control:ramp:7 [artifact] for 2; mana=6.
  P2 (control) casts control:removal:5 [instant] for 3; mana=3.
  P0 (magnus) casts Arcane Denial [instant] for 1; mana=7.
    STACK: P0 casts Arcane Denial targeting control:removal:5.
  P2 (control) casts control:counter:4 [instant] for 2; mana=1.
    STACK: P2 casts control:counter:4 targeting Arcane Denial.
    STACK: control:counter:4 counters Arcane Denial.
    STACK: Arcane Denial is countered.
    COMBAT P2 engine token 1/1 into P1 aggro:medium:0 3/3.
  P1 land -> 6 lands.
  P1 (aggro) casts aggro:small:3 [creature] for 1; mana=5.
  P1 (aggro) casts aggro:small:9 [creature] for 2; mana=3.
  P1 (aggro) casts aggro:burn:0 [instant] for 3; mana=0.
    COMBAT P1 aggro:small:8 hits P0 for 3.
    COMBAT P1 aggro:medium:1 hits P3 for 3.
    COMBAT P1 aggro:medium:0 hits P0 for 3.
  P3 (combo) casts combo:engine:10 [enchantment] for 2; mana=11.
    COMBAT P3 engine token hits P0 for 1.
  P0 misses land drop.
    COMBAT P0 Magnus the Red hits P3 for 4.
    COMBAT P0 Soldier hits P3 for 1.
    COMBAT P0 Spawn 3/3 into P1 aggro:small:3 3/2.
  End round: P0 magnus life=9 board=18 sources=7, P1 aggro life=39 board=13 sources=6, P2 control life=20 board=17 sources=11, P3 combo life=16 board=1 sources=13
```

## Scope reminder
This is an infrastructure diagnostic. v8 does not claim accurate deck win rates. Counterspell response priority is bounded and simplified; selection, several lands, and unimplemented real cards remain partial.
