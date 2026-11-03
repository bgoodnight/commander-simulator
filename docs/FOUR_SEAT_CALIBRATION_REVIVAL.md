# Four-seat AI calibration revival — November 3, 2026

This work **restores** the original seven-archetype four-active-seat sandbox at
`simulator/v5_four_player` as an independent calibration tool. It **does not**
replace or mutate the current source-pinned physical Commander engine.

## Historical implementation confirmed

- `simulator/v4_abstract_opponents`: 3 live generic decks and passive Magnus.
- `simulator/v5_four_player/simulation.py`: all four seats have independent,
  shuffled 99-card synthetic category decks; hand, lands, ramp, source mana,
  creatures, interaction, removal, counterspells, game-ending effects.
- `simulator/v5_four_player/experiments.py`: old randomized tables, mirror
  matches and controlled lineups. Historical 2,800 random-table games had
  median completion round 18 and 97.9% completion within 30 rounds.
- `simulator/v6_real_deck`: partial named Magnus bridge, **not** full-coverage.
- `simulator/v8_central` through `v35_copy_targets`: progressively shared
  physical objects and four-seat action/priority rules, but still only one
  detailed deck against three synthetic policies in the tested host.
- Current `commander_sim/early_game_runner.py`: one source-pinned physical
  deck at seat 0 against three bounded **abstract** opponent seats.

These engines cannot be equated by their respective win rates. Use the same
benchmark structure, not a wholesale transplant of outdated effect handling.

## New reproducible small benchmark

Run:
```sh
python tools/four_seat_calibration.py --mirrors 20 --rotations 4 --rounds 30 \
  --seed 20261103 --output dist/four-seat/calibration.json \
  --records dist/four-seat/games.jsonl
```

Seven mirror archetypes x 20 games = 140 games. Four distinct archetypes
(Aggro, Control, Combo, Midrange) x every permutation of four seat assignments
x four repetitions = 96 games. **236 games total.** Every seat gets a genuine
shuffled generic deck and obeys the same shared v5 policies and game host.

In the first completed pass, 225/236 games resolved by round 30; median
**completed** terminal round 19. Seat wins were P0 59, P1 46, P2 60, P3 60,
and 11 unresolved. This sample cannot rule out moderate seat differences;
seat order is separately randomized and measured.

The resulting `testdata/four-seat-calibration/calibration.json` includes
seat/order exposure, mirror fairness, role win shares, ending causes and
observed development by turn for all seven abstract archetypes. The workflow
artifact also contains all individual per-round game histories.

## Next: genuinely source-pinned deck-versus-deck

Build a **four-seat physical host**, not a fictional conversion of printed
cards to generic effects. In order:

1. Generalize the current per-seat deck assembly (pinned catalog, library,
   hand, command zone, mulligan, color-accurate mana, pilot context), so
   **each** seat can be a named physical deck or abstract calibration adapter.
2. Share the same `Kernel`, `Zones`, `Life`, cost planner and action
   resolution across all four seats. Preserve owner/controller, stack
   priority, every turn's actor, and per-seat life-zero/draw-loss SBAs.
3. Reuse `pilot_policy.py` to rank legal actions for any controller; avoid
   any name-, seat- or commander-specific pilot behavior. Archetype/tier
   controls tune permitted decisions and generic deck composition only.
4. Compare four-way mirrors, all seat rotations, and mixed named deck
   matchups; measure legal actions/round, mana by round, board threats,
   first attempted win, response availability and terminal round.
5. Keep failures, unsupported actions, censored games and true game
   eliminations distinct. Persist a full outcome/evidence record per game.
6. Only after actual named decks play source-grounded actions through this
   common host should reports claim deck-vs-deck win shares.

A generic-card **projection** of real lists could support extra exploratory
tests, but must be labeled approximation and never be used in place of actual
card-text fidelity. Do not publish any of this calibration data as live Deck
Lab matchup results until equivalent-host tests pass.
