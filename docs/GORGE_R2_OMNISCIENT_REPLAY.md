# Omniscient synthetic Gorge Results — contract and release gates

These are **four-bot simulations**. Visibility of game state is not restricted
to public human-player information. The native Gorge warehouse already keeps
the complete ordered event stream (including `secret:true` events) in
`warehouse/v1/{batch}/{deck}/{shard}/events.parquet`, referenced by SHA-256
from each source manifest. The new materialized presentation exposes these
events **without altering the native source** or changing cohort approval.

## Two coordinated views

1. **Original Results-compatible replay:** Rebuild
   `ui-original.v1.json` from the exact retained native recording via
   `tools.gorge_original_ui_shard`. The exporter now calls
   `gorge_ui_export.convert(..., include_hidden=True)` and requires
   `visibility:omniscient` and `synthetic_simulation_only:true`.
   The adapter preserves named hero and opponent hands, ordered libraries,
   boards, graveyards, exiles, command zones, mana pools and life at *recorded*
   turn-entry snapshots. Names are source-backed; no invented snapshots.
   The old original renderer remains authoritative for charts and cards.
2. **Complete native event feed:** The materializer validates the
   SHA-256 of `events.parquet`, exact physical event row offsets,
   game IDs, seeds, replay chains, source event sequence and event kinds.
   It creates immutable, independently hashed chunks of 500 events under
   `results/materialized/v1/versions/{version}/{deck}/events/{sha256(game_id)}/{part}.json`.
   The new Worker endpoint:
   `GET /v1/ui/events?deck={deck}&page={page}&game_id={game_id}&part={part}`
   returns up to 500 **original native event JSON objects**, including
   hidden draws and zone moves. `part` is zero-based; the result contains
   `part_count`, `native_event_count` and the exact cohort `version`.
   Traverse all parts for every event; never assume the first chunk is the
   entire recording. Metadata pages stay at 25 games and fetch no event parts.

Native bot *intents* and internal object crosswalk catalogs remain retained in
the immutable R2 source instead of being embedded in lightweight UI responses;
the requested **complete event stream** includes every native event kind
without public-event filtering. Event object IDs are exact *within one game*.
The adapter removes reusable identity crosswalks from its conventional
renderer envelope.

## Opening-hand semantics

`opening_hand` currently reflects the **first recorded
`first_pending_decision_of_turn` state**, not necessarily the literal seven
cards dealt before the first draw or any mulligans. The adapter labels this
source boundary explicitly in `run.gorge_source.opening_hand_boundary`.
An exact pre-draw hand must be reconstructed and certified using native
opening draws/zone-change events; **do not call it the original seven-card
hand solely because the field is named opening_hand**. Raw native event
chunks are sufficient for an evidence-based follow-up reconstruction when
the original source recorded the required actions.

## Safe rollout

- This PR is **stacked on PR #200**; Work mode's original presentation
  integration is **PR #207**. Reconcile its latest replay component and test
  against this branch before merging.
- Re-run the corrected-pilot source export for Mortarion and Magnus, validate
  the pinned source manifest, deck hashes and each of the 12 exact native
  game IDs, compare old and omniscient game outcomes, and verify that hero
  and all three opponent hand identities are present.
- The legacy reviewed public-only projection stays archived at its original
  immutable R2 key. New experimental omniscient projections use a separate
  `ui/experimental/corrected-pilot/v2/` prefix; the archival workflow is
  manual-only. Promotion to the current warehouse is manual-only and still
  audits the previous source evidence before using a new derived projection.
- Native card-insight evidence is tied to a specific UI projection SHA. Newly
  regenerated omniscient results must use the new immutable
  `card-insights.v2.json` sidecar; the old `v1` evidence is preserved.
  Publish and activate a materialized version only after the appropriate
  complete feature sidecars exist, or show insights as pending.
- The publication workflow downloads and verifies both games and full native
  events tables, then writes all event objects before the immutable version
  manifest and the `current.json` pointer. Rollback verifies every event
  part (including ordering and count) before changing the active pointer.
- Run actual private R2 isolated-prefix publication and rollback rehearsal,
  real-source Worker smoke, then Work mode desktop/mobile visual inspection.
  No R2 objects or Worker deployments are created by this draft PR.

## Invariants

Never silently conflate simulated omniscience with a real-player replay.
Never infer source action/player attribution from the active turn alone.
Never truncate a game to a 25-game page, omit hidden native events, or treat
the first turn-entry hand as definitively pre-draw. Only publish exact,
approved, full-source games with audited version, byte hash, event coverage,
card identity, and all-seat simulation provenance.
