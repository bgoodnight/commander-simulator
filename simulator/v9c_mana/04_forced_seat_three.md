# V9c source-mana diagnostic: 04_forced_seat_three

Seed 404; Magnus seat 3; forced opening: True.
Result: turn_limit; safety stop: None.

Physical-card conservation, zone indexing and battlefield projections passed.

## Transcript

```text

========== ROUND 1 ==========
  P1 plays combo:land:10 (1 lands).
  P2 plays tokens:land:23 (1 lands).
  P3 plays Island (1 lands).
    MANA P3: Island #455 -> (0, 1, 0)
  P3 (magnus) casts Sol Ring [artifact] for 1; mana=0.
    Sol Ring enters untapped; its mana ability is immediately available.
  P0 plays control:land:7 (1 lands).
    MANA P0: control:land:7 #459 -> (1, 0, 0)
  P0 (control) casts control:small:0 [creature] for 1; mana=0.
  End round: P0 control life=40 board=1 sources=1, P1 combo life=40 board=0 sources=1, P2 tokens life=40 board=0 sources=1, P3 magnus life=40 board=0 sources=3

========== ROUND 2 ==========
  P1 plays combo:land:29 (2 lands).
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
  P1 (combo) casts combo:engine:2 [enchantment] for 2; mana=0.
  P2 plays tokens:land:12 (2 lands).
    MANA P3: Island #455 -> (0, 1, 0)
  P3 (magnus) casts Ponder [sorcery] for 1; mana=2.
    Ponder: partial card selection (1 drawn; exact look/scry/untap not modeled).
  P0 plays control:land:8 (2 lands).
    MANA P0: control:land:7 #459 -> (1, 0, 0)
    MANA P0: control:land:8 #473 -> (1, 0, 0)
  P0 (control) casts control:ramp:6 [artifact] for 2; mana=0.
    COMBAT P0 control:small:0 hits P1 for 1.
  End round: P0 control life=40 board=1 sources=3, P1 combo life=39 board=2 sources=2, P2 tokens life=40 board=0 sources=2, P3 magnus life=40 board=0 sources=3

========== ROUND 3 ==========
  P1 plays combo:land:4 (3 lands).
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
    MANA P1: combo:land:4 #479 -> (1, 0, 0)
  P1 (combo) casts combo:engine:7 [enchantment] for 3; mana=0.
    COMBAT P1 combo:engine:2 hits P0 for 2.
  P2 plays tokens:land:22 (3 lands).
  P3 plays Spirebluff Canal (2 lands).
    MANA P3: Island #455 -> (0, 1, 0)
    MANA P3: Spirebluff Canal #485 -> (0, 0, 1)
  P3 (magnus) casts Young Pyromancer [creature] for 2; mana=2.
    Young Pyromancer enters battlefield (2/1).
  P0 plays control:land:19 (3 lands).
    MANA P0: control:land:7 #459 -> (1, 0, 0)
    MANA P0: control:land:8 #473 -> (1, 0, 0)
    MANA P0: control:ramp:6 #475 -> (1, 0, 0)
  P0 (control) casts control:ramp:7 [artifact] for 3; mana=1.
    MANA P0: control:land:19 #489 -> (1, 0, 0)
    MANA P0: control:ramp:7 #491 -> (2, 0, 0)
  P0 (control) casts control:medium:1 [creature] for 3; mana=0.
    COMBAT P0 control:small:0 hits P1 for 1.
  End round: P0 control life=38 board=5 sources=6, P1 combo life=38 board=5 sources=3, P2 tokens life=40 board=0 sources=3, P3 magnus life=40 board=2 sources=4

========== ROUND 4 ==========
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
  P1 (combo) casts combo:draw:8 [sorcery] for 2; mana=1.
  P2 plays tokens:land:16 (4 lands).
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:2 [enchantment] for 4; mana=0.
  P3 plays Mountain (3 lands).
    MANA P3: Island #455 -> (0, 1, 0)
    MANA P3: Spirebluff Canal #485 -> (0, 0, 1)
  P3 (magnus) casts Harmonic Prodigy [creature] for 2; mana=3.
    Harmonic Prodigy enters battlefield (1/3).
  P0 plays control:land:28 (4 lands).
    MANA P0: control:land:7 #459 -> (1, 0, 0)
    MANA P0: control:ramp:7 #491 -> (2, 0, 0)
  P0 (control) casts control:engine:1 [enchantment] for 3; mana=4.
    MANA P0: control:land:8 #473 -> (1, 0, 0)
    MANA P0: control:ramp:6 #475 -> (1, 0, 0)
    MANA P0: control:land:19 #489 -> (1, 0, 0)
  P0 (control) casts control:medium:3 [creature] for 3; mana=1.
  End round: P0 control life=38 board=9 sources=7, P1 combo life=38 board=5 sources=3, P2 tokens life=40 board=0 sources=4, P3 magnus life=40 board=3 sources=5

========== ROUND 5 ==========
  P1 plays combo:land:3 (4 lands).
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
  P1 (combo) casts combo:draw:10 [sorcery] for 2; mana=2.
    MANA P1: combo:land:4 #479 -> (1, 0, 0)
    MANA P1: combo:land:3 #520 -> (1, 0, 0)
  P1 (combo) casts combo:ramp:6 [artifact] for 2; mana=0.
    MANA P1: combo:ramp:6 #527 -> (2, 0, 0)
  P1 (combo) casts combo:draw:3 [sorcery] for 2; mana=0.
    COMBAT P1 combo:engine:7 hits P2 for 2.
  P2 plays tokens:land:0 (5 lands).
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:8 [enchantment] for 4; mana=1.
    MANA P2: tokens:land:0 #537 -> (1, 0, 0)
  P2 (tokens) casts tokens:small:4 [creature] for 1; mana=0.
  P3 plays Mountain (4 lands).
    MANA P3: Island #455 -> (0, 1, 0)
    MANA P3: Sol Ring #457 -> (2, 0, 0)
    MANA P3: Spirebluff Canal #485 -> (0, 1, 0)
    MANA P3: Mountain #507 -> (0, 0, 1)
  P3 (magnus) casts Magnus the Red [creature] for 5; mana=1.
    Magnus the Red enters battlefield (4/5).
  P0 plays control:land:3 (5 lands).
    MANA P0: control:ramp:7 #491 -> (2, 0, 0)
  P0 (control) casts control:removal:0 [instant] for 2; mana=6.
    COMBAT P0 control:medium:3 hits P1 for 4.
  End round: P0 control life=38 board=10 sources=8, P1 combo life=34 board=6 sources=6, P2 tokens life=38 board=3 sources=5, P3 magnus life=40 board=3 sources=6

========== ROUND 6 ==========
  P1 plays combo:land:34 (5 lands).
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:ramp:6 #527 -> (2, 0, 0)
  P1 (combo) casts combo:ramp:4 [artifact] for 3; mana=4.
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
    MANA P1: combo:land:4 #479 -> (1, 0, 0)
  P1 (combo) casts combo:draw:9 [sorcery] for 2; mana=3.
    MANA P1: combo:land:3 #520 -> (1, 0, 0)
    MANA P1: combo:land:34 #555 -> (1, 0, 0)
    MANA P1: combo:ramp:4 #557 -> (1, 0, 0)
  P1 (combo) casts combo:draw:0 [sorcery] for 3; mana=0.
    COMBAT P1 engine token 1/1 into P2 tokens:small:4 3/2.
  P2 plays tokens:land:31 (6 lands).
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:1 [enchantment] for 3; mana=3.
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
    MANA P2: tokens:land:0 #537 -> (1, 0, 0)
  P2 (tokens) casts tokens:buff:3 [sorcery] for 2; mana=1.
    COMBAT P2 tokens:small:4 4/2 into P1 combo:engine:2 2/3.
    MANA P3: Island #455 -> (0, 1, 0)
  P3 (magnus) casts Preordain [sorcery] for 1; mana=5.
    Preordain: partial card selection (1 drawn; exact look/scry/untap not modeled).
  P0 plays control:land:4 (6 lands).
    COMBAT P0 control:medium:1 hits P2 for 4.
  End round: P0 control life=38 board=11 sources=9, P1 combo life=34 board=3 sources=8, P2 tokens life=34 board=0 sources=6, P3 magnus life=40 board=5 sources=6

========== ROUND 7 ==========
  P1 plays combo:land:28 (6 lands).
    MANA P1: combo:ramp:6 #527 -> (2, 0, 0)
  P1 (combo) casts combo:ramp:7 [artifact] for 2; mana=7.
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
  P1 (combo) casts combo:ramp:0 [artifact] for 2; mana=6.
    MANA P1: combo:land:4 #479 -> (1, 0, 0)
    MANA P1: combo:land:3 #520 -> (1, 0, 0)
    MANA P1: combo:land:34 #555 -> (1, 0, 0)
  P1 (combo) casts combo:combo_piece:1 [artifact] for 3; mana=4.
    MANA P1: combo:ramp:4 #557 -> (1, 0, 0)
    MANA P1: combo:land:28 #590 -> (1, 0, 0)
    MANA P1: combo:ramp:7 #592 -> (1, 0, 0)
  P1 (combo) casts combo:medium:2 [creature] for 3; mana=1.
    COMBAT P1 engine token 1/1 into P0 control:small:0 1/3.
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:4 [enchantment] for 4; mana=2.
  P3 plays Cascade Bluffs (5 lands).
    MANA P3: Island #455 -> (0, 1, 0)
    MANA P3: Sol Ring #457 -> (2, 0, 0)
    MANA P3: Spirebluff Canal #485 -> (0, 1, 0)
    MANA P3: Mountain #507 -> (0, 0, 1)
    MANA P3: Mountain #543 -> (0, 0, 1)
    MANA P3: Cascade Bluffs #605 -> (1, 0, 0)
  P3 (magnus) casts Magnus the Red [creature] for 7; mana=0.
    Magnus the Red enters battlefield (4/5).
  P0 plays control:land:0 (7 lands).
    COMBAT P0 control:small:0 hits P3 for 1.
    COMBAT P0 control:medium:3 hits P2 for 4.
  End round: P0 control life=38 board=11 sources=10, P1 combo life=34 board=6 sources=11, P2 tokens life=30 board=2 sources=6, P3 magnus life=39 board=9 sources=7

========== ROUND 8 ==========
  P1 plays combo:land:9 (7 lands).
    MANA P1: combo:ramp:6 #527 -> (2, 0, 0)
  P1 (combo) casts combo:ramp:8 [artifact] for 2; mana=10.
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
    MANA P1: combo:land:4 #479 -> (1, 0, 0)
  P1 (combo) casts combo:draw:5 [sorcery] for 3; mana=8.
    MANA P1: combo:land:3 #520 -> (1, 0, 0)
    MANA P1: combo:land:34 #555 -> (1, 0, 0)
  P1 (combo) casts combo:draw:11 [sorcery] for 2; mana=6.
    MANA P1: combo:ramp:4 #557 -> (1, 0, 0)
    MANA P1: combo:land:28 #590 -> (1, 0, 0)
  P1 (combo) casts combo:removal:2 [instant] for 2; mana=4.
    MANA P1: combo:ramp:7 #592 -> (1, 0, 0)
    MANA P1: combo:ramp:0 #594 -> (1, 0, 0)
  P1 (combo) casts combo:removal:4 [instant] for 2; mana=2.
    COMBAT P1 combo:medium:2 hits P2 for 4.
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
  P2 (tokens) casts tokens:tokens:0 [sorcery] for 3; mana=3.
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
  P2 (tokens) casts tokens:small:1 [creature] for 1; mana=2.
    COMBAT P2 engine token 1/1 into P1 combo:engine:7 2/3.
  P3 plays Island (6 lands).
    MANA P3: Sol Ring #457 -> (2, 0, 0)
  P3 (magnus) casts Mind Stone [artifact] for 2; mana=6.
    Mind Stone enters untapped; its mana ability is immediately available.
    COMBAT P3 Magnus the Red hits P1 for 4.
  P0 plays control:land:12 (8 lands).
    COMBAT P0 engine token 1/1 into P1 combo:engine:7 2/3.
  End round: P0 control life=38 board=9 sources=11, P1 combo life=30 board=7 sources=13, P2 tokens life=26 board=4 sources=6, P3 magnus life=39 board=12 sources=9

========== ROUND 9 ==========
  P1 plays combo:land:21 (8 lands).
    MANA P1: combo:land:10 #451 -> (1, 0, 0)
    MANA P1: combo:land:29 #463 -> (1, 0, 0)
    MANA P1: combo:land:4 #479 -> (1, 0, 0)
    MANA P1: combo:land:3 #520 -> (1, 0, 0)
    MANA P1: combo:land:34 #555 -> (1, 0, 0)
    MANA P1: combo:ramp:6 #527 -> (2, 0, 0)
  P1 (combo) casts combo:large:0 [creature] for 7; mana=7.
    COMBAT P1 combo:medium:2 hits P3 for 4.
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
  P2 (tokens) casts tokens:tokens:9 [sorcery] for 4; mana=2.
    MANA P2: tokens:land:0 #537 -> (1, 0, 0)
    MANA P2: tokens:land:31 #573 -> (1, 0, 0)
  P2 (tokens) casts tokens:draw:3 [sorcery] for 2; mana=0.
    COMBAT P2 Token 1/1 into P1 combo:engine:7 2/3.
    COMBAT P2 Token 1/1 into P1 combo:large:0 9/8.
    COMBAT P2 tokens:small:1 hits P3 for 1.
    COMBAT P3 Magnus the Red hits P1 for 4.
    MANA P0: control:ramp:7 #491 -> (2, 0, 0)
  P0 (control) casts control:draw:3 [sorcery] for 2; mana=9.
    MANA P0: control:land:7 #459 -> (1, 0, 0)
    MANA P0: control:land:8 #473 -> (1, 0, 0)
  P0 (control) casts control:removal:7 [instant] for 2; mana=7.
    MANA P0: control:ramp:6 #475 -> (1, 0, 0)
    MANA P0: control:land:19 #489 -> (1, 0, 0)
    MANA P0: control:land:28 #511 -> (1, 0, 0)
    MANA P0: control:land:3 #548 -> (1, 0, 0)
    MANA P0: control:land:4 #588 -> (1, 0, 0)
    MANA P0: control:land:0 #609 -> (1, 0, 0)
  P0 (control) casts control:wipe:1 [sorcery] for 6; mana=1.
    Board wipe removes 19 creatures.
  End round: P0 control life=38 board=0 sources=11, P1 combo life=26 board=0 sources=14, P2 tokens life=26 board=0 sources=6, P3 magnus life=34 board=0 sources=9

========== ROUND 10 ==========
  P1 plays combo:land:32 (9 lands).
  P2 plays tokens:land:11 (7 lands).
    MANA P2: tokens:land:23 #453 -> (1, 0, 0)
    MANA P2: tokens:land:12 #467 -> (1, 0, 0)
    MANA P2: tokens:land:22 #483 -> (1, 0, 0)
    MANA P2: tokens:land:16 #503 -> (1, 0, 0)
  P2 (tokens) casts tokens:tokens:16 [sorcery] for 4; mana=3.
    MANA P2: tokens:land:0 #537 -> (1, 0, 0)
    MANA P2: tokens:land:31 #573 -> (1, 0, 0)
  P2 (tokens) casts tokens:small:3 [creature] for 2; mana=1.
  P3 plays Island (7 lands).
    MANA P3: Island #455 -> (0, 1, 0)
    MANA P3: Island #639 -> (0, 1, 0)
    MANA P3: Island #697 -> (0, 1, 0)
    MANA P3: Sol Ring #457 -> (2, 0, 0)
    MANA P3: Spirebluff Canal #485 -> (0, 1, 0)
    MANA P3: Mountain #507 -> (0, 0, 1)
    MANA P3: Mountain #543 -> (0, 0, 1)
    MANA P3: Cascade Bluffs #605 -> (1, 0, 0)
  P3 (magnus) casts Magnus the Red [creature] for 9; mana=1.
    Magnus the Red enters battlefield (4/5).
    MANA P0: control:land:7 #459 -> (1, 0, 0)
    MANA P0: control:ramp:7 #491 -> (2, 0, 0)
  P0 (control) casts control:engine:3 [enchantment] for 3; mana=8.
    MANA P0: control:land:8 #473 -> (1, 0, 0)
    MANA P0: control:ramp:6 #475 -> (1, 0, 0)
    MANA P0: control:land:19 #489 -> (1, 0, 0)
    MANA P0: control:land:28 #511 -> (1, 0, 0)
    MANA P0: control:land:3 #548 -> (1, 0, 0)
    MANA P0: control:land:4 #588 -> (1, 0, 0)
    MANA P0: control:land:0 #609 -> (1, 0, 0)
  P0 (control) casts control:large:2 [creature] for 7; mana=1.
  End round: P0 control life=38 board=9 sources=11, P1 combo life=26 board=0 sources=15, P2 tokens life=26 board=6 sources=7, P3 magnus life=34 board=4 sources=10
```

## Boundaries

Mana uses physical source IDs with ordered activations. Priority remains counter-only; selection, land rules and synthetic abilities remain approximate. No deck-power conclusions.
