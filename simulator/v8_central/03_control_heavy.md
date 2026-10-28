# V8 narrated game: 03_control_heavy
**Seed:** 103 | **Seats:** Magnus vs control, spellslinger, midrange | **Opening:** shuffled
**Result:** turn_limit; winner seat None; Magnus life 20 after 10 rounds

## Player scoreboard
| Seat | Pilot | Life | Casts | Creatures left | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | magnus | 20 | 7 | 6 | 7 |
| 1 | control | 27 | 6 | 0 | 6 |
| 2 | spellslinger | 30 | 12 | 2 | 9 |
| 3 | midrange | 22 | 15 | 4 | 9 |

## Shared-rule diagnostics
- Persistent-kernel vs legacy-view consistency: **True**
- Shared-stack max depth: **3**; countered frames: **2**
- Game-object zone transitions: **11**; simultaneous combat-damage batches: **3**
- Trigger instances: **4**; cost queries: **5**
- Safety stop: **None**
- Magnus unsupported cards held: {'Twincast': 10, 'Capsize': 9, 'Underworld Breach': 8, 'Heralds of Tzeentch': 6, "Jeska's Will": 1}

## Round-by-round comparison
| Round | Magnus life | Token count | P1 life | P2 life | P3 life |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 0 | 40 | 40 | 40 |
| 2 | 40 | 0 | 40 | 40 | 34 |
| 3 | 40 | 0 | 40 | 40 | 34 |
| 4 | 40 | 0 | 40 | 40 | 34 |
| 5 | 40 | 0 | 40 | 40 | 34 |
| 6 | 40 | 1 | 40 | 40 | 28 |
| 7 | 39 | 2 | 36 | 40 | 24 |
| 8 | 37 | 2 | 32 | 37 | 24 |
| 9 | 32 | 2 | 31 | 37 | 22 |
| 10 | 20 | 3 | 27 | 30 | 22 |

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P2 land -> 1 lands.
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P0 plays Island (1 lands).
  End round: P0 magnus life=40 board=0 sources=1, P1 control life=40 board=0 sources=1, P2 spellslinger life=40 board=0 sources=1, P3 midrange life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (spellslinger) casts spellslinger:burn:1 [instant] for 2; mana=0.
  P1 land -> 2 lands.
  P0 plays Island (2 lands).
  End round: P0 magnus life=40 board=0 sources=2, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=0 sources=2, P3 midrange life=34 board=0 sources=1

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (spellslinger) casts spellslinger:ramp:6 [artifact] for 3; mana=0.
  P3 land -> 2 lands.
  P3 (midrange) casts midrange:ramp:3 [artifact] for 2; mana=0.
  P0 plays Mountain (3 lands).
  P0 (magnus) casts Third Path Iconoclast [creature] for 2; mana=1.
  P1 (control) casts control:counter:1 [instant] for 2; mana=0.
    STACK: P1 casts control:counter:1 targeting Third Path Iconoclast.
  P0 (magnus) casts Flusterstorm [instant] for 1; mana=0.
    STACK: P0 casts Flusterstorm targeting control:counter:1.
    STACK: Flusterstorm counters control:counter:1.
    STACK: control:counter:1 is countered.
    Third Path Iconoclast enters battlefield (1/1).
  End round: P0 magnus life=40 board=1 sources=3, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=0 sources=4, P3 midrange life=34 board=0 sources=3

========== ROUND 4 ==========
  P2 land -> 4 lands.
  P2 (spellslinger) casts spellslinger:ramp:1 [artifact] for 3; mana=2.
  P2 (spellslinger) casts spellslinger:removal:0 [instant] for 2; mana=0.
  P3 (midrange) casts midrange:ramp:8 [artifact] for 2; mana=1.
  P0 plays Exotic Orchard (4 lands).
  End round: P0 magnus life=40 board=0 sources=4, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=0 sources=6, P3 midrange life=34 board=0 sources=4

========== ROUND 5 ==========
  P2 (spellslinger) casts spellslinger:ramp:2 [artifact] for 3; mana=3.
  P2 (spellslinger) casts spellslinger:tokens:2 [sorcery] for 3; mana=0.
  P3 (midrange) casts midrange:ramp:7 [artifact] for 2; mana=2.
  P3 (midrange) casts midrange:draw:1 [sorcery] for 2; mana=0.
  P1 (control) casts control:removal:4 [instant] for 2; mana=0.
  P0 plays Riptide Laboratory (5 lands).
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=40 board=4 sources=5, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=2 sources=7, P3 midrange life=34 board=0 sources=5

========== ROUND 6 ==========
  P2 (spellslinger) casts spellslinger:combo_piece:0 [artifact] for 2; mana=5.
  P2 (spellslinger) casts spellslinger:tokens:4 [sorcery] for 3; mana=2.
    COMBAT P2 Token hits P3 for 2.
  P3 land -> 3 lands.
  P3 (midrange) casts midrange:ramp:6 [artifact] for 3; mana=3.
  P3 (midrange) casts midrange:medium:3 [creature] for 3; mana=0.
  P0 plays Mountain (6 lands).
  P0 (magnus) casts Pongify [instant] for 1; mana=5.
    Pongify destroys midrange:medium:3; P3 gets a 3/3 Ape.
    COMBAT P0 Magnus the Red hits P3 for 4.
  End round: P0 magnus life=40 board=7 sources=6, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=4 sources=7, P3 midrange life=28 board=3 sources=7

========== ROUND 7 ==========
  P2 (spellslinger) casts spellslinger:engine:6 [enchantment] for 3; mana=4.
    COMBAT P2 Token 2/2 into P3 Ape (Pongify) 3/3.
    COMBAT P2 Token hits P1 for 1.
    COMBAT P2 Token hits P0 for 1.
  P3 land -> 4 lands.
  P3 (midrange) casts midrange:draw:2 [sorcery] for 2; mana=6.
  P3 (midrange) casts midrange:removal:6 [instant] for 3; mana=3.
  P3 (midrange) casts midrange:removal:2 [instant] for 3; mana=0.
  P1 land -> 3 lands.
  P1 (control) casts control:ramp:6 [artifact] for 3; mana=0.
  P0 misses land drop.
  P0 (magnus) casts Archmage Emeritus [creature] for 4; mana=2.
    Archmage Emeritus enters battlefield (2/2).
    COMBAT P0 Magnus the Red hits P3 for 4.
    COMBAT P0 Spawn hits P1 for 3.
  End round: P0 magnus life=39 board=12 sources=6, P1 control life=36 board=0 sources=4, P2 spellslinger life=40 board=2 sources=7, P3 midrange life=24 board=3 sources=8

========== ROUND 8 ==========
  P2 (spellslinger) casts spellslinger:engine:7 [enchantment] for 3; mana=4.
  P3 land -> 5 lands.
  P3 (midrange) casts midrange:tokens:0 [sorcery] for 3; mana=6.
  P3 (midrange) casts midrange:tokens:2 [sorcery] for 4; mana=2.
  P3 (midrange) casts midrange:small:1 [creature] for 1; mana=1.
  P1 (control) casts control:engine:3 [enchantment] for 4; mana=0.
  Steam Vents enters untapped; P0 pays 2 life.
  P0 plays Steam Vents (7 lands).
    COMBAT P0 Magnus the Red hits P1 for 4.
    COMBAT P0 Spawn 3/3 into P3 Ape (Pongify) 3/3.
    COMBAT P0 Spawn hits P2 for 3.
  End round: P0 magnus life=37 board=12 sources=7, P1 control life=32 board=0 sources=4, P2 spellslinger life=37 board=2 sources=7, P3 midrange life=24 board=8 sources=9

========== ROUND 9 ==========
  P2 land -> 5 lands.
  P2 (spellslinger) casts spellslinger:large:1 [creature] for 7; mana=1.
    COMBAT P2 spellslinger:engine:6 hits P3 for 2.
  P3 (midrange) casts midrange:removal:4 [instant] for 2; mana=7.
    COMBAT P3 Token hits P0 for 2.
    COMBAT P3 Token 2/2 into P2 spellslinger:large:1 9/9.
    COMBAT P3 Token hits P1 for 1.
    COMBAT P3 Token hits P0 for 1.
    COMBAT P3 midrange:small:1 hits P0 for 2.
  P1 land -> 4 lands.
  P1 (control) casts control:engine:2 [enchantment] for 4; mana=1.
  P3 (midrange) casts midrange:counter:0 [instant] for 2; mana=5.
    STACK: P3 casts midrange:counter:0 targeting control:engine:2.
    STACK: midrange:counter:0 counters control:engine:2.
    STACK: control:engine:2 is countered.
  P0 misses land drop.
  P0 (magnus) casts Magnus the Red [creature] for 7; mana=0.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=32 board=12 sources=7, P1 control life=31 board=0 sources=5, P2 spellslinger life=37 board=11 sources=8, P3 midrange life=22 board=6 sources=9

========== ROUND 10 ==========
  P2 land -> 6 lands.
  P2 (spellslinger) casts spellslinger:removal:3 [instant] for 2; mana=7.
    COMBAT P2 spellslinger:engine:6 hits P0 for 2.
    COMBAT P2 spellslinger:large:1 hits P0 for 9.
  P3 (midrange) casts midrange:medium:8 [creature] for 3; mana=6.
    COMBAT P3 Token hits P1 for 2.
    COMBAT P3 Token hits P0 for 1.
    COMBAT P3 midrange:small:1 hits P1 for 2.
  P1 land -> 5 lands.
  P1 (control) casts control:engine:4 [enchantment] for 4; mana=2.
  P0 misses land drop.
  P0 (magnus) casts Storm-Kiln Artist [creature] for 4; mana=3.
    Storm-Kiln Artist enters battlefield (2/2).
    COMBAT P0 Spawn hits P2 for 3.
    COMBAT P0 Magnus the Red hits P2 for 4.
  End round: P0 magnus life=20 board=17 sources=7, P1 control life=27 board=0 sources=6, P2 spellslinger life=30 board=11 sources=9, P3 midrange life=22 board=8 sources=9
```

## Scope reminder
This is an infrastructure diagnostic. v8 does not claim accurate deck win rates. Counterspell response priority is bounded and simplified; selection, several lands, and unimplemented real cards remain partial.
