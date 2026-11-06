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

## Empirical native field inventory — 24 R2 games

[Source-audit run 42150745799](https://github.com/bgoodnight/commander-simulator/actions/runs/42150745799) finished successfully for both heroes. The keys listed below were **observed in the native records**; presence does not establish completeness or semantic correctness.

| Family | Top-level observed fields |
|---|---|
| Event | `amount`, `counter`, `from`, `ids`, `kind`, `obj`, `pairs`, `player`, `secret`, `seq`, `step`, `text`, `to` |
| Intent | `choices`, `payment`, `player`, `seq` |
| Object | `card_name`, `controller_at_end`, `effective_name`, `is_copy`, `is_token`, `object_id`, `owner`, `types_at_end` |
| Snapshot | `active_seat`, `after_event_seq`, `boundary`, `players`, `step`, `turn` |

Record totals: Mortarion **122,040 events**, **23,239 intents**, **6,055 objects**, **460 snapshots**; Magnus **136,472 events**, **25,656 intents**, **6,480 objects**, **502 snapshots**. There were **60 distinct numeric event kinds** in Mortarion and **64** in Magnus. Both source archives have **12/12 native recordings**.

**Interpretation priority:** there is significantly richer evidence in events and intents than the current feature extractor consumes. Before feature generation, perform source-backed actor/owner/controller disambiguation for `player` (including omitted seat zero), resolve `choices` and `payment` semantics, and map additional numerical event kinds to documented Gorge engine definitions. `controller_at_end` is not a historical controller field; end-state information must not leak into landmark predictors. For true hand dwell or cost-reduction attribution, confirm that the raw event / intent timeline provides enough information rather than claiming such metrics are already available.

**Worker handoff:** request versioned private source-backed event, intent, object crosswalk and turn/snapshot datasets (or a manifest for corresponding immutable Parquet partitions). The generic public UI batch must remain sanitized. Do not request dedicated fields for every engineered indicator until after this semantic audit; `kind`/`seq`/`obj`/`player`/`from`/`to` and contextual card, turn, choice and payment data form the minimum raw material, subject to privacy and field verification.
