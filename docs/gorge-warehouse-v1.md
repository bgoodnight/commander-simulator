# Gorge Warehouse v1 (private analytics layer)

**Status:** implementation on a feature branch; not yet deployed or validated
against a complete Gorge batch. R2 upload/readback credentials were verified
independently in the connection smoke test.

## Storage layout

The existing private bucket `gorge-simulations` holds:

- `native/v1/<player>/<shard>/<run-id>-<attempt>.tar.gz`: full original Gorge
  traces, outcomes and per-shard derived card insights.
- `warehouse/v1/<run-id>-<attempt>/<player>/<shard>/games.parquet`: one row
  for every verified game, including game ID, chain, outcomes, player seat,
  source SHA-256 and immutable opponent/deck metadata.
- `warehouse/v1/<run-id>-<attempt>/<player>/<shard>/events.parquet`: one row
  per native event, with original kind, sequence, game ID and the complete
  original event object serialized in `event_json`.
- `warehouse/v1/<run-id>-<attempt>/<player>/<shard>/manifest.json`: schema
  version, source population counts and SHA-256 of each Parquet object.

The stored native traces remain authoritative. An event's `event_json`
contains **exact source evidence**, not inferred card names, snapshots, or
actions. We deliberately do not publish these private omniscient events on
GitHub Pages.

## Example local DuckDB queries

After downloading one or more authorized Parquet shard files:

```sql
SELECT deck, count(*) AS games,
       avg(CASE WHEN winner_seat=hero_seat AND NOT draw
                THEN 1.0 ELSE 0.0 END) AS win_rate
FROM read_parquet('warehouse/**/games.parquet', union_by_name=true)
GROUP BY deck;
```

```sql
SELECT kind_id, count(*) AS occurrences,
       count(DISTINCT game_id) AS games_with_event
FROM read_parquet('warehouse/**/events.parquet', union_by_name=true)
GROUP BY kind_id ORDER BY occurrences DESC;
```

These are local or scheduled analytical queries, **not browser queries**.
Win-rate comparisons must use properly scoped cohorts, account for draws,
validate deck/pilot/engine version comparability and report denominator.
Repeated observations from a single game are not independent.

## Current limitations and next steps

1. The present exporter holds shard event rows in memory; benchmark on a
   representative shard and migrate to streaming Parquet writes if large.
2. The entire R2 archive is private. The UI has **not yet been switched**
   to query an API, and there is no live D1 database or Worker endpoint.
3. Build a versioned catalog and materialize commonly requested statistics
   and reliable confidence intervals/adjusted model outputs separately.
4. Add a read-only, constrained API that returns aggregates or selected
   authorized synthetic game details rather than scanning raw R2 objects on
   each request.
5. Backfill older verified results only if authoritative native recordings
   survive in artifacts or archives; do not fabricate missing events.
6. Establish upload idempotence, bucket lifecycle rules and retention metrics
   before scaling batch counts.

Tests: `python -m unittest tests.test_gorge_warehouse_export -v`.
The large benchmark remains manually triggered; it is not invoked by a
commit or by the storage smoke test.
