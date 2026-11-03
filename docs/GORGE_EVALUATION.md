# Experimental gorge Commander backend: simulation impact trial

**Status:** opt-in benchmark only. The Python rules kernel, existing AI pilot,
sim outputs and UI remain the production implementation. PR and CI compare
runtime characteristics; they do not silently switch the simulation engine.

## Which decks are actually played?

`tools/export_gorge_decks.py` exports the pinned, hash-validated, 100-card
fixture lists (including each commander), without downloading new Oracle text.
The `gorge_commander_probe.go` driver loads the 100 cards for each of:

- Mortarion Current
- Magnus Premium
- Necron Dynasties
- Wretched Ranks

The benchmark explicitly requests `rules.FormatCommander`, sends one
commander index per seat, and rotates the four decks through player seats. It
uses gorge's `bot` policy (not our Python pilot). It checks Commander deck
legality as seen by gorge, allows a turn cap, and replay-verifies every complete
match. This is not gorge's stock `mtgsim` command: that command's default
Commander deck fixtures are played with **constructed** format and 20 life.

## How to run

The GitHub workflow
`.github/workflows/gorge-commander-evaluation.yml` can be triggered manually.
It also runs when the benchmark files change on a PR. It clones a **pinned**
upstream gorge commit and fetches Forge's GPL card scripts into a temporary,
untracked, runner-local cache. The card scripts and compiled corpus are never
committed to or uploaded from this repository.

The workflow produces a `gorge-commander-evaluation` Actions artifact:

| File | Contents |
|---|---|
| `gorge_runs.jsonl` | One JSON record per Commander game; seed, seating, result, stall, turns, intents, events, warm runtime, verified replay |
| `python_baseline.json` | Bounded 10-round Python runs against **three abstract opponents** |
| `comparison.json` | Separate metrics and limitations, not win-rate equivalence |
| `gorge_exit_code.txt` | Whether the optional gorge probe saw errors, stalls or replay failures |

## Interpreting results carefully

- Python currently uses an abstract opponent model, short horizon and a
  different event vocabulary. Gorge uses **four full decks** and potentially
  longer games. The game speeds and win rates are **not apples to apples**.
- `games_per_minute` measures **warm execution** on the GitHub runner, not
  the initial clone, corpus download, compilation or Go build. Measure setup
  time separately before deciding whether to run many small jobs.
- A completed gorge game establishes that the deck could be loaded and a game
  reached an end. It **does not prove** every card's printed ability worked
  correctly, every triggered effect fired or the bot played optimally.
- Card legality and the source library are bound to the pinned gorge/Forge
  revisions. Inspect any warnings, failures and card coverage before treating
  observed wins as useful power estimates.
- Gorge's event log is **not yet translated** into our UI's hand, zone,
  mana-source, or per-turn replay schema. Hash-chain replay verification is
  a prerequisite, not the full adapter.
- 24 games with four decks provide a smoke/stability trial, not a precise
  deck matchup study. A controlled study needs more games, randomized seating,
  opponent-selection balance, pilot calibration and validated card effects.

## Migration gate

Only consider a selectable gorge backend once the following are demonstrated:

1. 100-card Commander import and significant printed-card coverage;
2. four-player games with a reliable completion rate and reproducible seeds;
3. representative Mortarion/Necron/Magnus ability correctness against known
   fixtures, not merely success in reaching game end;
4. documented per-game and batch runtime, including one-time setup cost;
5. a **versioned event-to-observation adapter** that preserves the UI's
   distinguishable event types and reports missing state as unknown;
6. no regressions to existing Python deck analyses or deployment artifacts.

Do not replace our shared-effects catalog or delete the custom kernel before
these gates pass. It remains a useful reference implementation and fallback.
