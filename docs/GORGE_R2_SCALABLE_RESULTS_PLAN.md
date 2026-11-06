# R2 scalable Results delivery — implementation staging (2026-11-06)

## Decision

Keep the current original Results renderer and approval gates. Separate **full-cohort statistics** from **individual game playback**. R2 retains immutable native Gorge recordings and approved, public-safe UI projections. A versioned cohort manifest is the only source of truth for which shards belong to current statistics.

## Phase 1: approved game-index pagination (this PR)

`GET /v1/games?deck=<deck>&limit=25` returns up to 25 approved game metadata rows, with `total`, `has_more`, and `next_cursor`. Pass `cursor=<next_cursor>` for the next page. The default is 25; smaller limits remain valid. The cursor is the last approved game ID sorted lexicographically, not an R2 path. A nonmatching cursor is rejected. Existing `/v1/summary`, `/v1/ui/overview`, `/v1/ui/batch` and game details are unchanged in this PR.

**Limitation:** The index still scans up to the existing 40-shard ceiling and reads approved Parquet rows for each request. The cursor does **not** solve scalability beyond that ceiling, so it must be replaced with an indexed, version-pinned game catalog before large-cohort release. Clients should discard cursors when a newly published cohort version appears.

## Phase 2: complete, versioned cohort summary

- Ingestion archives new shards immutably; require exact engine/rules/deck/pilot/opponent cohort fingerprint compatibility and source SHA verification. Never combine historical or unapproved games.
- Rebuild the summary from **all eligible batches**, not the last 25 games. Recompute denominators, win/loss, matchup distributions, turns, histograms, full-cohort card insights and coverage. Refit predictive models separately only when their validation contract and sample-size gates pass; never carry old model coefficients into a newly expanded population.
- Write versioned summary and game-index objects into a staging prefix with cohort fingerprint, approved game IDs, exact source object digests, schema/producer versions, counts and checksum. Verify totals against the full approved index; ensure every projection and summary uses the same deck hash.
- Publish the manifest **last**. Atomically switch a small `current` pointer only after verification. Do not remove the previous complete version until rollback retention expires. An interrupted refresh leaves the old version live; never mix partially built versions.
- Worker serves a consistent version of the precomputed summary, avoiding a full Parquet scan per UI request. Invalidation/refresh begins only after source append and explicit eligibility/certification, not simply whenever an R2 object appears.

## Phase 3: lazy replay

- Keep overview and insight charts bound to the **complete cohort**. Do not calculate them from a 25-row page.
- Add an **approved UI game index** (25 rows/page) with per-game display metadata and stable IDs; provide a separately version-pinned `GET /v1/ui/games/{id}` for one public-safe original-renderer `run` projection. No omniscient native event data reaches the browser.
- Results UI initially fetches summary + first page; fetch another page only on the explicit more/scroll action; fetch replay only on selection. Cache pages/details keyed by `cohort_version, deck_hash, game_id`. Cancel/discard stale responses on deck or cohort changes.
- Preserve `DeckGameOutcomes.validate` contract by wrapping the single selected run in the expected compatible batch, or create a separately tested lightweight renderer entry point. Never silently fall back to older/experimental cohorts.
- Retire the current `/v1/ui/batch` 200-game hard-stop only after the lazy replay path is verified on desktop and mobile; do not merely increase its limit.

## Required release checks

Test 0, 1, 25, 26, 200, 201 and 500+ games, duplicate IDs, invalid cursor, approval change during pagination, missing projection, source hash mismatch, incomplete append, interrupted build, mixed deck fingerprints, insight denominator consistency and repeatability of a pinned version. Compare full summaries against independently computed source-backed totals and replay event attribution. The initial pagination PR alone **is not** a deploy-ready solution for larger batches.
