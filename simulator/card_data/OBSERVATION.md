# Flameslinger v0.7: initial observation projection

This initial projection is deliberately narrower than the P0.6 exit gate. It uses the authoritative deck file and the matching, hash-checked Scryfall snapshot. It **is not a game played by the simulator**: it keeps the opening seven without evaluating a mulligan, draws once each turn for a non-starting player, and plays only an Island or Mountain from hand. It does not model nonbasic lands, card effects, color payment, timing, targets, combat, or opponent actions. All candidate spells are a mana-value-only screen, not legal plays. A supplied threat is a scripted scenario, and no counter or other response resolves.

Reproduce the no-threat version:

```sh
python -m commander_sim.observation decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt simulator/card_data/flameslinger_v0_7_scryfall.json --seed 0 --turns 6 --reserve 1
```

The checked-in [`v0_7_observation_seed0.json`](v0_7_observation_seed0.json) additionally includes a scripted opposing noncreature spell on turn three. In that run the kept opening seven contains no basic lands; Mountains are drawn and modeled as played on turns one and two. A hypothetical one-source reserve is applied each turn. The turn-five Exotic Orchard remains in hand because nonbasic lands are not modeled. These details illustrate the projection's limitations; they do not demonstrate a sensible mulligan, an actual mana screw, or deck strength.

[`v0_7_observation_performance.json`](v0_7_observation_performance.json) records 20 local seed runs, including snapshot validation. On that host p50 was 1.758 ms and p95 was 2.781 ms. These are not engine-game timings and are not comparable to the eight-round live-engine baseline.

Next: verified shared characteristics and targets in the live engine, a reviewed nonbasic source model and mulligan policy, real supported actions with explicit costs/legality, and fidelity/dependence logging before hybrid gameplay.
