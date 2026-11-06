# Gorge R2 original Results UI contract (v1)

The original Deck Lab renderer **must not be rewritten to parse Gorge-native events**.
The Cloudflare Worker is the presentation API; analytics endpoints remain
independent and backward compatible.

## Stable public endpoints

- `GET /v1/summary?deck=...`: existing analytics summary; unchanged.
- `GET /v1/games?deck=...`: existing approved game index; unchanged.
- `GET /v1/games/{id}/timeline?deck=...`: existing privacy-preserving event-family segments; unchanged.
- `GET /v1/ui/overview?deck=...`: approved outcomes, matchup groups, histogram and coverage.
- **`GET /v1/ui/batch?deck=...`**: one original `commander-gorge-outcomes-v1` batch for the existing `DeckGameOutcomes.validate/render` entry point.

The new batch response has schema `gorge-r2-original-ui-batch-response-v1`,
`deck`, `population: "approved_current_decisive_only"`, `status`, and
`batch`. When `status: "ready"`, `batch` has the existing renderer's
`format: "commander-gorge-outcomes-v1"` and `schema_version: 1`.
The public UI should **validate** that batch with the existing
`DeckGameOutcomes.validate` and compare its `deck_sha256` to the selected
deck version before displaying anything.

Non-ready statuses: `awaiting_cohort_approval`, `no_warehouse_shards`, or
`projection_pending`. In each case `batch` is null. No older, experimental
or partial cohort is used as a fallback.

## Required R2 source projection

The Worker first verifies exact current-cohort approval via the already used
`isApproved` check on `games.parquet`. For an approved shard it then expects
a **precomputed** adjacent object, at:

```
warehouse/v1/{batch_id}/{deck}/{shard}/ui-original.v1.json
```

Projection envelope:

```json
{
  "schema": "gorge-r2-original-ui-projection-v1",
  "source_batch": "12345678-1",
  "deck": "mortarion_current",
  "shard": 0,
  "games": [
    {
      "game_id": "12345678-1/mortarion_current/0/187000",
      "chain": "native-recording-replay-chain",
      "source_sha256": "64-character-lowercase-hex-source-digest",
      "run": {
        "...": "Public-only fields returned by the established GorgeLegacyAdapter.projectRun"
      }
    }
  ]
}
```

The exporter must use native `gorge-ui-replay-v1` produced by
`tools/gorge_ui_export.py`, then reuse the original
`web/pages/gorge_legacy_adapter.js` `projectRun` logic. It must strip
`source_object_id` and any private crosswalk, hidden hand identities,
unfiltered event payloads, bot intents, native object catalogs, and hidden
libraries. All snapshot boundaries must retain their actual recorded meaning:
the **first pending decision of a turn**, not the end of a turn.

Every projected game must correspond to an approved Parquet row with the exact
`game_id`, `seed`, `chain`, `source_sha256`, player deck hash, winner and
player seat. The Worker rejects extra/duplicate/unapproved games, partial
projections and mixed deck revisions; no fabricated life totals or inferred card
actions are allowed. For multiple approved shards, all required projections
must exist or the endpoint remains `projection_pending`.

The projection **producer and R2 archival upload remain a separate follow-up**.
Adding this endpoint alone intentionally does not approve cohorts, create
source data, or change the existing GitHub Pages rendering. When projections
are created and approved the Worker can serve the original compatible batch
without exposing the native Gorge recording.

## Analytics branch compatibility

No changes to existing endpoint names, query parameters, response schemas,
or approval rules. The Worker only adds a separate v1 route and reads
`seed` and `chain` as private Parquet verification columns. Future
analytic metrics should be added in new fields or versioned analytics routes,
without changing this Results UI batch contract.
