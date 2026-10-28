# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v11** (October 28, 2026): explicit ordinary turn steps and simultaneous ordinary combat damage, plus Abrade, Capsize/buyback, Arcane Adaptation's Wizard choice and upgraded Frantic Search. Shared zones, source-ID mana and typed priority remain active. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## Current architecture and scope

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

**Live v11 limits:** one detailed Magnus deck plus synthetic opponents. Ordinary steps, priority around attacks/blocks, both main phases and one simultaneous ordinary combat damage batch are live. The card expansion covers three new named cards and one upgraded effect; it does not mark the whole deck complete. One blocker per attacker, limited combat keywords, selected card choices/cost forms, partial land/selection adapters and temporary-token cleanup remain boundaries. No multi-block, first/double strike, trample, planeswalker loyalty, copied spells, commander damage or verified loops. Unsupported behavior fails closed. No deck win-rate conclusions are supported.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**372 tests across eleven suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34, v9c:49, v10:51, v11:50). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run live v11 and reproduce validation:

```bash
python simulator/v11_steps/tests.py
python simulator/v11_steps/validate.py
```

`validate.py` writes five targeted interaction stories, two unforced live replays, an interaction report and `validation_results.json`. By default it checks 200 twelve-round games across all Magnus seats and compares 20 eight-round timing samples per engine. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The pre-v11 rollback point is `a1c3aa774b97708e5e16bd972255365ec82738f0`. V11 adds its own directory plus backward-compatible derived-subtype, announced-action and trigger-operation seams in the shared code. Historical suites pass; dated manifests remain checkpoint records. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

Expand verified card/activation coverage in similarly small interaction-tested batches. Combat keywords/multiple blockers, delayed triggers, more land abilities and broader card choices remain gates before several detailed decks and statistical deck comparisons. Keep narrated diagnostics and independent state/payment/priority audits while profiling the added windows and choices.
