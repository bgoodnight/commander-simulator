# v6 — Real-deck vertical integration

**Status:** diagnostic alpha, not a credible Magnus win-rate engine. The old v5 four-player abstract engine is **unchanged** and imported as a module.

This stage injects an actual 99-card Magnus v1.6 library (with commander in the command zone) into seat 0, next to three distinct abstract v5 seats. Every action uses the typed `CardSpec`, `Action`, `Creature`, `Permanent`, `Pilot` and `Table` interfaces. The purpose is to catch infrastructure and legality problems early, not to tune cards or measure deck win rate.

## Commands

Requires Python 3.10+ and no external dependencies. From `simulator/v6_real_deck`:

```bash
python tests.py
python run_narratives.py
```

The narrative script regenerates exactly **four** reproducible, human-readable replays and their machine-readable state logs: three natural draws and one labeled forced-opening diagnostic. It does not run Monte Carlo calibration.

To run a manual matchup:

```python
from integrated import MixedTable
sim = MixedTable(('aggro','control','combo'),seed=102,trace=True).run(10)
print(sim.summary())
print(sim.diagnostics())
print('\n'.join(sim.events))
```

## Structure

- `integrated.py` contains a `DetailedPlayer`, `MagnusPilot`, `ColoredPayment`, and `MixedTable` adapter. V5 stays authoritative for abstract opponents, threat targeting, typed actions, removals, life, and multiplayer eliminations.
- `tests.py` checks 21 invariants including color payments, fliers, the command zone, tokens, response costs, and named-card interactions.
- `run_narratives.py`, `0*.md`, `0*.json`, `narrative_results.json`: reproducible narrative inspection fixtures.
- `ASSESSMENT.md`: concrete findings, card-coverage gaps, limits, and next steps.

**No silent fallback:** real nonland cards without an implemented behavior are tracked as unsupported and cannot be cast. Some named supported effects are only approximate; this is marked in `diagnostics()`.

## Baseline and rollback

This version adds a new directory without modifying v3/v4/v5. Normal Git commits preserve history. To undo the import, revert its commit or switch to the v5 baseline commit; do not force-push. The separate complete recovery copy remains in Google Drive.
