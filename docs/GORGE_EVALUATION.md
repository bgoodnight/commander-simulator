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


## Curated precon opponents and AI pilot options

`python -m tools.fetch_gorge_precons --out /tmp/gorge-decks` downloads four
pinned stock precon lists into the temporary gorge deck pool. Combined with
the existing owned Necron Dynasties and Wretched Ranks fixtures, the
experimental pool contains **six stock precons and two user-built decks**
(Mortarion Current and Magnus Premium). Source provenance and commander
information are recorded in `library_manifest.json`.

The current curated gorge source set includes:

| Key | Commander | Classification |
|---|---|---|
| `avengers-assemble` | Captain America, Team Leader | Stock precon as recorded in upstream sources |
| `cavalry-charge` | Sidar Jabari of Zhalfir | Stock precon |
| `deadly-disguise` | Kaust, Eyes of the Glade | Stock precon |
| `science-pip` | Dr. Madison Li | Stock precon |
| `necron_dynasties` | Szarekh, the Silent King | Existing locally pinned stock precon |
| `wretched_ranks` | Ghoulcaller Gisa | Existing locally pinned stock precon |

Two additional lists (`ulalek-eldrazi` and
`valgavoth-endless-punishment`) are available only through the explicit
`--include-community` option. They are **not** classified as stock:
the first is community-built and the second an upgraded precon. Several
upstream Foundation lists are explicitly *interim approximations* and
are intentionally not included in the stock opponent pool.

The Go probe accepts `-decks` as a comma-separated pool of four or more
loaded keys and rotates them through four seats across seeds. The
`-pilot` flag selects a native gorge AI strategy for every player;
`-hero-pilot` optionally chooses a different native policy for seat 0.
Supported Commander policies at this upstream pin are `bot`,
`forge-heuristic`, `forge-heuristic-hold`, and `lethal-pressure`.
This uses gorge's *actual legal-action-driven AI*, not a transcription
of its heuristics into our Python kernel.

### Native replay contract

With `-native-dir /tmp/results/native -native-limit 2`, the Go driver
writes the **entire gorge event log and player intents** for the first two
games, tagged `gorge-native-trace-v1`. These are source-of-truth
records rather than inferred Python action strings.

`python -m tools.gorge_native_replay --native-dir ... --out ...`
writes a lightweight, versioned `gorge-native-index-v1` segment index.
Its event-kind labels use the pinned gorge enum and unknown kinds retain
their original numeric identifier. Every index contains ranges into the
unchanged raw event sequence. Future UI panels can read these records
natively, rendering only supported fields and leaving unavailable fields
unknown. This avoids inventing hand contents, mana source names or
card actions based on incomplete records.

**Privacy/provenance:** raw match logs contain hands, libraries and other
hidden information. Keep them as restricted per-run artifacts and never
commit them into the public decklab assets. The current workflow uploads
the raw logs as GitHub Actions artifacts for developer testing only.
The UI does *not* automatically publish or load these replay logs yet.

**Simulation results:** the new workflow exercises a 24-game `bot`
baseline across the eight-deck pool and eight additional games using
`forge-heuristic` opponents with a `lethal-pressure` seat-zero pilot.
Its report includes two pilot outputs and the first two native replays.
These runs are still experimental evidence; they do not claim calibrated
deck bracket or competitively optimized bot play.
