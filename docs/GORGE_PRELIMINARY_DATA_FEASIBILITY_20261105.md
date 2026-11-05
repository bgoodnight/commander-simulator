# Preliminary Gorge data feasibility — 2026-11-05

## Scope
Exploratory inspection of **three accessible newly published Gorge UI replays** (seeds 620, 621, 622) from `web/pages/data/gorge/`, plus the **separate, historical** `web/pages/data/analytics/mortarion_physical_final.json` elastic-net report. **Not** a read of private R2. The 24-game postmerge experimental batch is retained in Actions artifacts but was not parsed here. No current cohort inference is justified.

## Replays examined

| Seed | Hero | Seat | Winner from explicit game_over | Global turns in manifest | Native events reported | UI exported events | Turn-entry snapshots |
|---|---|---:|---|---:|---:|---:|---:|
| 620 | mortarion_current | 0 | mortarion_current | 26 | 7,683 | 1,594 | 26 |
| 621 | mortarion_current | 1 | cavalry-charge | 31 | 8,216 | 1,810 | 31 |
| 622 | magnus_premium | 0 | cavalry-charge | 32 | 7,522 | 1,601 | 32 |
| **Total** | | | | | **23,421** | **5,005** | **89** |

- Game outcome is read from explicit `game_over` events, not inferred from a final snapshot.
- The first player in seed 620 initially held three Swamps, K'rrik, Skullclamp, Bastion of Remembrance, and Sol Ring. Seed 621 had two Swamps, Pristine Talisman, Pestilence Demon, Shambling Ghast, Viscera Seer, and Arcane Signet. Seed 622 had Island twice, Baral, Goblin Electromancer, Shivan Reef, Consider, and Riptide Laboratory.
- Available fields: `turns[].events` with sequence and kind IDs; `object_identity` mapping; `snapshots[].players[].zones` with named cards at **turn entry**; player life, hand count, mana pools, deck and hero-seat metadata.
- The UI replays omit much native activity (5,005 events exported of 23,421 reported). Do not presume that UI events are a complete gameplay activity ledger. Native source is authoritative.
- In exported events, seat 0 may be represented by omitted `player` rather than integer zero. Never use `event.player === 0` as a complete ownership rule without crosswalking through the native event contract.
- Recordings are synthetic simulation observations, not evidence of causal effects or real-world Commander win rates.

## Independent historical elastic-net artifact (do NOT mix into Gorge sample)
`web/pages/data/analytics/mortarion_physical_final.json` reports 500 observations across 100 independent seeds, 418 wins and 82 nonwins, 13 selected predictors, holdout Brier 0.12735, and opponent-composition baseline Brier 0.12817, using grouped seeds. This pertains to a different engine commit and deck and is **not** a current Gorge result. The narrow Brier improvement is not evidence that this model generalizes to the new rules cohort.

## Next read-only analysis
1. Access the approved/current R2 warehouse `games.parquet` and `events.parquet`, and verify corresponding native tarballs and hashes.
2. Count decisive, drawn, stalled, errored and unverified records by exact cohort/deck/pilot fingerprints; do not promote historical runs.
3. Build source-backed per-hero, per-game feature rows. For each feature, record evidence event IDs, owner/crosswalk basis and effective observation time.
4. Construct opening-hand and time-landmark predictors only when complete native source events/zone states suffice; leave unobserved variables as missing, never zero.
5. Fit grouped elastic net only with adequate independent seeds, outcome balance, and approved eligibility. Report insufficient-data when not adequate.
