# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v18**: canonical v1.13 budget deck adapter, plus v17 Mystical Tutor search and v16 Otawara and Sokenzan channel abilities, building on v15 Mystic Sanctuary's targeted graveyard-return trigger, Fiery Islet's draw activation, and Riptide Laboratory's 1U Wizard-return activation. V14 land rules and reference fingerprints, v13 selection/engines, v12 combat, live zones and source-ID mana remain active. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## V18 canonical budget deck

The authoritative [v1.13 budget list](decklists/magnus_thousand_sons_v1_13_budget.txt) is loaded by [BudgetTable](simulator/v18_budget_deck/README.md). Identity and color verification remain incomplete; 29 names are unverified and inert. See the [v1.13 audit](simulator/v18_budget_deck/CARD_COVERAGE.md) and [assessment](simulator/v18_budget_deck/ASSESSMENT.md). Prior tables retain historical decks for regression.

## V17 tutor

[Mystical Tutor](simulator/v17_tutor/README.md) adds instant-speed search with resolution-time choice and shuffle; see [current coverage](simulator/v17_tutor/CARD_COVERAGE.md), [interaction narrative](simulator/v17_tutor/INTERACTION_REPORT.md), and [validation](simulator/v17_tutor/validation_results.json).

## V16 channel

[Channel implementation](simulator/v16_channel/README.md) adds Otawara and Sokenzan as a bounded subset, with known token-color and metadata limits. See its [interaction report](simulator/v16_channel/INTERACTION_REPORT.md) and [coverage audit](simulator/v16_channel/CARD_COVERAGE.md) for validation and remaining gaps.

## Current architecture and scope

- [V15 utility-land README](simulator/v15_utility/README.md) — Sanctuary target timing, Islet costs and Riptide target rechecks.
- [Historical v15 Magnus coverage](simulator/v15_utility/CARD_COVERAGE.md) — 41 supported subsets, 7 partial, 35 unsupported names.
- [V15 interaction report](simulator/v15_utility/INTERACTION_REPORT.md) — six narratives, live sweep and runtime.
- [V15 assessment](simulator/v15_utility/ASSESSMENT.md) — validation and remaining limits.

- [V14 land README](simulator/v14_lands/README.md) — individual entry checks, basic types, life/face choices and Passage costs/resolution.
- [Historical v14 Magnus coverage](simulator/v14_lands/CARD_COVERAGE.md) — 38 supported subsets, 10 partial and 35 unsupported names.
- [V14 interaction report](simulator/v14_lands/INTERACTION_REPORT.md) — seven source-paid stories, live sweep and timing.
- [V14 assessment](simulator/v14_lands/ASSESSMENT.md) — results, remaining scope and pre-optimization reference.
- [Reference cases](simulator/v14_lands/REFERENCE_CASES.json) and [performance history](simulator/v14_lands/PERFORMANCE_HISTORY.json) — deterministic outputs for later caching comparisons; no new caching yet.

- [V13 selection/engines README](simulator/v13_engines/README.md) — exact resolution choices and focused missing engine text.
- [Historical v13 Magnus card coverage](simulator/v13_engines/CARD_COVERAGE.md) — 32 supported subsets, 16 partial and 35 unsupported distinct names.
- [V13 interaction report](simulator/v13_engines/INTERACTION_REPORT.md) — seven source-paid stories, including five selection branches, plus the live sweep.
- [V13 assessment](simulator/v13_engines/ASSESSMENT.md) — validation, timing and remaining limits.

- [V12 combat/audit README](simulator/v12_combat/README.md) — allocation choices, trample and two damage steps.
- [Historical v12 card coverage and triage](simulator/v12_combat/CARD_COVERAGE.md) — all 100 cards: 23 supported subsets, 25 partial and 35 unsupported distinct names.
- [V12 interaction report](simulator/v12_combat/INTERACTION_REPORT.md) — six targeted narratives, source payments and the live sweep.
- [V12 assessment](simulator/v12_combat/ASSESSMENT.md) — validation, timing and remaining limits.

- [V11 steps/cards README](simulator/v11_steps/README.md) — ordinary turn windows, combat batch and the focused card/rule expansion.
- [V11 interaction report](simulator/v11_steps/INTERACTION_REPORT.md) — observed results from five targeted stories and the seeded sweep.
- [V11 assessment](simulator/v11_steps/ASSESSMENT.md) — validation, fixes, efficiency and remaining limits.
- [V10 priority README](simulator/v10_priority/README.md) — four-seat passes, APNAP triggers, instant responses and registered activated frames.
- [V10 assessment](simulator/v10_priority/ASSESSMENT.md) — stack/priority validation, conservation sweep, timing and remaining gates.
- [V9c source-mana README](simulator/v9c_mana/README.md) — live source objects and bounded ordered mana-ability payment for every seat.
- [V9c assessment](simulator/v9c_mana/ASSESSMENT.md) — acceptance tests, conservation/payment sweep, efficiency review and remaining boundaries.
- [V9b live-zone README](simulator/v9b_live/README.md) — authoritative live inventories, read-only card projections, physical spell/permanent identity and 34 migration tests.
- [V9b assessment](simulator/v9b_live/ASSESSMENT.md) — correctness review, 400-game conservation sweep, timings and next gates.
- [V9a README](simulator/v9_kernel/README.md) — portable Magnus seat, central object-zone operations, bounded source-specific mana prototype, 29 focused new tests and four narrated games.
- [V9a assessment](simulator/v9_kernel/ASSESSMENT.md) — validation, limitations, and next integration gates.
- [V8 README](simulator/v8_central/README.md) — persistent shared battlefield, four-seat turn driver, bounded counterspell stack, and baseline implementation.
- [V8 assessment](simulator/v8_central/ASSESSMENT.md) — original limitations and confidence boundaries.
- [V7 rules kernel](simulator/v7_rules/README.md) — reusable rule primitives and safe finite loop infrastructure.
- [Real Magnus deck integration](simulator/v6_real_deck/README.md) — original partial real 99-card adapter.
- [Magnus v1.6 decklist](decklists/magnus_thousand_sons_v1_6.txt), [v3 card catalog](simulator/v3_magnus_modular/cards.json), and [candidate combo lines](simulator/v3_magnus_modular/combos.json).

**Historical v15 limits:** one detailed Magnus deck plus synthetic opponents. Sanctuary, Fiery Islet and Riptide Laboratory join the prior individual land-entry rules and Fabled Passage. Channel, full double-faced/layer/replacement behavior, spell-copy producers, full legend/Commander rules, attachments and verified loops remain absent or partial as audited. No additional caching is introduced; v14 reference outputs are preserved for later optimization. No deck win-rate conclusions are supported.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**610 tests across eighteen suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34, v9c:49, v10:51, v11:50, v12:50, v13:69, v14:56, v15:38, v16:14, v17:6, v18:5). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run historical v15 and reproduce validation:

```bash
python simulator/v15_utility/tests.py
python simulator/v15_utility/coverage.py
python simulator/v15_utility/validate.py
```

The v15 validator writes six targeted interaction stories, JSON diagnostics, an interaction report and validation_results.json. By default it checks 200 twelve-round games across all Magnus seats and compares 12 eight-round timing samples per engine. V14 reference fingerprints remain preserved. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The pre-v15 rollback point is `b0b0237ee915532b4d2f4ca3b089999671294b27`. V15 adds a utility-land provider/table and backward-compatible trigger target-preparation seam; existing cache implementations remain untouched. Historical suites pass; dated manifests remain checkpoint records. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

First verify v1.13 card identity and color identity, then prioritize Magnus cost reduction, buyback, convoke, token generation, tutors, Wizard/Shaman triggers and Underworld Breach. Add spell-copy mechanics and validate combo lines as their prerequisites are implemented. Track runtime while building functionality; defer additional caching and compare later optimized outputs against the versioned v14 deterministic reference cases. Keep source-paid narratives and independent state/payment/priority checks.
