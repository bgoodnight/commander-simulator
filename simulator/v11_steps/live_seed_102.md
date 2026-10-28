# Unforced live game, seed 102

**Unforced seeded live game; synthetic opponents and declared coverage limits apply.**

turn_limit; safety=None; steps=428

## Branch 1

```text

========== ROUND 1 ==========
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:31 (1 lands).
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:16 (1 lands).
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:8 [creature] for 1; mana=0.
    STACK +1 [spell] P1: aggro:small:8.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:26 (1 lands).
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Sulfur Falls (1 lands) tapped.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 2 ==========
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:7 (2 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
  P2 (control) casts control:engine:1 [enchantment] for 2; mana=0.
    STACK +2 [spell] P2: control:engine:1.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:9 (2 lands).
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:4 [creature] for 2; mana=0.
    STACK +3 [spell] P1: aggro:small:4.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:8 #445 -> P0.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={0: 1}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:22 (2 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:4 [artifact] for 2; mana=0.
    STACK +4 [spell] P3: combo:ramp:4.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 3 ==========
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +5 [triggered] P2: control:engine:1: draw.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:10 (3 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
    MANA P2: control:land:10 #466 -> (1, 0, 0)
  P2 (control) casts control:engine:3 [enchantment] for 3; mana=0.
    STACK +6 [spell] P2: control:engine:3.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:4 (3 lands).
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
  P1 (aggro) casts aggro:buff:1 [sorcery] for 2; mana=1.
    STACK +7 [spell] P1: aggro:buff:1.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:8 #445 -> P2.
    ATTACK: P1 aggro:small:4 #457 -> P3.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={2: 3, 3: 4}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:5 (3 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:engine:3 [enchantment] for 2; mana=2.
    STACK +8 [spell] P3: combo:engine:3.
    MANA P3: combo:ramp:4 #461 -> (1, 0, 0)
    MANA P3: combo:land:5 #474 -> (1, 0, 0)
  P3 (combo) casts combo:draw:2 [sorcery] for 2; mana=0.
    STACK +9 [spell] P3: combo:draw:2.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 4 ==========
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +10 [triggered] P2: control:engine:1: draw.
    STACK +11 [triggered] P2: control:engine:3: draw.
    STACK +12 [triggered] P2: control:engine:3: create_token.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:8 (4 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
  P2 (control) casts control:draw:2 [sorcery] for 2; mana=2.
    STACK +13 [spell] P2: control:draw:2.
    MANA P2: control:land:10 #466 -> (1, 0, 0)
    MANA P2: control:land:8 #487 -> (1, 0, 0)
  P2 (control) casts control:draw:6 [sorcery] for 2; mana=0.
    STACK +14 [spell] P2: control:draw:6.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:14 (4 lands).
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:1 [creature] for 4; mana=0.
    STACK +15 [spell] P1: aggro:medium:1.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:8 #445 -> P3.
    ATTACK: P1 aggro:small:4 #457 -> P0.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 3, 0: 4}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:27 (4 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:5 [artifact] for 2; mana=3.
    STACK +16 [spell] P3: combo:ramp:5.
    MANA P3: combo:ramp:4 #461 -> (1, 0, 0)
    MANA P3: combo:land:5 #474 -> (1, 0, 0)
    MANA P3: combo:land:27 #504 -> (1, 0, 0)
    MANA P3: combo:ramp:5 #506 -> (1, 0, 0)
  P3 (combo) casts combo:engine:2 [enchantment] for 4; mana=0.
    STACK +17 [spell] P3: combo:engine:2.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Shivan Reef (2 lands).
    MANA P0: Sulfur Falls #449 -> (0, 1, 0)
    MANA P0: Shivan Reef #510 -> (1, 0, 0)
  P0 (magnus) casts Arcane Signet [artifact] for 2; mana=0.
    STACK +18 [spell] P0: Arcane Signet.
    Arcane Signet enters untapped; its mana ability is immediately available.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 5 ==========
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +19 [triggered] P2: control:engine:1: draw.
    STACK +20 [triggered] P2: control:engine:1: create_token.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:33 (5 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
  P2 (control) casts control:draw:0 [sorcery] for 2; mana=3.
    STACK +21 [spell] P2: control:draw:0.
    MANA P2: control:land:10 #466 -> (1, 0, 0)
    MANA P2: control:land:8 #487 -> (1, 0, 0)
    MANA P2: control:land:33 #516 -> (1, 0, 0)
  P2 (control) casts control:draw:4 [sorcery] for 3; mana=0.
    STACK +22 [spell] P2: control:draw:4.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:0 [creature] for 4; mana=0.
    STACK +23 [spell] P1: aggro:medium:0.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:8 #445 -> P0.
    ATTACK: P1 aggro:small:4 #457 -> P2.
    ATTACK: P1 aggro:medium:1 #502 -> P0.
  STEP P1: declare_blockers.
    BLOCK: #483 blocks #457.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={483: 4, 457: 1}; players={0: 6}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
    STACK +24 [triggered] P3: combo:engine:3: draw.
    STACK +25 [triggered] P3: combo:engine:2: draw.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:18 (5 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
    MANA P3: combo:ramp:4 #461 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:0 [artifact] for 3; mana=4.
    STACK +26 [spell] P3: combo:ramp:0.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
    ATTACK: P3 combo:engine:3 #476 -> P2.
  STEP P3: declare_blockers.
  STEP P3: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={2: 2}.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
    MANA P0: Sulfur Falls #449 -> (0, 1, 0)
    MANA P0: Arcane Signet #512 -> (0, 0, 1)
  P0 (magnus) casts Harmonic Prodigy [creature] for 2; mana=1.
    STACK +27 [spell] P0: Harmonic Prodigy.
    MANA P3: combo:land:5 #474 -> (1, 0, 0)
    MANA P3: combo:land:27 #504 -> (1, 0, 0)
  P3 (combo) casts combo:counter:4 [instant] for 2; mana=3.
    STACK +28 [spell] P3: combo:counter:4.
    STACK -27: Harmonic Prodigy countered.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 6 ==========
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +29 [triggered] P2: control:engine:1: draw.
    STACK +30 [triggered] P2: control:engine:1: create_token.
    STACK +31 [triggered] P2: control:engine:3: create_token.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:18 (6 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
  P2 (control) casts control:engine:9 [enchantment] for 2; mana=4.
    STACK +32 [spell] P2: control:engine:9.
    MANA P2: control:land:10 #466 -> (1, 0, 0)
    MANA P2: control:land:8 #487 -> (1, 0, 0)
    MANA P2: control:land:33 #516 -> (1, 0, 0)
    MANA P2: control:land:18 #547 -> (1, 0, 0)
  P2 (control) casts control:engine:7 [enchantment] for 4; mana=0.
    STACK +33 [spell] P2: control:engine:7.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:3 [creature] for 4; mana=0.
    STACK +34 [spell] P1: aggro:medium:3.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:medium:1 #502 -> P2.
    ATTACK: P1 aggro:medium:0 #530 -> P3.
  STEP P1: declare_blockers.
    BLOCK: #549 blocks #502.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={549: 3, 502: 2}; players={3: 3}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
    STACK +35 [triggered] P3: combo:engine:2: draw.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:21 (6 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
    MANA P3: combo:ramp:4 #461 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:9 [artifact] for 3; mana=6.
    STACK +36 [spell] P3: combo:ramp:9.
    MANA P3: combo:land:5 #474 -> (1, 0, 0)
    MANA P3: combo:land:27 #504 -> (1, 0, 0)
    MANA P3: combo:ramp:5 #506 -> (1, 0, 0)
    MANA P3: combo:land:18 #535 -> (1, 0, 0)
    MANA P3: combo:ramp:0 #537 -> (1, 0, 0)
    MANA P3: combo:land:21 #559 -> (1, 0, 0)
  P3 (combo) casts combo:large:1 [creature] for 6; mana=1.
    STACK +37 [spell] P3: combo:large:1.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
    ATTACK: P3 combo:engine:3 #476 -> P2.
  STEP P3: declare_blockers.
  STEP P3: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={2: 2}.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 7 ==========
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:26 (7 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
    MANA P2: control:land:10 #466 -> (1, 0, 0)
    MANA P2: control:land:8 #487 -> (1, 0, 0)
  P2 (control) casts control:medium:4 [creature] for 4; mana=3.
    STACK +38 [spell] P2: control:medium:4.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
  P1 (aggro) casts aggro:tokens:0 [sorcery] for 4; mana=0.
    STACK +39 [spell] P1: aggro:tokens:0.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:medium:0 #530 -> P0.
    ATTACK: P1 aggro:medium:3 #554 -> P0.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={0: 8}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
    STACK +40 [triggered] P3: combo:engine:3: create_token.
    STACK +41 [triggered] P3: combo:engine:2: draw.
    STACK +42 [triggered] P3: combo:engine:2: create_token.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:2 (7 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:engine:10 [enchantment] for 2; mana=9.
    STACK +43 [spell] P3: combo:engine:10.
    MANA P3: combo:ramp:4 #461 -> (1, 0, 0)
    MANA P3: combo:land:5 #474 -> (1, 0, 0)
    MANA P3: combo:land:27 #504 -> (1, 0, 0)
  P3 (combo) casts combo:engine:4 [enchantment] for 3; mana=6.
    STACK +44 [spell] P3: combo:engine:4.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Mountain (3 lands).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 8 ==========
  STEP P2: untap.
  STEP P2: upkeep.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:36 (8 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
    MANA P2: control:land:10 #466 -> (1, 0, 0)
    MANA P2: control:land:8 #487 -> (1, 0, 0)
    MANA P2: control:land:33 #516 -> (1, 0, 0)
  P2 (control) casts control:large:0 [creature] for 5; mana=3.
    STACK +45 [spell] P2: control:large:0.
    MANA P0: Sulfur Falls #449 -> (0, 1, 0)
    MANA P0: Arcane Signet #512 -> (0, 1, 0)
  P0 (magnus) casts Counterspell [instant] for 2; mana=2.
    STACK +46 [spell] P0: Counterspell.
    MANA P2: control:land:18 #547 -> (1, 0, 0)
    MANA P2: control:land:26 #566 -> (1, 0, 0)
  P2 (control) casts control:counter:6 [instant] for 2; mana=1.
    STACK +47 [spell] P2: control:counter:6.
    STACK -46: Counterspell countered.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
    ATTACK: P2 Elemental #543 -> P3.
  STEP P2: declare_blockers.
    BLOCK: #476 blocks #543.
  STEP P2: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={476: 1, 543: 2}; players={}.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:11 (5 lands).
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
  P1 (aggro) casts aggro:draw:2 [sorcery] for 2; mana=3.
    STACK +48 [spell] P1: aggro:draw:2.
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:9 [creature] for 2; mana=1.
    STACK +49 [spell] P1: aggro:small:9.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:small:8 #445 -> P3.
    ATTACK: P1 aggro:medium:0 #530 -> P2.
    ATTACK: P1 aggro:medium:3 #554 -> P2.
    ATTACK: P1 Token #571 -> P2.
    ATTACK: P1 Token #572 -> P0.
  STEP P1: declare_blockers.
    BLOCK: #563 blocks #445.
    BLOCK: #592 blocks #554.
    BLOCK: #568 blocks #571.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={563: 3, 445: 6, 592: 5, 554: 6, 568: 1, 571: 3}; players={2: 3, 0: 1}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
    STACK +50 [triggered] P3: combo:engine:3: draw.
    STACK +51 [triggered] P3: combo:engine:10: create_token.
    STACK +52 [triggered] P3: combo:engine:4: draw.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:3 (8 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:1 [artifact] for 2; mana=10.
    STACK +53 [spell] P3: combo:ramp:1.
    MANA P3: combo:ramp:4 #461 -> (1, 0, 0)
    MANA P3: combo:land:5 #474 -> (1, 0, 0)
    MANA P3: combo:land:27 #504 -> (1, 0, 0)
  P3 (combo) casts combo:tokens:0 [sorcery] for 3; mana=8.
    STACK +54 [spell] P3: combo:tokens:0.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
    ATTACK: P3 combo:engine:3 #476 -> P0.
    ATTACK: P3 Elemental #576 -> P2.
  STEP P3: declare_blockers.
    BLOCK: #568 blocks #576.
  STEP P3: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={568: 1, 576: 3}; players={0: 2}.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Island (4 lands).
    MANA P0: Sulfur Falls #449 -> (0, 1, 0)
    MANA P0: Arcane Signet #512 -> (0, 1, 0)
    MANA P0: Shivan Reef #510 -> (1, 0, 0)
    MANA P0: Mountain #584 -> (0, 0, 1)
    MANA P0: Island #615 -> (0, 1, 0)
  P0 (magnus) casts Magnus the Red [creature] for 5; mana=0.
    STACK +55 [spell] P0: Magnus the Red.
    Magnus the Red enters battlefield (4/5).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 9 ==========
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +56 [triggered] P2: control:engine:1: draw.
    STACK +57 [triggered] P2: control:engine:1: create_token.
    STACK +58 [triggered] P2: control:engine:7: draw.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:17 (9 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
  P2 (control) casts control:small:2 [creature] for 1; mana=8.
    STACK +59 [spell] P2: control:small:2.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
    ATTACK: P2 Elemental #513 -> P3.
    ATTACK: P2 control:medium:4 #568 -> P1.
  STEP P2: declare_blockers.
    BLOCK: #563 blocks #513.
    BLOCK: #600 blocks #568.
  STEP P2: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={563: 1, 513: 6, 600: 3, 568: 3}; players={}.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
  P1 (aggro) casts aggro:medium:5 [creature] for 4; mana=1.
    STACK +60 [spell] P1: aggro:medium:5.
    MANA P1: aggro:land:11 #594 -> (1, 0, 0)
  P1 (aggro) casts aggro:small:3 [creature] for 1; mana=0.
    STACK +61 [spell] P1: aggro:small:3.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
    ATTACK: P1 aggro:medium:0 #530 -> P3.
  STEP P1: declare_blockers.
  STEP P1: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={}; players={3: 3}.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:0 (9 lands).
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
    ATTACK: P3 Elemental #574 -> P2.
    ATTACK: P3 Token #611 -> P2.
  STEP P3: declare_blockers.
    BLOCK: #624 blocks #574.
    BLOCK: #592 blocks #611.
  STEP P3: combat_damage.
    COMBAT DAMAGE simultaneous: creatures={624: 1, 574: 2, 592: 1, 611: 6}; players={}.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  P0 plays Island (5 lands).
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.

========== ROUND 10 ==========
  STEP P2: untap.
  STEP P2: upkeep.
    STACK +62 [triggered] P2: control:engine:3: draw.
  STEP P2: draw.
  STEP P2: precombat_main.
  P2 plays control:land:13 (10 lands).
    MANA P2: control:land:31 #441 -> (1, 0, 0)
    MANA P2: control:land:7 #451 -> (1, 0, 0)
  P2 (control) casts control:draw:5 [sorcery] for 2; mana=8.
    STACK +63 [spell] P2: control:draw:5.
    MANA P2: control:land:10 #466 -> (1, 0, 0)
    MANA P2: control:land:8 #487 -> (1, 0, 0)
    MANA P2: control:land:33 #516 -> (1, 0, 0)
    MANA P2: control:land:18 #547 -> (1, 0, 0)
    MANA P2: control:land:26 #566 -> (1, 0, 0)
  P2 (control) casts control:wipe:1 [sorcery] for 5; mana=3.
    STACK +64 [spell] P2: control:wipe:1.
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:counter:5 [instant] for 2; mana=12.
    STACK +65 [spell] P3: combo:counter:5.
    MANA P2: control:land:36 #586 -> (1, 0, 0)
    MANA P2: control:land:17 #622 -> (1, 0, 0)
  P2 (control) casts control:counter:4 [instant] for 2; mana=1.
    STACK +66 [spell] P2: control:counter:4.
    STACK -65: combo:counter:5 countered.
    Board wipe removes 13 creatures.
  STEP P2: begin_combat.
  STEP P2: declare_attackers.
  STEP P2: end_combat.
  STEP P2: postcombat_main.
  STEP P2: end.
  STEP P2: cleanup.
  STEP P1: untap.
  STEP P1: upkeep.
  STEP P1: draw.
  STEP P1: precombat_main.
  P1 plays aggro:land:7 (6 lands).
    MANA P1: aggro:land:16 #443 -> (1, 0, 0)
    MANA P1: aggro:land:9 #455 -> (1, 0, 0)
    MANA P1: aggro:land:4 #470 -> (1, 0, 0)
  P1 (aggro) casts aggro:engine:1 [enchantment] for 3; mana=3.
    STACK +67 [spell] P1: aggro:engine:1.
    MANA P1: aggro:land:14 #500 -> (1, 0, 0)
    MANA P1: aggro:land:11 #594 -> (1, 0, 0)
    MANA P1: aggro:land:7 #660 -> (1, 0, 0)
  P1 (aggro) casts aggro:burn:0 [instant] for 3; mana=0.
    STACK +68 [spell] P1: aggro:burn:0.
  STEP P1: begin_combat.
  STEP P1: declare_attackers.
  STEP P1: end_combat.
  STEP P1: postcombat_main.
  STEP P1: end.
  STEP P1: cleanup.
  STEP P3: untap.
  STEP P3: upkeep.
  STEP P3: draw.
  STEP P3: precombat_main.
  P3 plays combo:land:28 (10 lands).
    MANA P3: combo:land:26 #447 -> (1, 0, 0)
    MANA P3: combo:land:22 #459 -> (1, 0, 0)
  P3 (combo) casts combo:ramp:3 [artifact] for 2; mana=13.
    STACK +69 [spell] P3: combo:ramp:3.
  STEP P3: begin_combat.
  STEP P3: declare_attackers.
  STEP P3: end_combat.
  STEP P3: postcombat_main.
  STEP P3: end.
  STEP P3: cleanup.
  STEP P0: untap.
  STEP P0: upkeep.
  STEP P0: draw.
  STEP P0: precombat_main.
  STEP P0: begin_combat.
  STEP P0: declare_attackers.
  STEP P0: end_combat.
  STEP P0: postcombat_main.
  STEP P0: end.
  STEP P0: cleanup.
```
