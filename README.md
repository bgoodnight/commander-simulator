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


## V6 diagnostic integration (October 28, 2026)

- [Real-deck integration README](simulator/v6_real_deck/README.md) and [assessment](simulator/v6_real_deck/ASSESSMENT.md): actual Magnus v1.6 library and commander zone against three stochastic v5 opponents.
- Run `python simulator/v6_real_deck/tests.py` (21 tests); from that folder, `python run_narratives.py` regenerates three random-opening games plus one explicitly forced-opening diagnostic.
- **Do not infer win rates or propose deck changes yet:** 38 named nonland cards remain unimplemented, and selection, stack/priority, card-specific mechanics, and win conditions remain incomplete.
- The v3/v4/v5 source code is unchanged; GitHub's prior v5 import commit can be restored or this v6 change reverted without force-pushing.


## V7 modular rules and loop-safety prototype (October 28, 2026)

- [V7 rules kernel README](simulator/v7_rules/README.md) and [V7 assessment](simulator/v7_rules/ASSESSMENT.md): reusable typed card/object descriptions, static and triggered abilities, zones, keyword/counter rules, damage and targeting, plus four qualitative mixed-table game traces.
- Run `python simulator/v7_rules/tests.py` (50 tests). All five versioned suites currently pass (127 tests total).
- [Loop safety](simulator/v7_rules/loops.py): fail-closed resource/action/time limits, repeated-state detection, and finite symbolic summaries for **separately verified** repeatable loops. No actual Magnus infinite combo has been certified yet.
- **Scope:** V7 is a shared rules kernel and incremental v6 bridge; the full multiplayer stack, precise mana source activations and the remaining unimplemented Magnus cards are not yet integrated. Do not interpret the short replay outcomes as deck win rates.
- GitHub history retains the prior V6 baseline, and a separate V7 recovery ZIP is backed up in the same Google Drive Commander Simulator folder.


## V8 persistent shared multiplayer kernel (October 28, 2026)

- [V8 code, 32 new tests, and four diagnostic replays](simulator/v8_central/README.md) | [assessment of limitations](simulator/v8_central/ASSESSMENT.md).
- `simulator/v8_central/kernel.py`: **persistent** per-game creature/permanent/token state, shared combat/damage/zone rules across all four seats. `stack.py`: bounded nested counterspell responses. `turns.py`: one four-seat turn driver. `responses.py`: declarative counterspell riders.
- Run `python run_all_tests.py` from the repository root (159 passing regression tests across v3-v8); a GitHub Actions workflow also runs all suites on pushes and pull requests.
- **Scope:** the real Magnus deck still has unsupported named cards; hand/library/land/mana source policies and general spell/trigger priority are not yet fully migrated. These are diagnostic simulations, **not** validated deck win-rate data.
- The independent v7 commit (`622ec87a6249ec7726af705c74084a31d993619b`) remains available for revert/branch. Recovery ZIP also saved to the existing Google Drive backup folder.
