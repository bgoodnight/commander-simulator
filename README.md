# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v9c** (October 28, 2026): all four live seats use one physical-card registry and source-ID mana payment, with ordered activation costs, tap/untap, floating pools and Treasure sacrifice. General stack priority remains unfinished. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## Current architecture and scope

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

**Live v9c limitations:** one detailed Magnus deck and three synthetic archetypes. Physical zones, source tap flags and U/R/colorless pools are authoritative in the shared kernel. The new bounded planner handles U/R/generic spell and activation costs; the isolated v9a DFS and legacy `ColoredPayment` no longer pay live v9c spells. Synthetic lands/ramp retain explicit approximate abilities. Only the modeled U/R subset of Treasure colors is available. Fellwar Stone and Exotic Orchard derive colors from opposing modeled lands; synthetic colorless lands supply neither with a color. Priority remains counter-only, with cast triggers settling before responses. Some selection, land behavior and phase timing remain approximate. Unsupported behavior fails closed; no deck win-rate conclusions are supported.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**271 tests across nine suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34, v9c:49). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run live v9c and reproduce validation:

```bash
python simulator/v9c_mana/tests.py
python simulator/v9c_mana/validate.py
```

`validate.py` writes four narrated replays and `validation_results.json`; by default it checks 400 twelve-round games across all Magnus seats and compares 40 ten-round timing samples per engine. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The pre-v9c rollback point is `eb32c1153ca6793cc0a69d66f6bc6919dd7eb374`. V9c adds its own directory, extracts backward-compatible construction/resource hooks in v9b, and guards legacy source-name accounting in the shared battlefield. Historical suites pass; their standalone behavior is retained. Dated manifests remain checkpoint records. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

Generalize triggered/activated stack frames and priority before enabling multiple real decks or expanding complex Magnus interactions. Replace the coarse phase driver with actual step boundaries, and extend source descriptors beyond the modeled U/R subset as needed. Keep exhaustive conservation/payment validation while profiling projection and planning costs. Do not optimize deck wins until the simulation is credible.
