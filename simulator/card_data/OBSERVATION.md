# Flameslinger v0.7: initial observation projection

This initial projection is deliberately narrower than the P0.6 exit gate. It uses the authoritative deck file and the matching, hash-checked Scryfall snapshot. It **is not a game played by the simulator**: it keeps the opening seven without evaluating a mulligan, draws once each turn for a non-starting player, and plays only a basic land or Command Tower from hand. It does not model other nonbasic lands, card effects, color payment, timing, targets, combat, or opponent actions. All candidate spells are a mana-value-only screen, not legal plays. A supplied threat is a scripted scenario, and no counter or other response resolves.

Reproduce the no-threat version:

```sh
python -m commander_sim.observation decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt simulator/card_data/flameslinger_v0_7_scryfall.json --seed 0 --turns 6 --reserve 1
```

The checked-in [`v0_7_observation_seed0.json`](v0_7_observation_seed0.json) additionally includes a scripted opposing noncreature spell on turn three. In that run the kept opening seven contains no basic lands; Mountains are drawn and modeled as played on turns one and two. A hypothetical one-source reserve is applied each turn. The turn-five Exotic Orchard remains in hand because nonbasic lands are not modeled. These details illustrate the projection's limitations; they do not demonstrate a sensible mulligan, an actual mana screw, or deck strength.

[`v0_7_observation_performance.json`](v0_7_observation_performance.json) records 20 local seed runs, including snapshot validation. On that host p50 was 1.583 ms and p95 was 1.937 ms. These are not engine-game timings and are not comparable to the eight-round live-engine baseline.

Next: verified shared characteristics and targets in the live engine, additional reviewed nonbasic source models and mulligan decisions, real supported actions with explicit costs/legality, and fidelity/dependence logging before hybrid gameplay.

## Mono-black fixture observations

Offline snapshots also validate the 100-card [Gisa precon](../../decklists/wretched_ranks_foundations_precon_2026.txt) and the 100-card [Mortarion purchase-reconciled candidate](../../decklists/mortarion_purchase_reconciled_candidate_2026_10_27.txt). The latter is an evidence-based candidate, not a confirmed physical deck. Seed-zero projections are recorded in [Gisa's trace](gisa_observation_seed0.json) and [Mortarion's trace](mortarion_observation_seed0.json). The projection counts basic Swamps but does not execute black mana payments, cast spells, simulate a full turn, or infer win rates. The current live simulator still rejects these commanders.

## Optional first multiplayer mulligan

Pass `--mulligan one-free` to enable a simple one-redraw policy. It takes the first free multiplayer mulligan if every possible verified land count in the initial seven is outside 2–5, then keeps the replacement seven. Unknown card faces are counted as uncertain; if they could change the decision, the policy keeps and reports uncertainty. The policy does not evaluate colors, curve or card quality, and takes no second mulligan. The first multiplayer mulligan is free under the [official rules description](https://magic.wizards.com/en/news/feature/core-set-2020-release-notes-2019-06-25).

The [seed-zero one-free example](v0_7_observation_one_free_seed0.json) redraws its original landless hand and keeps seven, including three Mountains. It is one illustrative projection, not a deck-quality assessment. Command Tower is now modeled as an untapped source with colors in the commander's identity; other nonbasic land abilities remain unmodeled. No mana is actually spent.

The newer [Mortarion current ordered-plus-owned](../../decklists/mortarion_current_ordered_plus_owned_2026_10_31.txt) and [ideal](../../decklists/mortarion_inexorable_plague_host_ideal.txt) lists have matching identity snapshots and separate [current](mortarion_current_observation_seed0.json) and [ideal](mortarion_ideal_observation_seed0.json) observations. The current list remains provisional and ordered cards are not confirmed delivered; the ideal list is aspirational.
