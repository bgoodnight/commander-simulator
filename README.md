# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v9a** (October 28, 2026), an incremental integration of the v8 central shared battlefield with portable detailed-seat placement and separately validated kernel-backed card-zone/mana services. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

## Current architecture and scope

- [V9a README](simulator/v9_kernel/README.md) — portable Magnus seat, central object-zone operations, bounded source-specific mana prototype, 29 focused new tests and four narrated games.
- [V9a assessment](simulator/v9_kernel/ASSESSMENT.md) — validation, limitations, and next integration gates.
- [V8 README](simulator/v8_central/README.md) — persistent shared battlefield, four-seat turn driver, bounded counterspell stack, and baseline implementation.
- [V8 assessment](simulator/v8_central/ASSESSMENT.md) — original limitations and confidence boundaries.
- [V7 rules kernel](simulator/v7_rules/README.md) — reusable rule primitives and safe finite loop infrastructure.
- [Real Magnus deck integration](simulator/v6_real_deck/README.md) — original partial real 99-card adapter.
- [Magnus v1.6 decklist](decklists/magnus_thousand_sons_v1_6.txt), [v3 card catalog](simulator/v3_magnus_modular/cards.json), and [candidate combo lines](simulator/v3_magnus_modular/combos.json).

**Live v9a game limitations:** the detailed real Magnus deck may occupy any of four seats, but only **one detailed player** per table is supported; other seats are synthetic archetypes. Legacy hands, libraries, mana sequencing and counter-only priority remain active. The v9 kernel-owned `KernelZones` and `TypedMana` services are separately tested, **not yet installed in the live game**. Unsupported card behavior fails closed rather than being fabricated. More named card coverage, complete priority, multi-detailed tables, and statistical optimization are future milestones.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**188 tests across seven versions** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9:29). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run v9 diagnostics:

```bash
cd simulator/v9_kernel
python tests.py
python run_narratives.py
python benchmark.py
```

## Preservation and methodology

Each milestone is additive under `simulator/vN_*`. Earlier versions remain standalone and reproducible; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Next milestone

Migrate draw/mulligan/hand/graveyard/land and spell movement in the live v8-derived table to **one authoritative object registry**. Replace legacy mutable lists with read-only projections; wire a source-backed resource policy and full triggered stack/priority, then unlock several real decks and verify the complex Magnus interactions. Do not optimize deck wins until that simulation is credible.
