# Commander Simulator — Recovery Snapshot (2026-10-28)

## Status and intended use
This is a complete checkpoint of the reusable Python Commander simulation project as developed in ChatGPT on 2026-10-28. The current baseline is **v5, a four-player abstract-archetype game engine**, not yet a fully validated Magnus the Red deck simulator.

## Where to resume
- `simulator/v5_four_player/`: **CURRENT baseline**, including `simulation.py`, 7 configurable archetypes, typed actions and effects, four-player life/combat/counter/removal/finishers, `tests.py`, `results_v5.json`, four narrated replays, calibration report, and the v3 bridge manifest.
- `simulator/v4_abstract_opponents/`: earlier three-opponent stochastic threat engine / snowball tests.
- `simulator/v3_magnus_modular/`: named-card behavior (`cards.json`), deck membership (`deck_v16.json`), combo recipes (`combos.json`), pilot, tests, and sample games. Has partial card coverage; do not interpret win rates as accurate.
- `decklists/`: Magnus v1–v1.6 lists (latest `magnus_thousand_sons_v1_6.txt` and `_import.txt`). Keep original Warhammer/Tzeentch creature contingent and prescribed theme.
- `prior_work/`: earlier v1–v2 scripts, reports and raw results.
- `original_archives/`: byte-for-byte original versioned ChatGPT ZIP artifacts, included for redundancy.
- `MANIFEST_SHA256.txt`: SHA-256 hashes of all files to verify integrity.

## Run tests (Python standard library)
From the extracted snapshot root:

```bash
python simulator/v5_four_player/tests.py
python simulator/v4_abstract_opponents/tests.py
python simulator/v3_magnus_modular/tests.py
```

At checkpoint: 21 tests pass in v5, 15 in v4, 20 in v3.

## Last calibration (synthetic)
2,800 random four-player tables in v5; 97.9% ended by round 30, median finishing round 18. Win/share among occupied archetype seats: Aggro 17.5%, Tokens 25.1%, Ramp/Stompy 29.5%, Control 21.2%, Spellslinger 24.9%, Midrange 26.7%, Combo 26.2%. Control-mirror games persist much longer. These figures are model outputs, not real-world Commander estimates.

## Critical next steps
1. Calibrate overly long games and the Aggro/Ramp imbalance without forcing equal win rates.
2. Add shared colored-mana and named-card effect/stack compatibility to v5, with explicit unmodeled-card warnings.
3. Adapt the modular v3 card/combination catalog and pilot into the common player interface; ensure all deck cards have accurate behavior.
4. Validate narrated games and rules tests, then compare Magnus policy/deck variants only under paired, reproducible scenarios.

## Recovery workflow
If resuming in a future ChatGPT session, upload this archive and ask: "Resume the Commander Simulator from the 2026-10-28 v5 checkpoint; read RECOVERY_README.md, run tests, and preserve the v3 card/combination catalogs when integrating a real deck." 

The ZIP is a snapshot, not a running background process. Keep the snapshots in Drive and source files in a dedicated GitHub repository with tags for v3/v4/v5 after GitHub repository access is configured. Do not publish any unrelated personal data or private credentials.
