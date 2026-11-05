# Gorge cohort isolation: safety contract (v1)

This change protects current inferential statistics from obsolete simulations. It
does not delete, rewrite, or relocate historical R2 recordings.

## Two independent boundaries

1. **Historical storage/visibility:** raw Gorge recordings and Parquet shards
   remain immutable in their existing R2 location. Existing artifacts remain
   accessible for audits and historical comparisons. A catalog's lifecycle
   value is `archived`, `experimental`, or `current`. Only `current` is
   eligible for primary results.
2. **Statistical eligibility:** `tools/gorge_cohort_report.py` requires
   `--registry data/gorge_analytics_cohort_registry_v1.json`. The report CLI
   routes all source rows through a fail-closed, approved-cohort and exact
   fingerprint match before calculating summary denominators or models.
   Unknown/legacy cohorts are excluded.

A successful Gorge replay is *not* proof that its rules corpus was correct.

## Required current-cohort version identity

All identity fields are required and must agree with an approved cohort:
`engine_commit`, `rules_patch_sha256`, `card_corpus_sha256`,
`player_deck_sha256`, `pilot_version`, `opponent_panel_sha256`,
`oracle_bulk_sha256`, and `simulation_protocol_sha256`.

An approved row also needs `cohort_id`, `cohort_manifest_sha256`,
`source_sha256`, a unique `game_id`, `finished=true`,
`replay_verified=true`, and no error. These fields must be written at
simulation/export time from pinned inputs and trusted native-recording
checks, *not* inferred later from dates or seed ranges. A hash proves
consistency, not correctness of the underlying engine.

## Current migration posture

- Old/unknown Mortarion runs are ineligible, including pre-Astartes-fix
  recordings. The initial registry **deliberately has no approved current
  cohort**.
- The 60-deck precon certification panel is marked experimental. Its 60/60
  import-success result does not certify card mechanics or pilot behavior.
- Do not reclassify older results as current just because they are verified
  or stored in R2.
- We **have not migrated** existing R2 objects. New warehouse exports preserve
  nullable per-game provenance; `tools/gorge_approved_warehouse.py` produces
  separate approved-only Parquet games and events. The Pages builder now filters
  manifest/replay selections, published analytics, and cohort regressions
  through the approved registry. Historical card-insights files are not reused
  when they refer to an excluded cohort.
- Direct, arbitrary R2 SQL queries still bypass these approved-only projections.
  Point production queries at the protected dataset before declaring
  complete end-to-end isolation. Old published Pages builds are not retroactively
  changed by this draft PR.

## Promotion procedure

1. Pin full card/rules/pilot/hero/opponent versions and write an immutable
   cohort manifest before executing any new games.
2. Audit meaningful rules correctness, opponent legality, source traces and
   pilot behavior.
3. Add reviewed registry entry with explicit `approval_ref`, and retain the
   approval in Git history.
4. Ingest source-backed per-game metadata and enforce fingerprint matching
   at the query boundary. All regression tests must pass.
5. Permit **only** approved current cohorts in live summaries; keep
   experimental/historical runs separately retrievable.

The historical data should never be physically deleted solely to implement
this statistical gate.

## R2 preparation for the next approved cohort

The protected R2 writer is `.github/workflows/gorge-r2-approved-projection.yml`.
It is **manual only** and rejects missing approval, invalid batch IDs, bad
source shard digests, and zero approved decisive outcomes. It downloads existing
immutable `warehouse/v1/<run-attempt>/...` shards, validates all per-shard
manifests, writes a separate `warehouse/approved/v1/<registry SHA>/<run-attempt>/`
projection, and uploads `publication.json` **last**. Original R2 objects
are never overwritten or deleted.

For fresh simulated games after the site/UI is ready, create a **new**
version-pinned cohort manifest *before* running any games. Include a true
engine commit, patched rules digest, compiled card corpus hash, hero deck hash,
pilot version, opponent-panel hash, Oracle bulk digest and protocol digest.
Use `tools.gorge_cohort_provenance` on fully verified native recordings to
write `runs-stamped.jsonl` without modifying the source. The warehouse
exporter accepts `--runs-file runs-stamped.jsonl` and independently checks
native-recording SHA-256 when supplied.

Only then, following a separate reviewed signoff, may the registry entry be
changed to `status=current`, `approved=true` with an approval reference.
The approved-only R2 workflow will otherwise **refuse** to publish. The
current registry intentionally has no approved cohorts: no historical results
have been laundered into a new baseline.

The main site is not published by these scripts. Other clients that query
legacy `warehouse/v1` directly can bypass the protection until routed to
the `warehouse/approved/v1` prefix. The new Parquet projection is exclusively
for binary win/loss analytics; draw and turn-cap sources remain in raw R2 or
individual replay diagnostics.

**Deferred work:** Enable new run generation, publish the first reviewed
post-fix cohort, and migrate all production R2 query consumers only after
the UI work is ready. No benchmark reruns or R2 source deletion are part of
this preparation PR.
