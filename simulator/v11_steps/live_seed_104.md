# Unforced live game, seed 104

**Unforced seeded live game; synthetic opponents and declared coverage limits apply.**

turn_limit; safety=None; steps=394

## Branch 1

```text

========== ROUND 1 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:15 (1 lands).
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:14 [creature] for 1; mana=0.
    STACK +1 [spell] P1: aggro:small:14.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Island (1 lands).
    MANA P0: Island #431 -> (0, 1, 0)
  P0 (magnus) casts Brainstorm [instant] for 1; mana=0.
    STACK +2 [spell] P0: Brainstorm.
    Brainstorm: partial card selection (3 drawn; exact look/scry/untap not modeled).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:2 (1 lands).
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:3 (1 lands).
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 2 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:31 (2 lands).
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:13 [creature] for 2; mana=0.
    STACK +3 [spell] P1: aggro:small:13.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:14 #429 -> P3.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 1}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Mountain (2 lands).
    MANA P0: Island #431 -> (0, 1, 0)
  P0 (magnus) casts Pongify [instant] for 1; mana=1.
    STACK +4 [spell] P0: Pongify.
    Pongify destroys aggro:small:14; P1 gets a 3/3 Ape.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:8 (2 lands).
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:5 [artifact] for 2; mana=0.
    STACK +5 [spell] P3: combo:ramp:5.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:25 (2 lands).
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 3 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:16 (3 lands).
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:10 [creature] for 1; mana=2.
    STACK +6 [spell] P1: aggro:small:10.
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
    MANA P1: aggro:land:16 #460 -> (1, 0, 0)
  P1 (aggro) casts aggro:buff:0 [sorcery] for 2; mana=0.
    STACK +7 [spell] P1: aggro:buff:0.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 Ape (Pongify) #451 -> P3.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 4}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Stormcarved Coast (3 lands).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:9 [artifact] for 2; mana=1.
    STACK +8 [spell] P3: combo:ramp:9.
    MANA P3: combo:ramp:5 #456 -> (1, 0, 0)
    MANA P3: combo:ramp:9 #469 -> (1, 0, 0)
  P3 (combo) casts combo:engine:7 [enchantment] for 2; mana=0.
    STACK +9 [spell] P3: combo:engine:7.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:27 (3 lands).
    MANA P2: control:land:3 #442 -> (1, 0, 0)
    MANA P2: control:land:25 #458 -> (1, 0, 0)
    MANA P2: control:land:27 #473 -> (1, 0, 0)
  P2 (control) casts control:ramp:4 [artifact] for 3; mana=0.
    STACK +10 [spell] P2: control:ramp:4.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 4 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
    MANA P1: aggro:land:16 #460 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:1 [creature] for 3; mana=0.
    STACK +11 [spell] P1: aggro:medium:1.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:13 #446 -> P0.
    ATTACK: P1 Ape (Pongify) #451 -> P3.
    ATTACK: P1 aggro:small:10 #462 -> P0.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={0: 4, 3: 4}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Command Tower (4 lands).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
    STACK +12 [triggered] P3: combo:engine:7: draw.
    STACK +13 [triggered] P3: combo:engine:7: create_token.
  STEP P3: draw.
  STEP P3: precombat_main.
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
  P3 (combo) casts combo:draw:7 [sorcery] for 2; mana=2.
    STACK +14 [spell] P3: combo:draw:7.
  P3 plays combo:land:4 (3 lands).
    MANA P3: combo:ramp:5 #456 -> (1, 0, 0)
    MANA P3: combo:ramp:9 #469 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:0 [artifact] for 2; mana=1.
    STACK +15 [spell] P3: combo:ramp:0.
    MANA P3: combo:land:4 #489 -> (1, 0, 0)
    MANA P3: combo:ramp:0 #491 -> (1, 0, 0)
  P3 (combo) casts combo:draw:6 [sorcery] for 2; mana=0.
    STACK +16 [spell] P3: combo:draw:6.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:0 (4 lands).
    MANA P2: control:land:3 #442 -> (1, 0, 0)
    MANA P2: control:ramp:4 #475 -> (2, 0, 0)
  P2 (control) casts control:engine:4 [enchantment] for 3; mana=3.
    STACK +17 [spell] P2: control:engine:4.
    MANA P2: control:land:25 #458 -> (1, 0, 0)
    MANA P2: control:land:27 #473 -> (1, 0, 0)
    MANA P2: control:land:0 #498 -> (1, 0, 0)
  P2 (control) casts control:removal:6 [instant] for 3; mana=0.
    STACK +18 [spell] P2: control:removal:6.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 5 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:23 (4 lands).
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
    MANA P1: aggro:land:16 #460 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:5 [creature] for 3; mana=1.
    STACK +19 [spell] P1: aggro:medium:5.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:13 #446 -> P3.
    ATTACK: P1 Ape (Pongify) #451 -> P0.
    ATTACK: P1 aggro:small:10 #462 -> P2.
    ATTACK: P1 aggro:medium:1 #478 -> P2.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 2, 0: 4, 2: 7}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Riptide Laboratory (5 lands).
    MANA P0: Island #431 -> (0, 1, 0)
    MANA P0: Mountain #448 -> (0, 0, 1)
    MANA P0: Stormcarved Coast #466 -> (0, 1, 0)
    MANA P0: Command Tower #480 -> (0, 1, 0)
    MANA P0: Riptide Laboratory #509 -> (1, 0, 0)
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    STACK +20 [spell] P0: Magnus the Red.
    Magnus the Red enters battlefield (4/5).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:22 (4 lands).
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
    MANA P3: combo:ramp:5 #456 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:7 [artifact] for 3; mana=4.
    STACK +21 [spell] P3: combo:ramp:7.
    MANA P3: combo:ramp:9 #469 -> (1, 0, 0)
    MANA P3: combo:land:4 #489 -> (1, 0, 0)
    MANA P3: combo:ramp:0 #491 -> (1, 0, 0)
  P3 (combo) casts combo:draw:10 [sorcery] for 3; mana=2.
    STACK +22 [spell] P3: combo:draw:10.
    MANA P3: combo:land:22 #513 -> (1, 0, 0)
    MANA P3: combo:ramp:7 #515 -> (1, 0, 0)
  P3 (combo) casts combo:small:1 [creature] for 2; mana=0.
    STACK +23 [spell] P3: combo:small:1.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
    ATTACK: P3 Elemental #481 -> P1.
  STEP P3: declare_blockers.
    BLOCK: #507 blocks #481.
  STEP P3: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={507: 1, 481: 5}; players={}.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:22 (5 lands).
    MANA P2: control:land:3 #442 -> (1, 0, 0)
    MANA P2: control:land:25 #458 -> (1, 0, 0)
    MANA P2: control:ramp:4 #475 -> (2, 0, 0)
  P2 (control) casts control:engine:2 [enchantment] for 4; mana=3.
    STACK +24 [spell] P2: control:engine:2.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 6 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:30 (5 lands).
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
    MANA P1: aggro:land:16 #460 -> (1, 0, 0)
    MANA P1: aggro:land:23 #505 -> (1, 0, 0)
  P1 (aggro) casts aggro:tokens:3 [sorcery] for 4; mana=1.
    STACK +25 [spell] P1: aggro:tokens:3.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:13 #446 -> P2.
    ATTACK: P1 Ape (Pongify) #451 -> P3.
    ATTACK: P1 aggro:small:10 #462 -> P2.
    ATTACK: P1 aggro:medium:1 #478 -> P3.
    ATTACK: P1 aggro:medium:5 #507 -> P0.
  STEP P1: declare_blockers.
    BLOCK: #500 blocks #446.
    BLOCK: #521 blocks #451.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={500: 2, 446: 2, 521: 4, 451: 3}; players={2: 2, 3: 5, 0: 5}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Riverglide Pathway [U] (6 lands).
    MANA P0: Island #431 -> (0, 1, 0)
    MANA P0: Mountain #448 -> (0, 0, 1)
  P0 (magnus) casts Abrade [instant] for 2; mana=4.
    STACK +26 [spell] P0: Abrade.
    Abrade artifact mode: combo:ramp:7; destroyed=True.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
    ATTACK: P0 Magnus the Red #511 -> P1.
  STEP P0: declare_blockers.
  STEP P0: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={1: 4}.
    STACK +27 [triggered] P0: Magnus the Red: create_token.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:13 (5 lands).
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
    MANA P3: combo:ramp:5 #456 -> (1, 0, 0)
    MANA P3: combo:ramp:9 #469 -> (1, 0, 0)
  P3 (combo) casts combo:combo_piece:0 [artifact] for 4; mana=4.
    STACK +28 [spell] P3: combo:combo_piece:0.
    MANA P3: combo:land:4 #489 -> (1, 0, 0)
    MANA P3: combo:ramp:0 #491 -> (1, 0, 0)
    MANA P3: combo:land:22 #513 -> (1, 0, 0)
  P3 (combo) casts combo:medium:2 [creature] for 3; mana=1.
    STACK +29 [spell] P3: combo:medium:2.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +30 [triggered] P2: control:engine:2: draw.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:16 (6 lands).
    MANA P2: control:land:3 #442 -> (1, 0, 0)
    MANA P2: control:land:25 #458 -> (1, 0, 0)
    MANA P2: control:ramp:4 #475 -> (2, 0, 0)
  P2 (control) casts control:engine:5 [enchantment] for 4; mana=4.
    STACK +31 [spell] P2: control:engine:5.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 7 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:14 (6 lands).
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
  P1 (aggro) casts aggro:engine:2 [enchantment] for 2; mana=4.
    STACK +32 [spell] P1: aggro:engine:2.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:10 #462 -> P2.
    ATTACK: P1 aggro:medium:1 #478 -> P2.
    ATTACK: P1 aggro:medium:5 #507 -> P2.
    ATTACK: P1 Token #529 -> P0.
    ATTACK: P1 Token #530 -> P2.
    ATTACK: P1 Token #531 -> P2.
    ATTACK: P1 Token #532 -> P2.
  STEP P1: declare_blockers.
    BLOCK: #500 blocks #530.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={500: 2, 530: 2}; players={2: 16, 0: 2}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
    ATTACK: P0 Magnus the Red #511 -> P2.
    ATTACK: P0 Spawn #541 -> P2.
  STEP P0: declare_blockers.
  STEP P0: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={2: 7}.
    STACK +33 [triggered] P0: Magnus the Red: create_token.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:25 (6 lands).
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
    MANA P3: combo:ramp:5 #456 -> (1, 0, 0)
  P3 (combo) casts combo:engine:6 [enchantment] for 3; mana=6.
    STACK +34 [spell] P3: combo:engine:6.
    MANA P3: combo:ramp:9 #469 -> (1, 0, 0)
    MANA P3: combo:land:4 #489 -> (1, 0, 0)
    MANA P3: combo:ramp:0 #491 -> (1, 0, 0)
    MANA P3: combo:land:22 #513 -> (1, 0, 0)
    MANA P3: combo:land:13 #543 -> (1, 0, 0)
    MANA P3: combo:land:25 #560 -> (1, 0, 0)
  P3 (combo) casts combo:large:0 [creature] for 6; mana=0.
    STACK +35 [spell] P3: combo:large:0.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +36 [triggered] P2: control:engine:4: draw.
    STACK +37 [triggered] P2: control:engine:2: draw.
    STACK +38 [triggered] P2: control:engine:5: create_token.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:9 (7 lands).
    MANA P2: control:ramp:4 #475 -> (2, 0, 0)
  P2 (control) casts control:draw:1 [sorcery] for 2; mana=7.
    STACK +39 [spell] P2: control:draw:1.
    MANA P2: control:land:3 #442 -> (1, 0, 0)
    MANA P2: control:land:25 #458 -> (1, 0, 0)
    MANA P2: control:land:27 #473 -> (1, 0, 0)
    MANA P2: control:land:0 #498 -> (1, 0, 0)
  P2 (control) casts control:medium:4 [creature] for 4; mana=3.
    STACK +40 [spell] P2: control:medium:4.
    MANA P2: control:land:22 #523 -> (1, 0, 0)
    MANA P2: control:land:16 #550 -> (1, 0, 0)
    MANA P2: control:land:9 #569 -> (1, 0, 0)
  P2 (control) casts control:removal:3 [instant] for 3; mana=0.
    STACK +41 [spell] P2: control:removal:3.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
    ATTACK: P2 control:engine:4 #500 -> P0.
  STEP P2: declare_blockers.
  STEP P2: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={0: 2}.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 8 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:4 (7 lands).
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:10 #462 -> P2.
    ATTACK: P1 aggro:medium:1 #478 -> P3.
    ATTACK: P1 aggro:medium:5 #507 -> P3.
    ATTACK: P1 Token #529 -> P2.
    ATTACK: P1 Token #531 -> P3.
    ATTACK: P1 Token #532 -> P3.
  STEP P1: declare_blockers.
    BLOCK: #575 blocks #462.
    BLOCK: #562 blocks #531.
    BLOCK: #547 blocks #532.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={575: 2, 462: 5, 562: 2, 531: 2, 547: 2, 532: 4}; players={3: 10, 2: 2}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
    MANA P0: Island #431 -> (0, 1, 0)
    MANA P0: Riverglide Pathway #537 -> (0, 1, 0)
  P0 (magnus) casts Baral, Chief of Compliance [creature] for 2; mana=4.
    STACK +42 [spell] P0: Baral, Chief of Compliance.
    Baral, Chief of Compliance enters battlefield (1/3).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
    ATTACK: P0 Magnus the Red #511 -> P3.
    ATTACK: P0 Spawn #558 -> P1.
  STEP P0: declare_blockers.
  STEP P0: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 4, 1: 3}.
    STACK +43 [triggered] P0: Magnus the Red: create_token.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
    STACK +44 [triggered] P3: combo:engine:6: draw.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:15 (7 lands).
    MANA P3: combo:land:2 #440 -> (1, 0, 0)
    MANA P3: combo:land:8 #454 -> (1, 0, 0)
    MANA P3: combo:ramp:5 #456 -> (1, 0, 0)
    MANA P3: combo:ramp:9 #469 -> (1, 0, 0)
    MANA P3: combo:land:4 #489 -> (1, 0, 0)
    MANA P3: combo:ramp:0 #491 -> (1, 0, 0)
    MANA P3: combo:land:22 #513 -> (1, 0, 0)
  P3 (combo) casts combo:large:1 [creature] for 7; mana=3.
    STACK +45 [spell] P3: combo:large:1.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +46 [triggered] P2: control:engine:4: create_token.
    STACK +47 [triggered] P2: control:engine:2: create_token.
    STACK +48 [triggered] P2: control:engine:5: draw.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:7 (8 lands).
    MANA P2: control:land:3 #442 -> (1, 0, 0)
    MANA P2: control:ramp:4 #475 -> (2, 0, 0)
  P2 (control) casts control:ramp:0 [artifact] for 3; mana=7.
    STACK +49 [spell] P2: control:ramp:0.
    MANA P2: control:land:25 #458 -> (1, 0, 0)
    MANA P2: control:land:27 #473 -> (1, 0, 0)
  P2 (control) casts control:draw:6 [sorcery] for 2; mana=6.
    STACK +50 [spell] P2: control:draw:6.
    MANA P2: control:land:0 #498 -> (1, 0, 0)
    MANA P2: control:land:22 #523 -> (1, 0, 0)
    MANA P2: control:land:16 #550 -> (1, 0, 0)
  P2 (control) casts control:ramp:7 [artifact] for 3; mana=3.
    STACK +51 [spell] P2: control:ramp:7.
    MANA P2: control:land:9 #569 -> (1, 0, 0)
    MANA P2: control:land:7 #595 -> (1, 0, 0)
    MANA P2: control:ramp:0 #597 -> (1, 0, 0)
  P2 (control) casts control:engine:6 [enchantment] for 3; mana=1.
    STACK +52 [spell] P2: control:engine:6.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
    ATTACK: P2 control:engine:4 #500 -> P3.
    ATTACK: P2 control:medium:4 #575 -> P3.
  STEP P2: declare_blockers.
    BLOCK: #547 blocks #500.
  STEP P2: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={547: 2, 500: 4}; players={3: 5}.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.

========== ROUND 9 ==========
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
    MANA P1: aggro:land:16 #460 -> (1, 0, 0)
    MANA P1: aggro:land:23 #505 -> (1, 0, 0)
  P1 (aggro) casts aggro:tokens:1 [sorcery] for 4; mana=3.
    STACK +53 [spell] P1: aggro:tokens:1.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:medium:1 #478 -> P3.
    ATTACK: P1 aggro:medium:5 #507 -> P2.
    ATTACK: P1 Token #529 -> P0.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 5, 2: 5, 0: 2}.
    ELIMINATED P3 (combo): state_based.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
    ATTACK: P0 Magnus the Red #511 -> P2.
  STEP P0: declare_blockers.
  STEP P0: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={2: 4}.
    ELIMINATED P2 (control): state_based.
    STACK +54 [triggered] P0: Magnus the Red: create_token.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 10 ==========
  STEP P1: untap.
  STEP P1: upkeep.
    STACK +55 [triggered] P1: aggro:engine:2: draw.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:15 #427 -> (1, 0, 0)
    MANA P1: aggro:land:31 #444 -> (1, 0, 0)
    MANA P1: aggro:land:16 #460 -> (1, 0, 0)
    MANA P1: aggro:land:23 #505 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:4 [creature] for 4; mana=3.
    STACK +56 [spell] P1: aggro:medium:4.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:medium:1 #478 -> P0.
    ATTACK: P1 aggro:medium:5 #507 -> P0.
    ATTACK: P1 Token #529 -> P0.
    ATTACK: P1 Token #609 -> P0.
    ATTACK: P1 Token #610 -> P0.
    ATTACK: P1 Token #611 -> P0.
    ATTACK: P1 Token #612 -> P0.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={0: 16}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
    ATTACK: P0 Spawn #585 -> P1.
    ATTACK: P0 Spawn #615 -> P1.
  STEP P0: declare_blockers.
    BLOCK: #619 blocks #585.
  STEP P0: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={619: 3, 585: 3}; players={1: 3}.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
```
