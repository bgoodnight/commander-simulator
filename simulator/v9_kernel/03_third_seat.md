# v9 infrastructure narrative: 03_third_seat
**Seed:** 103 · **Magnus seat:** 2 · **Forced opening:** False
**Result:** turn_limit; winner None; Magnus life 20 after 10 rounds

| Seat | Provider | Life | Casts | Creatures | Mana sources |
|---:|---|---:|---:|---:|---:|
| 0 | control | 23 | 7 | 1 | 6 |
| 1 | spellslinger | 32 | 13 | 4 | 9 |
| 2 | magnus | 20 | 7 | 4 | 7 |
| 3 | midrange | 28 | 15 | 5 | 8 |

## Diagnostics
- Kernel views consistent: **True**
- Safety stop: **None**
- Shared-stack depth: **3**
- Casts resolved: **38**; countered: **4**
- Unsupported named cards seen: `{'Twincast': 10, 'Capsize': 9, 'Underworld Breach': 8, 'Heralds of Tzeentch': 6, "Jeska's Will": 1}`
- Same-seed v8 Magnus at seat zero: life 20; spells 7
- Different seat numbering changes turn ordering, random choice and response behavior; this is not a deck-strength comparison.

## Action-by-action transcript
```text

========== ROUND 1 ==========
  P2 plays Island (1 lands).
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P0 land -> 1 lands.
  End round: P0 control life=40 board=0 sources=1, P1 spellslinger life=40 board=0 sources=1, P2 magnus life=40 board=0 sources=1, P3 midrange life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 plays Island (2 lands).
  P1 land -> 2 lands.
  P1 (spellslinger) casts spellslinger:burn:1 [instant] for 2; mana=0.
  P0 land -> 2 lands.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=40 board=0 sources=2, P2 magnus life=40 board=0 sources=2, P3 midrange life=34 board=0 sources=1

========== ROUND 3 ==========
  P2 plays Mountain (3 lands).
  P2 (magnus) casts Third Path Iconoclast [creature] for 2; mana=1.
    Third Path Iconoclast enters battlefield (1/1).
  P3 land -> 2 lands.
  P3 (midrange) casts midrange:ramp:3 [artifact] for 2; mana=0.
  P1 land -> 3 lands.
  P1 (spellslinger) casts spellslinger:ramp:6 [artifact] for 3; mana=0.
  P0 (control) casts control:counter:1 [instant] for 2; mana=0.
    STACK: P0 casts control:counter:1 targeting spellslinger:ramp:6.
  P2 (magnus) casts Flusterstorm [instant] for 1; mana=0.
    STACK: P2 casts Flusterstorm targeting control:counter:1.
    STACK: Flusterstorm counters control:counter:1.
    STACK: control:counter:1 is countered.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=40 board=0 sources=4, P2 magnus life=40 board=2 sources=3, P3 midrange life=34 board=0 sources=3

========== ROUND 4 ==========
  P2 plays Exotic Orchard (4 lands).
    COMBAT P2 Soldier hits P1 for 1.
  P3 (midrange) casts midrange:ramp:8 [artifact] for 2; mana=1.
  P0 (control) casts control:counter:0 [instant] for 2; mana=0.
    STACK: P0 casts control:counter:0 targeting midrange:ramp:8.
    STACK: control:counter:0 counters midrange:ramp:8.
    STACK: midrange:ramp:8 is countered.
  P1 land -> 4 lands.
  P1 (spellslinger) casts spellslinger:ramp:1 [artifact] for 3; mana=2.
  P1 (spellslinger) casts spellslinger:removal:0 [instant] for 2; mana=0.
  P0 (control) casts control:removal:4 [instant] for 2; mana=0.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=39 board=0 sources=6, P2 magnus life=40 board=0 sources=4, P3 midrange life=34 board=0 sources=3

========== ROUND 5 ==========
  P2 plays Riptide Laboratory (5 lands).
  P2 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    Magnus the Red enters battlefield (4/5).
  P3 (midrange) casts midrange:ramp:7 [artifact] for 2; mana=1.
  P1 (spellslinger) casts spellslinger:ramp:2 [artifact] for 3; mana=3.
  P1 (spellslinger) casts spellslinger:tokens:2 [sorcery] for 3; mana=0.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=39 board=4 sources=7, P2 magnus life=40 board=4 sources=5, P3 midrange life=34 board=0 sources=4

========== ROUND 6 ==========
  P2 plays Mountain (6 lands).
  P2 (magnus) casts Pongify [instant] for 1; mana=5.
    Pongify destroys Token; P1 gets a 3/3 Ape.
    COMBAT P2 Magnus the Red hits P3 for 4.
  P3 land -> 3 lands.
  P3 (midrange) casts midrange:medium:3 [creature] for 3; mana=2.
  P3 (midrange) casts midrange:draw:1 [sorcery] for 2; mana=0.
  P1 (spellslinger) casts spellslinger:combo_piece:0 [artifact] for 2; mana=5.
  P1 (spellslinger) casts spellslinger:tokens:4 [sorcery] for 3; mana=2.
    COMBAT P1 Token hits P2 for 2.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=39 board=7 sources=7, P2 magnus life=38 board=7 sources=6, P3 midrange life=30 board=3 sources=5

========== ROUND 7 ==========
  P2 misses land drop.
  P2 (magnus) casts Archmage Emeritus [creature] for 4; mana=2.
    Archmage Emeritus enters battlefield (2/2).
    COMBAT P2 Magnus the Red hits P0 for 4.
    COMBAT P2 Spawn 3/3 into P3 midrange:medium:3 3/3.
  P3 land -> 4 lands.
  P3 (midrange) casts midrange:ramp:6 [artifact] for 3; mana=3.
  P3 (midrange) casts midrange:draw:2 [sorcery] for 2; mana=1.
  P1 (spellslinger) casts spellslinger:engine:6 [enchantment] for 3; mana=4.
    COMBAT P1 Token hits P2 for 2.
    COMBAT P1 Ape (Pongify) hits P2 for 3.
    COMBAT P1 Token hits P3 for 1.
    COMBAT P1 Token hits P3 for 1.
  P0 land -> 3 lands.
  P0 (control) casts control:ramp:6 [artifact] for 3; mana=0.
  End round: P0 control life=36 board=0 sources=4, P1 spellslinger life=39 board=9 sources=7, P2 magnus life=33 board=9 sources=6, P3 midrange life=28 board=0 sources=7

========== ROUND 8 ==========
  Steam Vents enters untapped; P2 pays 2 life.
  P2 plays Steam Vents (7 lands).
    COMBAT P2 Magnus the Red hits P1 for 4.
    COMBAT P2 Spawn hits P1 for 3.
  P3 land -> 5 lands.
  P3 (midrange) casts midrange:removal:6 [instant] for 3; mana=5.
  P3 (midrange) casts midrange:removal:2 [instant] for 3; mana=2.
  P1 (spellslinger) casts spellslinger:counter:3 [instant] for 2; mana=2.
    STACK: P1 casts spellslinger:counter:3 targeting midrange:removal:2.
    STACK: spellslinger:counter:3 counters midrange:removal:2.
    STACK: midrange:removal:2 is countered.
  P3 (midrange) casts midrange:small:1 [creature] for 1; mana=1.
  P1 (spellslinger) casts spellslinger:large:1 [creature] for 7; mana=0.
    COMBAT P1 Ape (Pongify) hits P0 for 3.
    COMBAT P1 Token hits P0 for 1.
    COMBAT P1 Token hits P0 for 1.
    COMBAT P1 spellslinger:engine:6 hits P2 for 2.
  P0 (control) casts control:engine:3 [enchantment] for 4; mana=0.
  End round: P0 control life=31 board=0 sources=4, P1 spellslinger life=32 board=18 sources=7, P2 magnus life=29 board=8 sources=7, P3 midrange life=28 board=2 sources=8

========== ROUND 9 ==========
  P2 misses land drop.
  P2 (magnus) casts Magnus the Red [creature] for 7; mana=0.
    Magnus the Red enters battlefield (4/5).
  P3 (midrange) casts midrange:removal:4 [instant] for 2; mana=6.
  P3 (midrange) casts midrange:tokens:0 [sorcery] for 3; mana=3.
    COMBAT P3 midrange:small:1 hits P2 for 2.
  P1 land -> 5 lands.
  P1 (spellslinger) casts spellslinger:engine:7 [enchantment] for 3; mana=5.
    COMBAT P1 Token hits P0 for 1.
    COMBAT P1 Token 1/1 into P3 Token 2/2.
  P0 land -> 4 lands.
  P0 (control) casts control:engine:2 [enchantment] for 4; mana=1.
  End round: P0 control life=30 board=2 sources=5, P1 spellslinger life=32 board=8 sources=8, P2 magnus life=27 board=12 sources=7, P3 midrange life=28 board=6 sources=8

========== ROUND 10 ==========
  P2 misses land drop.
  P2 (magnus) casts Storm-Kiln Artist [creature] for 4; mana=3.
  P3 (midrange) casts midrange:counter:0 [instant] for 2; mana=1.
    STACK: P3 casts midrange:counter:0 targeting Storm-Kiln Artist.
    STACK: midrange:counter:0 counters Storm-Kiln Artist.
    STACK: Storm-Kiln Artist is countered.
    COMBAT P2 Spawn hits P0 for 3.
    COMBAT P2 Magnus the Red hits P0 for 4.
  P3 (midrange) casts midrange:medium:8 [creature] for 3; mana=5.
  P3 (midrange) casts midrange:tokens:2 [sorcery] for 4; mana=1.
    COMBAT P3 midrange:small:1 hits P2 for 2.
    COMBAT P3 Token 2/2 into P1 spellslinger:engine:6 2/3.
    COMBAT P3 Token hits P2 for 2.
  P1 land -> 6 lands.
  P1 (spellslinger) casts spellslinger:removal:3 [instant] for 2; mana=7.
    COMBAT P1 Ape (Pongify) hits P2 for 3.
    COMBAT P1 Token 1/1 into P3 midrange:medium:8 3/3.
  P0 land -> 5 lands.
  P0 (control) casts control:engine:4 [enchantment] for 4; mana=2.
  End round: P0 control life=23 board=2 sources=6, P1 spellslinger life=32 board=8 sources=9, P2 magnus life=20 board=11 sources=7, P3 midrange life=28 board=9 sources=8
```

## Boundaries
Card-zone and typed-source services are tested separately; this live replay still uses legacy hand/library, mana, counter-only priority, and incomplete named-card effects.
