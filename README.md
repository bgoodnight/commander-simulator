# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v13** (October 28, 2026): exact selection for the existing draw/look spells, Harmonic prowess and self-exclusion, Storm-Kiln artifact power, Baral loot and Stormsplitter next-end-step exile. V12 expanded combat, live zones, source-ID mana and typed priority remain active. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## Current architecture and scope

- [V13 selection/engines README](simulator/v13_engines/README.md) — exact resolution choices and focused missing engine text.
- [Current Magnus card coverage](simulator/v13_engines/CARD_COVERAGE.md) — 32 supported subsets, 16 partial and 35 unsupported distinct names.
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

**Live v13 limits:** one detailed Magnus deck plus synthetic opponents. Explicit turn steps, priority, multiple blockers, trample and first/double strike remain live. Six selection spells now enforce ordered resolution choices; four engine cards gained missing text. No previously unsupported named card was enabled. Special-land/utility adapters, general copy/layer effects, draw/scry triggers/replacements, full legend/Commander rules, attachments and verified loops remain absent or partial as audited. No deck win-rate conclusions are supported.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**491 tests across thirteen suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34, v9c:49, v10:51, v11:50, v12:50, v13:69). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run live v13 and reproduce validation:

```bash
python simulator/v13_engines/tests.py
python simulator/v13_engines/coverage_report.py
python simulator/v13_engines/validate_engines.py
```

The v13 validator writes seven targeted interaction stories (five conserved selection branches in the first) and their JSON diagnostics, an interaction report and validation_results.json. By default it checks 200 twelve-round games across all Magnus seats and compares 12 eight-round timing samples per engine. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The pre-v13 rollback point is `d15da6c9ee641b4743c916ab39ff591bd0e9d4f8`. V13 adds its own directory, descriptor-driven power/self-exclusion and successful-counter controller event plumbing. Historical descriptors keep their prior behavior. Historical suites pass; dated manifests remain checkpoint records. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

Special-land entry/utility rules remain the next P1 gap. Then prioritize spell copies, relevant creature activations/tutors, graveyard casting and combo validation. Broader damage keywords and attachments remain future rule milestones. Keep source-paid narratives and independent state/payment/priority checks while profiling larger runs.
