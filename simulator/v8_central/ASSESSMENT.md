# v8 integration assessment — October 28, 2026

## Summary

**Objective:** eliminate redundant shared board and spell transitions across v5, v6, and v7 while preserving working four-player play. Current v8 implementation is a deliberately limited but functioning **central battlefield + common cast/response/turn engine**. Previous engines are *not* modified and remain standalone reference baselines.

**Validation:** 32 new v8 tests + 127 prior versioned tests, **159 total passing**. One 100-seed 12-round smoke sweep (not Monte Carlo deck evaluation) completed with `world.consistent()` true at the end of every game. Four narrated games: no safety stop and no mismatch.

## Key architectural changes

1. **Persistent GameKernel**, no repeated `_view()` rematerialization. A projection `Creature`/`Permanent` has exactly the same object ID as its central game object, and each successful zone move discards the old ID. Synthetic and named creatures use the same implementation.
2. **All four player seats share the same combat, destruction, targeted-spell legality, and damage pipeline.** Indestructible blocks destroy/lethal marked damage but not sacrifice/exile; hexproof stops opponent targeted removal but not untargeted wipes. Damage is marked simultaneously on both combatants before state-based actions. Both players can be eliminated by one simultaneous damaging effect.
3. **Counterspells are actual nested stack frames.** A counterspell can target a counterspell, resolving LIFO; the cards/mana are consumed. Both synthetic and named spells use `SharedStack`. Printed counter restrictions and special riders are declarative in `responses.py`, not branches in the stack.
4. **Shared-trigger effect bridge** uses the persistent registry for Magnus, Young Pyromancer, Harmonic Prodigy, Storm-Kiln, etc.; Treasurer token identity is now kernel-backed and spending consumes the game object. No duplicate name-check trigger implementation in the active v8 code.
5. **One four-seat `TurnDriver`.** No seat-specific reimplementation of round order. Deck-specific mana/land/hand/mulligan are still adapters.
6. **Safety and observability:** Stack depth, repeated-action guard, operation counts, zone transitions, consistency assertions, and narrative replay metadata.

## Critical bug detected and resolved during migration

An early seed sweep revealed that a player eliminated by the v5 table was removed from the *pilot's* battlefield lists but not the kernel. Added `Battlefield.leave_game()`, which removes that player's objects without generating false death triggers, and a regression test. A subsequent 100-seed 12-round sweep passed.

## Short narrated games (10 rounds)

| Case | Lineup against real Magnus | Magnus life | Magnus spells | Shared-stack peak | Outcome |
|---|---|---:|---:|---:|---|
| `01_mixed` | Aggro / Control / Combo | 9 | 9 | 3 | Unresolved at turn limit |
| `02_pressure` | Aggro / Tokens / Ramp | 0 | 4 | 1 | Combat elimination |
| `03_control_heavy` | Control / Spellslinger / Midrange | 20 | 7 | 3 | Unresolved at turn limit |
| `04_forced_triggers` | Control / Combo / Tokens | 28 | 8 | 1 | Unresolved at turn limit |

The fourth case deliberately alters the opening hand to expose interactions. These matches are diagnostic only. Changes in outcomes versus v7 are expected because the shared response order, targeting choices, and combat rules alter stochastic histories. They are **not** a relative deck power comparison.

## Computational cost

Small local diagnostic, 40 distinct seeds each, 10 rounds, single-process standard-library Python:

| Engine | Median milliseconds | Mean milliseconds | Maximum milliseconds |
|---|---:|---:|---:|
| V7 `ModularTable` | 9.119 | 11.867 | 86.198 |
| V8 `CentralTable` | 9.435 | 9.763 | 16.868 |

This is not a fair deterministic paired timing benchmark across identical game trajectories (the models diverge). It indicates no immediate pathological slowdown in sampled positions; do not extrapolate to 100-card fully modeled games or dense combo turns.

## Remaining modeling and correctness risks

- **Zones incomplete:** persistent kernel currently authoritative for battlefield creatures, permanents and some tokens, not physical land objects, complete hands, graveyards, exile, command-zone objects or spell cards. The v6 real-deck adapter still owns opening hands and graveyard strings; command-zone recast is recorded at pilot level.
- **Priority incomplete:** counter-only response windows support nested counters, but triggered abilities currently settle before those windows, and players cannot respond with arbitrary instants or activated abilities. This is not complete Magic stack priority. A safety stop for overly deep counters remains a guard, not a substitute for full legal priority.
- **Mana incomplete:** Magnus colored sources reuse v6's payment search; synthetic opponents use abstract fungible mana. Izzet Signet activation, life-paying lands and utility-lands remain simplified. Continued resource tracking should move to resource objects and explicit taps.
- **Target selection:** the engine validates a target at resolution. Legacy abstract pilot target-choice heuristics may still select protected objects, wasting spells. The pilot should use legality API before casting.
- **Card coverage:** many named Magnus cards remain unimplemented, including special tutors, copy, buyback, Class, and combo pieces. Unsupported cards still cannot be cast; partial selection cards may use inaccurate decision logic.
- **Synthetic finishers:** abstract combo kills are symbolic non-damage eliminations, not actual printed card text.
- **Triggered ability event structure:** spell-cast triggers currently resolve immediately; replacement effects, APNAP ordering, and responding to each stack trigger need the next iteration.
- **Elimination cleanup:** leaving player objects are removed centrally without dying events, but comprehensive multiplayer state-based actions and triggers for control change still need support.
- **Performance:** avoid simulating astronomical loops; use `LoopResolver` only with proven repeatable state transitions and available opponent responses, and always preserve draw-to-deck checks.

## Recommended v9 priorities

1. A generic `DeckProvider` + `ResourcePolicy` adapter so Magnus is not intrinsically seat 0.
2. Kernel-owned card zone objects (library/hand/graveyard/command); remove legacy hand/graveyard string lists.
3. Typed mana sources, tapping and alternative/cost-additional payment with bounded plan selection.
4. Genuine stack priority for spell and trigger frames and general instant/activated responses.
5. Then complete named-card handler inventory and verify realistic combo certificates.
