# Architecture audit — October 31, 2026

Audited implementation: `789281e5e876b22aa8adf83cd7b74bacc10984ee` (v35). This is a code/design review with read-only diagnostic probes, not a complete rules certification. No implementation was changed during this audit.

## Assessment

The project has useful foundations worth retaining: one authoritative object registry, new identities on zone changes, source-backed payments, a shared priority stack, explicit safety stops, descriptor-based abilities, and seeded scenarios. It needs architectural consolidation before another large card batch. It is not yet a reusable arbitrary-deck engine.

The current engine is `CopyTable`, not the historical `PremiumTable` named in the old roadmap. Its inheritance chain contains **32 project classes** before Python's `object`, including **10 implementations of `priority_choices`**, 14 of `action_for`, and 9 of `emit`. Composition order already changes which card abilities exist.

The current premium audit reports 41 distinct supported subsets, 6 partial and 35 unsupported names; physical counts are 59/6/35. These labels cover documented behaviors only. More card coverage alone will not establish accurate decisions or realistic multiplayer outcomes.

## Findings, ordered by risk and implementation dependency

| ID | Priority | Evidence | Consequence and required direction |
|---|---|---|---|
| A1 | High: confirmed regression | `v21_early_mana/mana_table.py:38` wraps one resource instance; `v30_phyrexian_altar/altar_table.py:54` replaces it. | An explicitly untapped Frostboil Snarl pays U/R in `EarlyManaTable` but has no mana abilities in `AltarTable`, the current budget option. Add a current-engine regression and use composable providers. The current premium list removed Frostboil and is unaffected. |
| A2 | High: cross-deck blocker | `v7_rules/rules.py:18`, `v9c_mana/resources.py:18`, `v9_kernel/adapter.py:16`, `v9b_live/live.py:28`, premium/budget loaders. | Costs/pools represent U/R/C only; construction requires exactly one Magnus; singleton exceptions recognize Island/Mountain only. Mono-black cannot be configured normally. Generalize configuration and mana instead of creating a black table branch. |
| A3 | High: active dependencies | `run_simulation.py`, v35-to-v5 inheritance, repeated `sys.path.insert` and unqualified module names. | New cards extend historical tables and tests need separate interpreters to avoid collisions. Extract a normal package and compose services; retain historical versions as references, not active extension layers. |
| A4 | High: characteristic disagreement | `v9b_live/state.py:69`, v20 type corrections, v23 color map, v28 mana-value map, v31 supplements, v34 Adventure casting. | During Mage Siege casting the kernel reports `Mage Siege`/instant while `CardView` reports `Lindblum, Industrial Regency`/land. Current action-based handlers often compensate; generic queries could use the wrong face. Centralize definitions and zone/face-sensitive characteristics. |
| A5 | High before more keywords | `v9b_live/live.py:117`, `v11_steps/stepped.py:91`, `v33_reiterate/reiterate_table.py:96`, `v34_mage_siege/adventure_table.py:61`, `v35_copy_targets/copy_table.py:24`. | Normal/Adventure casting, buyback destinations and copies separately manage the same lifecycle. Mutable actions, name-based source selection, dynamic `step_targets`, and `id(action)` bookkeeping impede generic copying/replay. Use explicit IDs, typed targets and a common pipeline. |
| A6 | High before black/graveyard engines | `v7_rules/rules.py:233`, `v8_central/kernel.py:117`, `v8_central/table.py:110`, `v13_engines/engine_table.py:51`. | Kernel history and table listener events are separate paths: recording `dies` does not automatically dispatch triggers; the old object is gone and the event lacks full last-known data. Simultaneous moves are often sequential. Add event batches, snapshots and consistent trigger collection. |
| A7 | Medium-high: duplicated development | v17/v25/v26/v27/v28/v31 tutors; v11/v33 buyback; v33/v35 copies. | Predicates, choices, destinations and effects are embedded in named handlers. Extract typed primitives and compositions; keywords should expand into costs, permissions, restrictions, effects and replacements as needed. Not every keyword is a resolution effect. |
| A8 | Medium-high: measured runtime | `v10_priority/gameplay.py:155`, `v29_step_cycling/step_cycling.py:52`, `v7_rules/rules.py:183`, `v30_phyrexian_altar/altar_table.py:20`. | Each priority pass repeats scans and builds choices later layers discard. Target combinations grow quadratically. Use one action generator, shared query contexts and lazy enumeration; preserve complete legality and deterministic ordering. |
| A9 | Medium: invalidation design | `v7_rules/rules.py:174`, `v9c_mana/resources.py:103`, `v13_engines/engine_table.py:17`. | Global dirtying clears all kernel caches; mana signatures recompute sources even on cache hits; checkpoints rescan views. Profile-guided indexes and explicit mutation boundaries should precede more memoization. Never remove required priority/SBA checks for speed. |
| A10 | Medium: evidence/maintenance | `run_all_tests.py`, copied coverage reports, compressed card modules. | The runner prints an expected test count without verifying it. Passing old suites missed A1 in the assembled engine. Add current-engine contracts, generated capability coverage and clearer typed modules; historical test counts do not prove deck support. |

Paths above are relative to `simulator/` unless rooted at the repository.

## Runtime evidence

Read-only `cProfile` sample, Python 3.12.14: `CopyTable(seed=s, trace=False).run(8)` for seeds 0, 1, 2. All completed without safety stops. Instrumented CPU time totaled about 6.073 seconds; **this includes profiler overhead and is not a throughput benchmark**. Cumulative times overlap and must not be added.

| Path | Calls/observations | Profile evidence |
|---|---:|---:|
| Outer `priority_choices` chain | 4,046 calls | 3.487 s cumulative, about 57% of profile |
| `EngineStack.checkpoint` | 5,323 calls | 1.495 s cumulative |
| `AltarResources.sources` | 13,226 calls | 1.214 s cumulative |
| `Resources.plan` | 3,461 calls | 0.838 s cumulative |
| Battlefield generator | 1,202,759 profiled calls/resumptions | 0.887 s self time |
| Card views | 26,578 `views` calls | 0.393 s cumulative |

About 398 objects remained per game because all four libraries are in the registry. `on_battlefield()` filters that whole registry, including off-battlefield cards. Zone/controller indexes are a concrete optimization candidate, not an already measured speedup.

Isolated Step Through probe, no other hand cards, funded pool:

| Creature targets | Materialized pairs | Median of 3 choice calls |
|---:|---:|---:|
| 10 | 45 | 0.608 ms |
| 30 | 435 | 1.727 ms |
| 60 | 1,770 | 9.160 ms |

These are synthetic target-generation timings, not game timings. Lazy generation reduces unused allocations; exhaustive enumeration retains its underlying combinatorial cost.

The saved v35 unprofiled median remains 388.887 ms per eight-round game over 12 samples. Its recorded 200-game premium sweep had no safety stops. These are consistency diagnostics, not deck-strength validation or controlled cross-version comparisons.

## Validation performed in this audit

- Re-ran all 35 existing suites successfully; the runner labels the expected total as 780 tests.
- Reproduced the Frostboil provider loss without changing implementation files.
- Confirmed rejection of `Cost(black=1)`, two detailed Magnus seats and an unknown mono-black provider.
- Observed the Adventure kernel/view disagreement during casting.
- Collected the three-game profile and target-scaling probe above.
- Rechecked four saved v14 fingerprints, one per seat; all matched. This samples, rather than rechecks, the 200 stored digests.
- GitHub Actions passed for audited commit `789281e` on the configured Python matrix. No fresh 200-game sweep was needed for documentation-only changes.

## Decision

Keep the state/zone/priority/payment foundations and tests. Replace card-specific inheritance with a composed engine and typed definitions incrementally. Start the stabilization/package phases in [ROADMAP.md](../ROADMAP.md), following [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md). Broad card batches and new runtime caches wait for those gates. A wholesale rewrite and an Oracle-text interpreter are out of scope.
