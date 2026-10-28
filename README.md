# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v10** (October 28, 2026): all four live seats use shared physical zones, source-ID mana and a typed priority stack for spells, triggers and registered activated abilities. The turn/combat driver and named-card coverage remain partial. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## Current architecture and scope

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

**Live v10 limitations:** one detailed Magnus deck and three synthetic archetypes. Physical zones, source tap flags and U/R/colorless pools remain kernel-owned. Spell, trigger and registered activation frames share one LIFO stack with living-player priority, APNAP ordering and state-based checkpoints. Supported instants can respond; ordinary spell counters cannot target ability frames. Mind Stone's nonmana draw activation is live. The coarse turn/serial combat driver still omits official steps/windows; many card effects, activations, mana colors/costs, copying, buyback and commander damage remain unsupported or approximate. Unsupported behavior fails closed. No deck win-rate conclusions are supported.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**322 tests across ten suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34, v9c:49, v10:51). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run live v10 and reproduce validation:

```bash
python simulator/v10_priority/tests.py
python simulator/v10_priority/validate.py
```

`validate.py` writes four narrated replays and `validation_results.json`; by default it checks 400 twelve-round games across all Magnus seats and compares 40 ten-round timing samples per engine. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The pre-v10 rollback point is `e66c06f7526802ea1b60db38d73bd416923f8c90`. V10 adds its own directory and an optional reserved-source parameter in v9c payment planning, so tap/sacrifice activation costs cannot double-spend their source. Historical suites pass; their standalone behavior is retained. Dated manifests remain checkpoint records. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

Refine the phase/step and combat driver to expose the missing official timing windows. Expand verified effect/activation coverage and mana capabilities before enabling multiple detailed decks. Keep independent state, payment and priority audits while profiling the added window/choice costs. Do not optimize deck wins until the simulation is credible.
