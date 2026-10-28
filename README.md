# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v9b** (October 28, 2026): all four live seats now draw, cast, resolve, discard, play lands and leave the game through one kernel-owned physical-card registry. Magnus remains portable across seats. Mana and general priority are still unfinished. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## Current architecture and scope

- [V9b live-zone README](simulator/v9b_live/README.md) — authoritative live inventories, read-only card projections, physical spell/permanent identity and 34 migration tests.
- [V9b assessment](simulator/v9b_live/ASSESSMENT.md) — correctness review, 400-game conservation sweep, timings and next gates.
- [V9a README](simulator/v9_kernel/README.md) — portable Magnus seat, central object-zone operations, bounded source-specific mana prototype, 29 focused new tests and four narrated games.
- [V9a assessment](simulator/v9_kernel/ASSESSMENT.md) — validation, limitations, and next integration gates.
- [V8 README](simulator/v8_central/README.md) — persistent shared battlefield, four-seat turn driver, bounded counterspell stack, and baseline implementation.
- [V8 assessment](simulator/v8_central/ASSESSMENT.md) — original limitations and confidence boundaries.
- [V7 rules kernel](simulator/v7_rules/README.md) — reusable rule primitives and safe finite loop infrastructure.
- [Real Magnus deck integration](simulator/v6_real_deck/README.md) — original partial real 99-card adapter.
- [Magnus v1.6 decklist](decklists/magnus_thousand_sons_v1_6.txt), [v3 card catalog](simulator/v3_magnus_modular/cards.json), and [candidate combo lines](simulator/v3_magnus_modular/combos.json).

**Live v9b limitations:** one detailed Magnus deck and three synthetic archetypes; no multiple-real-deck games yet. Hands, libraries, graveyards, exile, command, stack and battlefield are kernel-owned; pilot card lists are read-only projections. Legacy colored/fungible mana policies and source readiness remain active. The isolated v9a `TypedMana` planner is **not connected to live payment**. Priority is still counter-only, with cast triggers settling before responses. Named-card selection, land behavior and cleanup timing retain documented approximations. Unsupported spells fail closed; these diagnostics cannot support deck win-rate conclusions.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**222 tests across eight suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run live v9b and reproduce validation:

```bash
python simulator/v9b_live/tests.py
python simulator/v9b_live/validate.py
```

`validate.py` writes four narrated replays and `validation_results.json`; by default it checks 400 twelve-round games across all Magnus seats and compares 40 ten-round timing samples per engine. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The v9a rollback point is commit `e008778493d9ad93a9a534509e015caf17fe39a8`. V9b adds its own directory and two optional shared-stack checks for spells removed when their owner leaves; all historical tests pass. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

Wire live mana production/payment to source object IDs, including tap/untap, floating mana, Treasure sacrifice and activation costs. Preserve explicit synthetic resource approximations. Then generalize triggered/activated stack frames and priority before enabling multiple real decks or expanding complex Magnus interactions. Profiled full-registry consistency checks are a known performance cost; optimize only while retaining conservation checks. Do not optimize deck wins until the simulation is credible.
