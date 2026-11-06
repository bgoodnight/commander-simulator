# Gorge native feature inventory and Worker handoff — draft v0.1

**Status:** Initial source-backed inventory, experimental only. Source audit job: [42150520392](https://github.com/bgoodnight/commander-simulator/actions/runs/42150520392). Do not confuse source field availability with validated semantic interpretation or modeling eligibility.

## Current verified source components

- Private immutable corrected-pilot archive keys: `native/experimental/corrected-pilot/v1/42143344243-1/mortarion_current.tar.gz` and `magnus_premium.tar.gz`.
- Each has twelve matched runs/native recordings and source manifest, trace event and intent log, end-of-game object crosswalk, first-pending-decision turn-entry snapshots and replay chain.
- Existing extractors: `gorge_landmark_features.py`, `gorge_event_features.py`, `gorge_sparse_card_features.py`. The new `gorge_native_schema_audit.py` inventories record types, event kinds and field presence without publishing private values.

## Feature requirement matrix

| Feature family | Grain | Source inputs | Current readiness | Proposed Worker interface |
|---|---|---|---|---|
| Cohort identity and provenance | cohort | source/qualification manifests, engine and card hashes | verified | private manifest and feature-version metadata |
| Outcomes and termination | game/attempt | runs.jsonl: finished, replay_verified, draw, winner, stall/error | verified | private attempts and game Parquet |
| Opponent context | game/seat | four deck IDs and hero seat | verified IDs; metadata needs pinned precon registry | private opponent context table |
| Opening/landmark state | game/global-turn | player life, zones, object IDs, first-pending-decision boundary | basic counts extracted; total mana not validated | private landmark table and evidence sequence |
| Card-in-deck indicator | game/card | pinned hero decklist, deck hash | needs card-roster integration | card roster/version table; not event-derived |
| Draw and first-draw time | game/card | draw and zone-transition events, actor and turn boundaries | semantic audit needed | private event projection with IDs + controller/actor + time |
| Cast count and first-cast time | game/card | cast events and object crosswalk | cast owner evidence extracted; caster/turn needs audit | private per-card event/turn records |
| Never cast and hand dwell | game/card | roster, draw, full zone history, game censoring | incomplete until transition audit | private card lifecycle table |
| Mana resource development | turn/cast | pool, mana change, payment, sources, discounts | pool snapshot available; semantic audit needed | private mana/cost event projection |
| Token/trigger/sacrifice engines | card/event | token created, trigger, sacrifice reason, source object/controller | event family counts only | private source-attributed mechanism table |
| Board/interaction pressure | game/turn | life, damage, death/exile, targeting | partial; actor and target must be checked | private event/snapshot-derived table |
| Decision opportunities and missed actions | decision | Gorge intents, legal alternatives, board state | raw intents present; semantics/alternatives unverified | private decision/choice records only if actually captured |
| At-risk landmarks | game/turn | player_lost, game_over, timestamps | not validated | terminal-state eligibility/censoring table |

## Modeling requirements

- Keep `game/cohort/attempt/hero/seed` identities and all source hashes; seed alone cannot identify a game across batches.
- Separate **included in deck**, **drawn**, **observed in hand**, **cast**, and **performed by hero**. Object ownership is not the casting actor. Track zero, not observed, and missing data distinctly.
- Card features must use source events **at or before** prediction cutoff. First sampled snapshot turn is not exact draw or cast turn. For postgame descriptive features use a separate outcome-table namespace, not pre-outcome predictors.
- Game-state repeated landmarks are NOT independent observations; group by run/seed and opponent pod when validating. Do not select on completed games only without a missingness/censoring audit.
- Model with a broad feature dictionary; evaluate against opponent-only baseline with seed-grouped nested cross-validation (or OOB where supported). Confirm promising card/pilot findings in independent matched-seed A/B simulations.
- The public UI Worker stays approval-gated; private analytic data requires authentication and partitioned bulk retrieval. Source fidelity inspection can proceed directly from R2 without waiting for a Worker endpoint.

## Next decisions based on field-coverage audit

1. Map the actual native event kinds and intents to stable semantic names and required actor/source/target fields; test seat-zero omissions explicitly.
2. Audit exact draw/cast/zone-transition/player-turn mapping on hand-reviewed games. Flag unsupported measures instead of inferring them.
3. Add a pinned card-roster join and card lifecycle view (drawn/not drawn, played/held/censored) with independent evidence checks.
4. Materialize partitioned feature files with a versioned data dictionary and hashes; request the Worker expose only the necessary authorized datasets.
