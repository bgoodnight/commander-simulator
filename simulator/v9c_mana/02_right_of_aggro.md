# V9c source-mana diagnostic: 02_right_of_aggro

Seed 104; Magnus seat 1; forced opening: False.
Result: combat; safety stop: None.

Physical-card conservation, zone indexing and battlefield projections passed.

## Transcript

```text

========== ROUND 1 ==========
  P1 plays Island (1 lands).
    MANA P1: Island #427 -> (0, 1, 0)
  P1 (magnus) casts Brainstorm [instant] for 1; mana=0.
    Brainstorm: partial card selection (3 drawn; exact look/scry/untap not modeled).
  P0 plays aggro:land:15 (1 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
  P0 (aggro) casts aggro:small:14 [creature] for 1; mana=0.
  P3 plays ramp_stompy:land:12 (1 lands).
  P2 plays tokens:land:27 (1 lands).
  End round: P0 aggro life=40 board=1 sources=1, P1 magnus life=40 board=0 sources=1, P2 tokens life=40 board=0 sources=1, P3 ramp_stompy life=40 board=0 sources=1

========== ROUND 2 ==========
  P1 plays Mountain (2 lands).
    MANA P1: Island #427 -> (0, 1, 0)
  P1 (magnus) casts Pongify [instant] for 1; mana=1.
    Pongify destroys aggro:small:14; P0 gets a 3/3 Ape.
  P0 plays aggro:land:31 (2 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
  P0 (aggro) casts aggro:small:13 [creature] for 2; mana=0.
  P3 plays ramp_stompy:land:8 (2 lands).
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:ramp:14 [artifact] for 2; mana=0.
  P2 plays tokens:land:31 (2 lands).
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
  P2 (tokens) casts tokens:ramp:5 [artifact] for 2; mana=0.
  End round: P0 aggro life=40 board=4 sources=2, P1 magnus life=40 board=0 sources=2, P2 tokens life=40 board=0 sources=3, P3 ramp_stompy life=40 board=0 sources=3

========== ROUND 3 ==========
  P1 plays Stormcarved Coast (3 lands).
  P0 plays aggro:land:16 (3 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
  P0 (aggro) casts aggro:small:10 [creature] for 1; mana=2.
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
    MANA P0: aggro:land:16 #464 -> (1, 0, 0)
  P0 (aggro) casts aggro:buff:0 [sorcery] for 2; mana=0.
    COMBAT P0 Ape (Pongify) hits P1 for 4.
  P3 plays ramp_stompy:land:1 (3 lands).
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:14 #456 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:1 #470 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:engine:0 [enchantment] for 4; mana=0.
  P2 plays tokens:land:8 (3 lands).
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:1 [enchantment] for 2; mana=2.
    MANA P2: tokens:ramp:5 #460 -> (1, 0, 0)
    MANA P2: tokens:land:8 #474 -> (1, 0, 0)
  P2 (tokens) casts tokens:small:0 [creature] for 2; mana=0.
  End round: P0 aggro life=40 board=8 sources=3, P1 magnus life=36 board=0 sources=3, P2 tokens life=40 board=5 sources=4, P3 ramp_stompy life=40 board=0 sources=4

========== ROUND 4 ==========
  P1 plays Command Tower (4 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
    MANA P0: aggro:land:16 #464 -> (1, 0, 0)
  P0 (aggro) casts aggro:medium:1 [creature] for 3; mana=0.
    COMBAT P0 Ape (Pongify) 4/3 into P2 tokens:small:0 3/1.
    COMBAT P0 aggro:small:13 2/2 into P2 tokens:engine:1 2/3.
    COMBAT P0 aggro:small:10 hits P3 for 2.
  P3 plays ramp_stompy:land:36 (4 lands).
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:14 #456 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:1 #470 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:medium:6 [creature] for 4; mana=1.
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
    MANA P2: tokens:ramp:5 #460 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:2 [enchantment] for 3; mana=1.
  End round: P0 aggro life=40 board=7 sources=3, P1 magnus life=36 board=0 sources=4, P2 tokens life=40 board=2 sources=4, P3 ramp_stompy life=38 board=5 sources=5

========== ROUND 5 ==========
  P1 plays Riptide Laboratory (5 lands).
    MANA P1: Island #427 -> (0, 1, 0)
    MANA P1: Mountain #444 -> (0, 0, 1)
    MANA P1: Stormcarved Coast #462 -> (0, 1, 0)
    MANA P1: Command Tower #480 -> (0, 1, 0)
    MANA P1: Riptide Laboratory #496 -> (1, 0, 0)
  P1 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    Magnus the Red enters battlefield (4/5).
  P0 plays aggro:land:23 (4 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
    MANA P0: aggro:land:16 #464 -> (1, 0, 0)
  P0 (aggro) casts aggro:medium:5 [creature] for 3; mana=1.
    COMBAT P0 aggro:small:10 hits P2 for 2.
    COMBAT P0 aggro:medium:1 hits P3 for 5.
  P3 plays ramp_stompy:land:5 (5 lands).
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:14 #456 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:1 #470 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:medium:1 [creature] for 4; mana=2.
    COMBAT P3 engine token 1/1 into P0 aggro:medium:5 5/5.
    COMBAT P3 ramp_stompy:medium:6 hits P1 for 4.
  P2 plays tokens:land:33 (4 lands).
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
    MANA P2: tokens:ramp:5 #460 -> (1, 0, 0)
    MANA P2: tokens:land:8 #474 -> (1, 0, 0)
    MANA P2: tokens:land:33 #510 -> (1, 0, 0)
  P2 (tokens) casts tokens:tokens:2 [sorcery] for 5; mana=0.
    COMBAT P2 tokens:engine:1 2/3 into P0 aggro:medium:5 5/5.
  End round: P0 aggro life=40 board=12 sources=4, P1 magnus life=32 board=4 sources=5, P2 tokens life=38 board=5 sources=5, P3 ramp_stompy life=33 board=8 sources=6

========== ROUND 6 ==========
  P1 plays Riverglide Pathway [U] (6 lands).
    COMBAT P1 Magnus the Red hits P3 for 4.
  P0 plays aggro:land:30 (5 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
    MANA P0: aggro:land:16 #464 -> (1, 0, 0)
    MANA P0: aggro:land:23 #500 -> (1, 0, 0)
  P0 (aggro) casts aggro:tokens:3 [sorcery] for 4; mana=1.
    COMBAT P0 aggro:small:10 2/3 into P3 ramp_stompy:medium:1 4/4.
    COMBAT P0 aggro:medium:1 hits P1 for 5.
    COMBAT P0 aggro:medium:5 hits P3 for 5.
  P3 plays ramp_stompy:land:4 (6 lands).
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:14 #456 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:1 #470 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:36 #489 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:5 #504 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:4 #532 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:large:4 [creature] for 7; mana=0.
    COMBAT P3 ramp_stompy:medium:6 hits P1 for 4.
    COMBAT P3 ramp_stompy:medium:1 hits P2 for 4.
  P2 plays tokens:land:13 (5 lands).
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
    MANA P2: tokens:ramp:5 #460 -> (1, 0, 0)
  P2 (tokens) casts tokens:buff:1 [sorcery] for 3; mana=3.
    MANA P2: tokens:land:8 #474 -> (1, 0, 0)
    MANA P2: tokens:land:33 #510 -> (1, 0, 0)
  P2 (tokens) casts tokens:removal:2 [instant] for 2; mana=1.
    COMBAT P2 engine token 3/1 into P0 Token 2/2.
    COMBAT P2 Token 3/1 into P0 Token 2/2.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:large:4 6/6.
    COMBAT P2 Token hits P3 for 3.
    COMBAT P2 Token hits P1 for 3.
  End round: P0 aggro life=40 board=12 sources=5, P1 magnus life=20 board=7 sources=6, P2 tokens life=34 board=6 sources=6, P3 ramp_stompy life=21 board=14 sources=7

========== ROUND 7 ==========
    COMBAT P1 Magnus the Red hits P3 for 4.
    COMBAT P1 Spawn hits P0 for 3.
  P0 plays aggro:land:14 (6 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
  P0 (aggro) casts aggro:engine:2 [enchantment] for 2; mana=4.
    COMBAT P0 aggro:medium:1 hits P3 for 5.
    COMBAT P0 aggro:medium:5 hits P2 for 5.
    COMBAT P0 Token hits P2 for 2.
  P3 plays ramp_stompy:land:35 (7 lands).
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:ramp:5 [artifact] for 2; mana=6.
    MANA P3: ramp_stompy:ramp:14 #456 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:1 #470 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:36 #489 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:5 #551 -> (2, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:large:2 [creature] for 5; mana=3.
    MANA P3: ramp_stompy:land:5 #504 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:4 #532 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:35 #549 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:tokens:1 [sorcery] for 3; mana=0.
    COMBAT P3 ramp_stompy:medium:1 hits P2 for 4.
    COMBAT P3 ramp_stompy:large:4 hits P0 for 6.
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
  P2 (tokens) casts tokens:engine:8 [enchantment] for 2; mana=4.
    MANA P2: tokens:ramp:5 #460 -> (1, 0, 0)
    MANA P2: tokens:land:8 #474 -> (1, 0, 0)
    MANA P2: tokens:land:33 #510 -> (1, 0, 0)
  P2 (tokens) casts tokens:removal:3 [instant] for 3; mana=1.
    COMBAT P2 Token 3/1 into P3 ramp_stompy:large:2 7/6.
  End round: P0 aggro life=31 board=7 sources=6, P1 magnus life=20 board=10 sources=6, P2 tokens life=23 board=4 sources=6, P3 ramp_stompy life=12 board=25 sources=10

========== ROUND 8 ==========
    MANA P1: Island #427 -> (0, 1, 0)
    MANA P1: Riverglide Pathway #519 -> (0, 1, 0)
  P1 (magnus) casts Baral, Chief of Compliance [creature] for 2; mana=4.
    Baral, Chief of Compliance enters battlefield (1/3).
    COMBAT P1 Magnus the Red hits P0 for 4.
    COMBAT P1 Spawn 3/3 into P2 Token 3/1.
  P0 plays aggro:land:4 (7 lands).
    MANA P0: aggro:land:15 #436 -> (1, 0, 0)
    MANA P0: aggro:land:31 #450 -> (1, 0, 0)
    MANA P0: aggro:land:16 #464 -> (1, 0, 0)
    MANA P0: aggro:land:23 #500 -> (1, 0, 0)
  P0 (aggro) casts aggro:tokens:1 [sorcery] for 4; mana=3.
    COMBAT P0 aggro:medium:1 hits P1 for 5.
    COMBAT P0 Token 2/2 into P3 ramp_stompy:medium:6 4/3.
    MANA P3: ramp_stompy:land:12 #440 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:5 #551 -> (2, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:ramp:7 [artifact] for 3; mana=7.
    MANA P3: ramp_stompy:land:8 #454 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:14 #456 -> (1, 0, 0)
    MANA P3: ramp_stompy:ramp:7 #580 -> (2, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:medium:4 [creature] for 4; mana=5.
    MANA P3: ramp_stompy:land:1 #470 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:36 #489 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:5 #504 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:4 #532 -> (1, 0, 0)
    MANA P3: ramp_stompy:land:35 #549 -> (1, 0, 0)
  P3 (ramp_stompy) casts ramp_stompy:finisher:0 [sorcery] for 5; mana=0.
    COMBAT P3 ramp_stompy:medium:1 hits P0 for 7.
    COMBAT P3 ramp_stompy:large:4 hits P1 for 9.
    COMBAT P3 ramp_stompy:large:2 hits P0 for 10.
    COMBAT P3 Token hits P0 for 5.
    COMBAT P3 Token hits P0 for 5.
    ELIMINATED P0 (aggro): combat.
  P2 plays tokens:land:15 (6 lands).
    MANA P2: tokens:land:27 #442 -> (1, 0, 0)
    MANA P2: tokens:land:31 #458 -> (1, 0, 0)
  P2 (tokens) casts tokens:small:7 [creature] for 2; mana=5.
    COMBAT P2 engine token 1/1 into P3 ramp_stompy:medium:6 7/3.
  End round: P1 magnus life=6 board=11 sources=6, P2 tokens life=23 board=1 sources=7, P3 ramp_stompy life=12 board=51 sources=12

========== ROUND 9 ==========
    COMBAT P1 Magnus the Red 4/5 into P3 ramp_stompy:medium:4 8/5.
  P3 plays ramp_stompy:land:28 (8 lands).
    COMBAT P3 ramp_stompy:medium:6 hits P2 for 7.
    COMBAT P3 ramp_stompy:medium:1 hits P1 for 7.
    ELIMINATED P1 (magnus): combat.
    COMBAT P3 ramp_stompy:large:4 hits P2 for 9.
    COMBAT P3 ramp_stompy:large:2 hits P2 for 10.
    ELIMINATED P2 (tokens): combat.
  End round: P3 ramp_stompy life=12 board=52 sources=13
```

## Boundaries

Mana uses physical source IDs with ordered activations. Priority remains counter-only; selection, land rules and synthetic abilities remain approximate. No deck-power conclusions.
