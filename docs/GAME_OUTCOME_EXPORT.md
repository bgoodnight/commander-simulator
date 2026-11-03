# Longer-game life and outcome export — UI contract

## Scope

The six-deck bounded physical runner now supports **1–30 complete rounds**.
Each round contains the pilot's actions plus the next three abstract-opponent
turns when `opponent_scenario` is selected. The historical six-round default
and its existing UI/archive structures are preserved.

**Do not label this a validated Commander win rate.** The three opponent
archetypes are seeded abstract policies with finite physical battlefield cards
and combat, not actual 100-card opposing Commander decks. The model also lacks
complete poison, commander-damage, alternative-win, concede, full priority,
APNAP and player-elimination rules.

## Outcome schema

Per run:

- `life_history`: records for rounds **0, 1, …, completed_rounds**.
  Round 0 captures all four starting life totals.
- `events[t].life_totals_start` / `events[t].life_totals`: four-seat
  totals before and after the simulated round.
- `events[t].life_changes`: ordered authoritative life changes, each with
  `seat`, `kind` (`damage` / `loss` / `gain`), `amount`,
  signed `delta`, `before`, `after`, and
  `source_object_id` (nullable when the opponent event is abstract or the
  recorded effect has no source).
- `events[t].eliminations`: newly observed modeled life-zero eliminations
  with source provenance, round, and remaining life.
- `events[t].alive_seats`: players still alive after this round.
- `outcome`: `status`, `reason`, `winner_seat` (nullable),
  `complete`, `requested_rounds`, `completed_rounds`,
  `surviving_seats`, `eliminations`, `fidelity`, and
  `post_elimination_life_effects` diagnostics.

The *status* enum means:

| Status | Meaning |
|---|---|
| `win` | Modeled pilot survives and all three abstract opponents have reached zero life |
| `loss` | Pilot reaches zero life with one or more opponents surviving |
| `draw` | All seats reach zero life within the modeled events |
| `unresolved` | No terminal life-zero outcome before the configured round limit |
| `not_evaluated` | Goldfish has no opponent game model; opponent-life drain is **not** a game victory |

A loss while two opponents are alive has `winner_seat=null`.
This is **not** an unspecified winner; the winner has simply not been
determined by the bounded experiment. All later life effects on an
already-eliminated player are explicitly logged as model limitations.
Actual opposing seats are removed from abstract turns and their physical
objects leave the game via the existing zone index.

## Run a 20-round example

```bash
python tools/build_game_outcomes.py \
  --deck mortarion_physical_final \
  --scenario mixed \
  --rounds 20 --seeds 12 \
  --examples 2 \
  --output output/mortarion-20-round-outcomes.json
```

Use `--rounds 10` to compare against the old horizon or `--rounds 30` for
longer games; the new outcome batch defaults to **20 rounds**.
`--scenario` accepts `balanced`, `aggressive`, `control`, `combo` and
`mixed`. Re-running the same revision, parameters and seed range should
produce exactly the same records. Do not combine results from different
deck revisions or opponent scenarios.

The `commander-modeled-outcomes-v1` JSON has:

- `summary.outcome_counts`: modeled wins, losses, draws, unfinished games,
  and not-evaluated games; never silently drop censored results.
- `summary.life_by_round`: `observed_games`, per-seat mean/median life,
  p25/p75 bands, and the number of surviving observed players. The
  per-round denominators are necessary because games can finish early.
- `summary.round_counts_by_outcome`: distribution of stopping rounds
  by outcome category.
- `runs`: small seed-level life histories for all experiments.
- `example_replays`: **optional**, `--examples 0–3`, richer physical
  event and card-zone snapshots for clickthrough. This keeps bulk
  experiment files small.

## UI: proposed first pass

1. **Top line:** modeled Wins / Losses / Draws / Unresolved, with a
   persistent 'abstract opponents' fidelity label. Clicking a category
   filters sample games, not a derived competitive win-rate claim.
2. **All four life curves:** one per seat, with a median and interquartile
   envelope across runs, or one selected seed's exact step line.
   Show `observed_games` near later rounds, since earlier terminal games
   should not be carried forward into fabricated turns.
3. **Elimination timeline:** markers on each opponent/pilot line at
   observed zero-life rounds. Click a marker to see the source ID (or
   'unattributed abstract effect' when genuinely unknown).
4. **Outcome timing:** histogram of rounds to pilot defeat and pilot
   modeled victory, keeping unresolved games separately visible.
5. **Example game:** same chronological art-backed replay UI used by
   Deck Lab, with a new four-player life strip showing the exact
   before/after changes and attribution where available.
6. **Controls:** 10/20/30-round horizon; scenario; deck; seed;
   sample size. Keep the existing six-round baseline available rather
   than silently replacing it.

## Outstanding fidelity

The current opponent engine provides useful exploratory endgames but does
not offer all legal 100-card decks or a complete action/priority stack.
Review replacement effects, commander-damage counters, game-loss effects,
opponent elimination cleanup and attacker choice before promoting these
modeled results to competitive diagnostics. More games cannot compensate
for missing rules; keep uncertainty and unmodeled actions visible.

## Full observation archive for feature engineering (next batch)

When invoking `tools/build_game_outcomes.py` with `--observations-output`, the
runner writes a *separate* JSONL file with one actual recorded game per line:
kept opening hand and mulligan, exact deck/pilot/opponent cohort, complete
ordered turn events, actual turn-boundary card-zone snapshots, four-seat life
history, outcome and fidelity. This is **not** a matrix of predetermined
statistical predictors. Unknown legality, omitted actor/source IDs and
unsupported rules must remain explicitly unknown, never imputed.

Both production simulation workflows now capture and validate this sidecar for
every game, compress it, and attach it to the immutable GitHub Release. The
existing public UI JSON files remain small and backward compatible; they
continue to retain only a few full example replays.

See [Observation capture contract](SIMULATION_OBSERVATIONS_CONTRACT.md) for the
next batch's requirements and downstream time-aware feature engineering.
