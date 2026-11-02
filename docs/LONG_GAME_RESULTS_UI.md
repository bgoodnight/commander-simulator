# Long-game outcomes in Deck Lab

The Results page accepts JSON files from tools/build_game_outcomes.py with format commander-modeled-outcomes-v1. These are **modeled outcomes against abstract opponent stress policies**, never verified multiplayer Commander win rates. The panels remain separate from six-turn goldfish and card-development insights.

## Use before publication

Generate a batch with the script (for example 20 rounds, 20 seeds, 3 example replays) and open Simulation Results > Life, results & opposing tables. Use **Load game JSON** to select one or more output files. Each batch must match the exact selected deck key and SHA. The browser keeps imported JSON only in memory, and does not upload it.

The initial real eight-game sample is in the [November 2 GitHub Actions run](https://github.com/bgoodnight/commander-simulator/actions/runs/41502434821). Download its ZIP and select the four extracted JSON files. Those exploratory observations are too few to characterize deck strength.

To auto-publish later, save batch files under web/pages/data/game-outcomes and create a manifest.json with format commander-modeled-outcomes-library-v1 and a files array of allowlisted basenames, such as mortarion-mixed-20.json. The static exporter validates matching deck revision, experimental fidelity and censoring contract before copying them into the Pages site. It never performs simulations itself.

## Existing fields needed by the UI

Each batch identifies deck_key, deck_sha256, scenario, requested_rounds, opponent_fidelity, outcomes_are_competitive_win_rates (false), runs and optional example_replays. Each run includes seed, completed_rounds, outcome and life_history from round 0 to its terminal or censored round. Every life-history record contains life_totals for seats 0–3, alive_seats, life_changes and new_eliminations. The UI computes life median and interquartile bands across only games observed at each round and keeps unresolved games distinct from losses.

Runs within a deck revision, scenario and horizon can be compared. Repeated imports of the same seed into that group replace the older observation instead of double-counting it.

## Match pilot styles and rules settings

The outcome exporter now records `pilot_style` and `provisional_mode`.
The dashboard keeps each recorded pilot style (adaptive, balanced, engine,
tempo, conservative), approximation setting, deck revision, scenario and
round horizon in its own result cohort. An older batch that lacks a setting
is marked `unrecorded` rather than guessed to be adaptive. Importing the
same seed twice into the *same* cohort replaces the earlier record, but a
matching seed from a different pilot setting remains a separate experiment.

Opponent-group comparisons may span different scenarios at the same
round horizon, but only when deck revision, pilot style and provisional
rules mode agree. "Highest" and "lowest" refer only to the fraction of
**modeled** wins among recorded games; tied fractions are not ranked.
Unresolved games remain in the denominator, and small samples do not
establish actual Commander win probabilities. A style selector in the
static UI only chooses imported data; it does not run a new simulation.

## Future opposing Commander deck support

The UI also accepts an optional opponent_decks array either on the batch or each run, with one object per opposing seat (1, 2, 3). Each object should contain seat, deck_key, commander_name and deck_sha256 for the actual opposing list. When those are present, the dashboard can compare observed outcomes for tables containing those decks instead of abstract scenario roles. Because each result is a four-player result, a deck's presence in a winning or losing pod is only an association, not a head-to-head win rate or proof of impact.

For future source-attributed effects, preserve actor seat, target seat, source object/card ID, event type, damage or life delta and fidelity. Keep unmapped sources unattributed. The current outcome engine measures life-zero elimination only: poison, commander damage, concessions, alternative wins and complete opponent deck/piloting rules need separate coverage.
