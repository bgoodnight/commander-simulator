# Deck Intelligence: automated and curated strategic tracking

Status: pure read-only reporting layer, not a game engine, auto-combo detector, or source of game events.

## Two complementary sources

1. Automatic printed features: `printed_features(catalog, quantities, profile)` counts verified Scryfall keywords, types and subtypes. Printed attributes describe cards; they do not establish rules support, synergy effectiveness or executable abilities.
2. Curated deck-specific profiles: optional `key_cards` (id/card/role), `groups` (id/cards), and `combos` (id/pieces). Cards must resolve to verified exact names in the supplied pinned catalog. Store profiles by deck version; do not change immutable canonical decklists.

Example illustrative profile (names below are placeholders, **not** a claim about a Magnus combo):

```json
{"key_cards":[{"id":"engine","card":"Engine","role":"engine"}],"groups":[{"id":"wizards","cards":["Wizard A","Wizard B"]}],"combos":[{"id":"sample_pair","pieces":["Wizard A","Engine"]}]}
```

## Live turn-state adapter contract

`analyze_game_turns(catalog, profile, states)` accepts only trusted engine-projected states with `source=authoritative_game`, monotonically increasing `turn`, and verified names in `battlefield`, `hand`, `graveyard`. It never simulates game objects. The M3 adapter must project these fields from authoritative kernel zones and controller-specific objects, not maintain an independent battlefield.

An optional `verified_tutor_access` record includes `tutor`, `target`, `destination` (`hand` or `battlefield`) and `verified:true` **only when the engine has proven the tutor can be used, the target is searchable in the appropriate zone, and all relevant restrictions, costs and timing permit the access**. Merely owning a tutor or drawing it does not prove access.

A curated combo can report piece count on the battlefield and available in hand or via verified tutoring. Even if every piece is present, it is `all_pieces_present_unverified`, not operational. Only `engine_verified_combos` from the rules layer may declare `engine_verified_operational`; that still does not establish a win until a supported win condition actually resolves.

## Planned visualization tiers

- Universal: mana sources, lands played, effective ramp, card draw, board presence, type/subtype/printed-keyword categories and first unsupported decision.
- Strategy: per-turn counts from curated mechanic groups, first key-card draw, verified tutor access, on-battlefield turn and combo piece accessibility.
- Comparisons: percentage reaching milestones by turns 3/5/7/10 and paired-seed differences, with uncertainty intervals and coverage labels. Runs blocked by omitted rules should be censored rather than counted as losses.

## Boundaries and next steps

The new module is a reporting contract, not a production M3 adapter, persistent profile store, profile UI, or complete statistics pipeline. First integrate the actual multi-deck turn driver; then emit ID-backed snapshots and verified search/cost events, run milestone aggregations, and add Deck Lab U3 charts. Printed keywords may propose descriptive groups for user review, but never auto-classify card text as game mechanics or combos.

## Implemented backend bridge (M3 reporting groundwork)

- `commander_sim.kernel_reporting.project_kernel_turn(zones, seat, turn, catalog, ...)` reads the existing IndexedKernel/LiveZones physical object IDs. Battlefield is scoped to *controller*, private hand and graveyard to *owner*. All recognized names require pinned metadata; unknown tokens are reported separately, not assigned invented keywords. The caller must invoke this at a real rules-engine turn boundary.
- `commander_sim.board_features.analyze_authoritative_run(catalog, profile, states)` produces one JSON-friendly object with `automatic` (verified printed keywords/types/subtypes in play each turn) and `strategy` (curated key/group/combo states). It rejects observation-only inputs.
- `commander_sim.milestone_stats.summarize_strategy_runs(runs, checkpoints=(3,5,7,10))` accepts independent seeded, single-deck, authoritative strategy analysis objects. It reports per-checkpoint sample sizes, censored runs, average on-board group counts, milestone rates, and Wilson 95% seed-sampling intervals. A run missing a checkpoint is **censored**, not silently scored as failing or losing.

Expected processing sequence after the M3 turn driver exists:

```python
# The game driver owns the kernel, turn, legal actions, and verified events.
state = project_kernel_turn(zones, seat, turn, pinned_catalog)
report = analyze_authoritative_run(pinned_catalog, curated_profile, [state])
# Batch independently seeded reports, then summarize the strategy branch.
batch = summarize_strategy_runs([
    {'seed': seed, 'deck_sha256': deck_sha, 'report': game_report['strategy']}
    for seed, deck_sha, game_report in completed_or_censored_runs
])
```

Do **not** populate `verified_tutor_access` until the actual rules layer has verified search eligibility, targets, costs, timing, and zone destination. Do **not** populate `engine_verified_combos` from a metadata match or a suggested synergy.

**Still pending:** production M3 six-turn driver and independent deck loader, live decision/event verification, real tutor reachability, mechanic-specific ability coverage, cross-game opponent calibration, and UI integration. The tools above analyze **supplied game states**, but do not themselves generate games or validate win rates. Coordinate UI changes on its separate Work branch; these backend modules are independent of HTML/JS.

## Bounded M3 real-action demonstration (October 31, 2026)

A new **backend-only** implementation uses authentic, pinned 100-card lists
directly in the existing physical-object `IndexedKernel`/`LiveZones`:

```sh
python -m commander_sim.early_game_runner --deck wretched_ranks --seed 7 --turns 6
python -m commander_sim.early_game_runner --deck magnus_premium --seed 7 --turns 6
python -m commander_sim.bounded_batch --deck wretched_ranks --seeds 20 --turns 6
python -m commander_sim.bounded_batch --deck magnus_premium --seeds 20 --turns 6
```

`run_bounded_early_game` validates its pinned manifest/snapshot offline,
instantiates all 100 physical cards in the authoritative library/command
zones, shuffles and draws seven (optional one-free mulligan), draws each turn,
plays one reviewed basic land/Command Tower, untaps physical land objects,
and source-pays/casts/resolves a **small manually approved subset of ordinary
creatures**. Each approved identity is pinned to an inspected Oracle ID and
exact rules text in `commander_sim/reviewed_early_cards.py`; changing its
text invalidates approval. No other card gains executable behavior from
metadata. The runner calls `project_kernel_turn` to provide an immutable
per-turn report, real cast/source IDs, and `analyze_authoritative_run`
for descriptive board trends.

`run_bounded_batch` repeats independent seeds and reports mean physical
lands and **reviewed** creatures in play, hand size, unsupported hand cards,
the fraction with a reviewed creature cast by turn N, and 95% seed-sampling
intervals. These are deliberately **bounded real-action metrics**, not
hypothetical mana-cost observations and **not a measure of full deck strength**.

**Limits:** No modeled opponents, combat, commander casting, mana rocks,
nonbasic land effects beyond Command Tower, instants/sorceries, full triggered
or activated abilities, response priority, exhaustive color/cost restrictions,
tutoring, search chains, combo execution, or win conditions. The creature
casting whitelist is safe only for the runner's constrained scenario and
does **not** grant exact printed-card fidelity elsewhere. Unsupported cards
stay physically in hand/library/other zones. Bounded runs must never be
reported as actual Commander wins or as an estimate of full-deck win rate.

This harness is an integration step toward M3, **not** a replacement for
the existing v35 live multiplayer turn driver. The next highest-value
engineering work is to connect general deck loading and actual source-paid
actions to that driver, then expand reviewed shared mana rocks, effect
handlers, tutor predicates, and legal opposing responses. Keep the UI in
Work mode on a separate branch; the backend module interface can be
consumed later, but should not be represented as a complete game API.

## Optional strategy profiles in bounded runs

Profiles are JSON definitions stored apart from canonical decklists. Use
`--profile` to track exact verified key-card names and named group membership
in real kernel snapshots, and to aggregate per-seed access milestones:

```sh
python -m commander_sim.early_game_runner --deck wretched_ranks --seed 7 --turns 6 --profile docs/examples/wretched_ranks_early_profile.json
python -m commander_sim.bounded_batch --deck wretched_ranks --seeds 20 --turns 6 --profile docs/examples/wretched_ranks_early_profile.json
python -m commander_sim.bounded_batch --deck magnus_premium --seeds 20 --turns 6 --profile docs/examples/magnus_early_profile.json
```

These example profiles are optional strategic **labels**, not user-endorsed
optimal plans or fully supported card abilities. Their combo lists are empty
because no combo execution is verified in the bounded land/creature runner.
The metrics distinguish ever-in-hand, on-board, and verified tutor access
(which remains unavailable here). Full tutoring and operational combo
rates must be driven by reviewed executable rules after the general turn
engine supports them. The separate UI workstream can consume
`deck_intelligence.strategy` and `curated_milestones` once it has a
real-run import or API; browser-only observation results must not be
rebranded as these gameplay metrics.
