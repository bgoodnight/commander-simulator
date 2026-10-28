# V10 typed-priority diagnostic: 03_third_seat

Seed 103; Magnus seat 2; forced opening: False.
Result: turn_limit; safety stop: None.

Physical-card conservation, zone indexing and battlefield projections passed.

## Transcript

```text

========== ROUND 1 ==========
  P2 plays Island (1 lands).
  P3 plays midrange:land:3 (1 lands).
  P1 plays spellslinger:land:30 (1 lands).
  P0 plays control:land:27 (1 lands).
  End round: P0 control life=40 board=0 sources=1, P1 spellslinger life=40 board=0 sources=1, P2 magnus life=40 board=0 sources=1, P3 midrange life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 plays Island (2 lands).
  P3 plays midrange:land:36 (2 lands).
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
  P3 (midrange) casts midrange:ramp:3 [artifact] for 2; mana=0.
    STACK +1 [spell] P3: midrange:ramp:3.
  P1 plays spellslinger:land:1 (2 lands).
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:burn:1 [instant] for 2; mana=0.
    STACK +2 [spell] P1: spellslinger:burn:1.
  P0 plays control:land:16 (2 lands).
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=40 board=0 sources=2, P2 magnus life=40 board=0 sources=2, P3 midrange life=34 board=0 sources=3

========== ROUND 3 ==========
  P2 plays Mountain (3 lands).
    MANA P2: Island #441 -> (0, 1, 0)
    MANA P2: Mountain #461 -> (0, 0, 1)
  P2 (magnus) casts Third Path Iconoclast [creature] for 2; mana=1.
    STACK +3 [spell] P2: Third Path Iconoclast.
    Third Path Iconoclast enters battlefield (1/1).
  P3 plays midrange:land:5 (3 lands).
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
  P3 (midrange) casts midrange:ramp:7 [artifact] for 2; mana=2.
    STACK +4 [spell] P3: midrange:ramp:7.
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
    MANA P3: midrange:land:5 #465 -> (1, 0, 0)
    MANA P3: midrange:ramp:7 #467 -> (1, 0, 0)
  P3 (midrange) casts midrange:ramp:9 [artifact] for 3; mana=0.
    STACK +5 [spell] P3: midrange:ramp:9.
    MANA P3: midrange:ramp:9 #469 -> (1, 0, 0)
  P3 (midrange) casts midrange:small:3 [creature] for 1; mana=0.
    STACK +6 [spell] P3: midrange:small:3.
  P1 plays spellslinger:land:8 (3 lands).
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
    MANA P1: spellslinger:land:8 #473 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:ramp:6 [artifact] for 3; mana=0.
    STACK +7 [spell] P1: spellslinger:ramp:6.
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
  P0 (control) casts control:counter:1 [instant] for 2; mana=0.
    STACK +8 [spell] P0: control:counter:1.
    STACK -7: spellslinger:ramp:6 countered.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=40 board=0 sources=3, P2 magnus life=40 board=1 sources=3, P3 midrange life=34 board=2 sources=6

========== ROUND 4 ==========
  P2 plays Exotic Orchard (4 lands).
    MANA P2: Island #441 -> (0, 1, 0)
  P2 (magnus) casts Pongify [instant] for 1; mana=2.
    STACK +9 [spell] P2: Pongify.
    STACK +10 [triggered] P2: Third Path Iconoclast: create_token.
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
  P0 (control) casts control:counter:0 [instant] for 2; mana=0.
    STACK +11 [spell] P0: control:counter:0.
    MANA P2: Island #449 -> (0, 1, 0)
  P2 (magnus) casts Flusterstorm [instant] for 1; mana=1.
    STACK +12 [spell] P2: Flusterstorm.
    STACK +13 [triggered] P2: Third Path Iconoclast: create_token.
    STACK -11: control:counter:0 countered.
    Pongify destroys midrange:small:3; P3 gets a 3/3 Ape.
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
  P3 (midrange) casts midrange:ramp:1 [artifact] for 3; mana=3.
    STACK +14 [spell] P3: midrange:ramp:1.
    MANA P3: midrange:land:5 #465 -> (1, 0, 0)
    MANA P3: midrange:ramp:7 #467 -> (1, 0, 0)
  P3 (midrange) casts midrange:draw:1 [sorcery] for 2; mana=2.
    STACK +15 [spell] P3: midrange:draw:1.
  P1 plays spellslinger:land:24 (4 lands).
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
    MANA P1: spellslinger:land:8 #473 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:ramp:1 [artifact] for 3; mana=1.
    STACK +16 [spell] P1: spellslinger:ramp:1.
    MANA P1: spellslinger:land:24 #499 -> (1, 0, 0)
    MANA P1: spellslinger:ramp:1 #501 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:removal:0 [instant] for 2; mana=0.
    STACK +17 [spell] P1: spellslinger:removal:0.
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
  P0 (control) casts control:removal:4 [instant] for 2; mana=0.
    STACK +18 [spell] P0: control:removal:4.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=40 board=0 sources=5, P2 magnus life=40 board=3 sources=3, P3 midrange life=34 board=0 sources=6

========== ROUND 5 ==========
  P2 plays Riptide Laboratory (5 lands).
    COMBAT P2 Soldier hits P3 for 1.
    COMBAT P2 Soldier hits P1 for 1.
  P3 plays midrange:land:26 (4 lands).
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
  P3 (midrange) casts midrange:small:0 [creature] for 2; mana=5.
    STACK +19 [spell] P3: midrange:small:0.
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
    MANA P3: midrange:land:5 #465 -> (1, 0, 0)
    MANA P3: midrange:ramp:7 #467 -> (1, 0, 0)
  P3 (midrange) casts midrange:removal:6 [instant] for 3; mana=2.
    STACK +20 [spell] P3: midrange:removal:6.
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
    MANA P1: spellslinger:land:8 #473 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:ramp:2 [artifact] for 3; mana=2.
    STACK +21 [spell] P1: spellslinger:ramp:2.
    MANA P1: spellslinger:land:24 #499 -> (1, 0, 0)
    MANA P1: spellslinger:ramp:1 #501 -> (1, 0, 0)
    MANA P1: spellslinger:ramp:2 #518 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:tokens:2 [sorcery] for 3; mana=0.
    STACK +22 [spell] P1: spellslinger:tokens:2.
  End round: P0 control life=40 board=0 sources=2, P1 spellslinger life=39 board=4 sources=6, P2 magnus life=40 board=2 sources=4, P3 midrange life=33 board=1 sources=7

========== ROUND 6 ==========
  P2 plays Mountain (6 lands).
    MANA P2: Island #441 -> (0, 1, 0)
    MANA P2: Island #449 -> (0, 1, 0)
    MANA P2: Mountain #461 -> (0, 0, 1)
    MANA P2: Mountain #525 -> (0, 0, 1)
    MANA P2: Riptide Laboratory #509 -> (1, 0, 0)
  P2 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    STACK +23 [spell] P2: Magnus the Red.
    Magnus the Red enters battlefield (4/5).
    COMBAT P2 Soldier hits P0 for 1.
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
  P3 (midrange) casts midrange:medium:3 [creature] for 3; mana=4.
    STACK +24 [spell] P3: midrange:medium:3.
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:combo_piece:0 [artifact] for 2; mana=4.
    STACK +25 [spell] P1: spellslinger:combo_piece:0.
    MANA P1: spellslinger:land:8 #473 -> (1, 0, 0)
    MANA P1: spellslinger:land:24 #499 -> (1, 0, 0)
    MANA P1: spellslinger:ramp:1 #501 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:tokens:4 [sorcery] for 3; mana=1.
    STACK +26 [spell] P1: spellslinger:tokens:4.
    COMBAT P1 Token 2/2 into P3 midrange:medium:3 3/3.
    COMBAT P1 Token hits P0 for 2.
  End round: P0 control life=37 board=0 sources=2, P1 spellslinger life=39 board=4 sources=6, P2 magnus life=40 board=6 sources=5, P3 midrange life=33 board=4 sources=7

========== ROUND 7 ==========
    MANA P2: Island #441 -> (0, 1, 0)
    MANA P2: Island #449 -> (0, 1, 0)
    MANA P2: Mountain #461 -> (0, 0, 1)
    MANA P2: Mountain #525 -> (0, 0, 1)
  P2 (magnus) casts Archmage Emeritus [creature] for 4; mana=1.
    STACK +27 [spell] P2: Archmage Emeritus.
    Archmage Emeritus enters battlefield (2/2).
    COMBAT P2 Magnus the Red hits P3 for 4.
    STACK +28 [triggered] P2: Magnus the Red: create_token.
  P3 plays midrange:land:34 (5 lands).
    COMBAT P3 midrange:small:0 hits P2 for 1.
    COMBAT P3 midrange:medium:3 hits P0 for 3.
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
    MANA P1: spellslinger:land:8 #473 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:engine:6 [enchantment] for 3; mana=3.
    STACK +29 [spell] P1: spellslinger:engine:6.
    COMBAT P1 Token hits P3 for 2.
    COMBAT P1 Token hits P2 for 1.
    COMBAT P1 Token hits P3 for 1.
  P0 plays control:land:14 (3 lands).
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
    MANA P0: control:land:14 #550 -> (1, 0, 0)
  P0 (control) casts control:ramp:6 [artifact] for 3; mana=0.
    STACK +30 [spell] P0: control:ramp:6.
  End round: P0 control life=34 board=0 sources=4, P1 spellslinger life=39 board=6 sources=6, P2 magnus life=38 board=11 sources=5, P3 midrange life=26 board=4 sources=8

========== ROUND 8 ==========
  P2 pays 2 life for Steam Vents.
  P2 plays Steam Vents (7 lands).
    COMBAT P2 Spawn hits P3 for 3.
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
  P3 (midrange) casts midrange:tokens:1 [sorcery] for 3; mana=5.
    STACK +31 [spell] P3: midrange:tokens:1.
    MANA P1: spellslinger:land:24 #499 -> (1, 0, 0)
    MANA P1: spellslinger:ramp:1 #501 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:counter:3 [instant] for 2; mana=1.
    STACK +32 [spell] P1: spellslinger:counter:3.
    MANA P3: midrange:land:5 #465 -> (1, 0, 0)
    MANA P3: midrange:ramp:7 #467 -> (1, 0, 0)
  P3 (midrange) casts midrange:counter:0 [instant] for 2; mana=3.
    STACK +33 [spell] P3: midrange:counter:0.
    STACK -32: spellslinger:counter:3 countered.
    COMBAT P3 midrange:small:0 hits P1 for 1.
    COMBAT P3 midrange:medium:3 hits P0 for 3.
    COMBAT P1 Token hits P2 for 2.
    COMBAT P1 Token hits P0 for 1.
    COMBAT P1 spellslinger:engine:6 hits P0 for 2.
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
    MANA P0: control:land:14 #550 -> (1, 0, 0)
    MANA P0: control:ramp:6 #552 -> (1, 0, 0)
  P0 (control) casts control:engine:3 [enchantment] for 4; mana=0.
    STACK +34 [spell] P0: control:engine:3.
  End round: P0 control life=28 board=0 sources=4, P1 spellslinger life=38 board=6 sources=6, P2 magnus life=34 board=11 sources=6, P3 midrange life=23 board=10 sources=8

========== ROUND 9 ==========
    MANA P2: Island #441 -> (0, 1, 0)
    MANA P2: Island #449 -> (0, 1, 0)
    MANA P2: Mountain #461 -> (0, 0, 1)
    MANA P2: Mountain #525 -> (0, 0, 1)
  P2 (magnus) casts Storm-Kiln Artist [creature] for 4; mana=2.
    STACK +35 [spell] P2: Storm-Kiln Artist.
    Storm-Kiln Artist enters battlefield (2/2).
    COMBAT P2 Magnus the Red hits P1 for 4.
    STACK +36 [triggered] P2: Magnus the Red: create_token.
    COMBAT P2 Spawn hits P0 for 3.
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
  P3 (midrange) casts midrange:removal:0 [instant] for 3; mana=5.
    STACK +37 [spell] P3: midrange:removal:0.
    COMBAT P3 midrange:small:0 hits P2 for 1.
    COMBAT P3 midrange:medium:3 hits P2 for 3.
    COMBAT P3 Token hits P2 for 2.
    COMBAT P3 Token hits P2 for 2.
    COMBAT P3 Token hits P2 for 2.
  P1 plays spellslinger:land:14 (5 lands).
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
    MANA P1: spellslinger:land:8 #473 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:engine:7 [enchantment] for 3; mana=4.
    STACK +38 [spell] P1: spellslinger:engine:7.
    COMBAT P1 Token hits P0 for 2.
  P0 plays control:land:13 (4 lands).
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
    MANA P0: control:land:14 #550 -> (1, 0, 0)
    MANA P0: control:ramp:6 #552 -> (1, 0, 0)
  P0 (control) casts control:engine:2 [enchantment] for 4; mana=1.
    STACK +39 [spell] P0: control:engine:2.
  End round: P0 control life=23 board=2 sources=5, P1 spellslinger life=34 board=7 sources=7, P2 magnus life=24 board=16 sources=6, P3 midrange life=23 board=10 sources=8

========== ROUND 10 ==========
    COMBAT P2 Soldier hits P3 for 1.
    COMBAT P2 Spawn hits P3 for 3.
    COMBAT P2 Spawn hits P0 for 3.
  P3 plays midrange:land:8 (6 lands).
    MANA P3: midrange:land:3 #443 -> (1, 0, 0)
    MANA P3: midrange:land:36 #451 -> (1, 0, 0)
    MANA P3: midrange:ramp:3 #453 -> (1, 0, 0)
    MANA P3: midrange:land:5 #465 -> (1, 0, 0)
    MANA P3: midrange:ramp:7 #467 -> (1, 0, 0)
    MANA P3: midrange:ramp:1 #493 -> (1, 0, 0)
    MANA P3: midrange:land:26 #511 -> (1, 0, 0)
  P3 (midrange) casts midrange:finisher:0 [sorcery] for 7; mana=2.
    STACK +40 [spell] P3: midrange:finisher:0.
    COMBAT P3 midrange:medium:3 hits P1 for 5.
    COMBAT P3 Token 4/2 into P1 spellslinger:engine:6 2/3.
    COMBAT P3 Token hits P2 for 4.
  P1 plays spellslinger:land:23 (6 lands).
    MANA P1: spellslinger:land:30 #445 -> (1, 0, 0)
    MANA P1: spellslinger:land:1 #455 -> (1, 0, 0)
  P1 (spellslinger) casts spellslinger:removal:3 [instant] for 2; mana=6.
    STACK +41 [spell] P1: spellslinger:removal:3.
    COMBAT P1 Token hits P2 for 1.
    COMBAT P1 Token 1/1 into P3 midrange:small:0 3/3.
    COMBAT P1 engine token 1/1 into P3 Token 4/2.
  P0 plays control:land:24 (5 lands).
    MANA P0: control:land:27 #447 -> (1, 0, 0)
    MANA P0: control:land:16 #459 -> (1, 0, 0)
    MANA P0: control:land:14 #550 -> (1, 0, 0)
    MANA P0: control:ramp:6 #552 -> (1, 0, 0)
  P0 (control) casts control:engine:4 [enchantment] for 4; mana=2.
    STACK +42 [spell] P0: control:engine:4.
  End round: P0 control life=20 board=2 sources=6, P1 spellslinger life=29 board=3 sources=8, P2 magnus life=19 board=13 sources=6, P3 midrange life=19 board=16 sources=9
```

## Boundaries

Mana uses physical source IDs with ordered activations. Spells, triggers and registered activations use typed priority; coarse steps, land rules and synthetic abilities remain approximate. No deck-power conclusions.
