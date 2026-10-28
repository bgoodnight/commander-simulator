# Commander Simulator

A reproducible, modular **four-player Magic: The Gathering Commander simulation project**. The current baseline is **v5**, a stochastic, abstract-archetype simulator; Magnus the Red is the first planned fully modeled 100-card deck.

> **Current scope:** This is *not* a complete Magic rules engine. v5 simulates abstract decks and game outcomes; its Magnus v1.6 card catalog is included for future integration but **is not yet represented by full-card simulations or win-rate results**.

## Start here

- [v5 simulation README](simulator/v5_four_player/README.md): architecture, CLI commands, assumptions, integration API.
- [v5 calibration report](simulator/v5_four_player/CALIBRATION_REPORT.md): mixed and mirror matchup findings and known limitations.
- [Recovery README](RECOVERY_README.md): version history, continuity, and pending development tasks.
- [v3 card catalog](simulator/v3_magnus_modular/cards.json), [v3 combo definitions](simulator/v3_magnus_modular/combos.json), [Magnus v1.6 deck](decklists/magnus_thousand_sons_v1_6.txt).

## Quick test

Requires Python 3.10 or later; no external packages:

```bash
python simulator/v5_four_player/tests.py
python simulator/v4_abstract_opponents/tests.py
python simulator/v3_magnus_modular/tests.py
```

At the 2026-10-28 checkpoint, these passed **21**, **15**, and **20** tests respectively.

To generate a new v5 calibration batch:

```bash
cd simulator/v5_four_player
python experiments.py --mixed 2800 --mirrors 120 --controlled 140 --limit 30 --seed 20261028
python make_report.py
```

## Repository organization

| Path | Contents |
| --- | --- |
| `simulator/v5_four_player/` | Current four-player abstract engine, seven archetypes, tests, experiment runner, replays, results, integration demo |
| `simulator/v4_abstract_opponents/` | Prior stochastic threat generator and snowball calibration |
| `simulator/v3_magnus_modular/` | Card definitions, combo recipes, named-card engine/pilot, and tests |
| `decklists/` | Historical Magnus deck versions, through v1.6 |
| `prior_work/` | Earlier simulator approaches and findings |
| `MANIFEST_SHA256.txt` | Checksums for original snapshot artifacts |

## Backups and next steps

- A full dated ZIP, Git-ready source ZIP, and independently restorable offline Git bundle are saved in the [Google Drive Commander Simulator backup](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y).
- Next: calibrate game duration and archetype balance, implement precise per-card/mana/stack hooks, and bridge the real Magnus deck into the v5 player interface.
- Keep the repository private while exploring experimental card/deck simulations. Avoid committing personal credentials or unrelated personal data.

**Project checkpoint:** 2026-10-28 · first GitHub source import from verified local + Google Drive archives.
