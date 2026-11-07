# R2 cross-workstream compatibility review — 2026-11-06

## Source of truth / distinction

- **Immutable native recording** `native/experimental/corrected-pilot/v1/42143344243-1/{hero}.tar.gz`: existing read-only importer `tools/gorge_r2_experiment_ingest.py` is verified against this exact layout, but intentionally NOT generic.
- **Approved warehouse source** `warehouse/v1/<batch>/<hero>/<shard>/{manifest.json,games.parquet,events.parquet,ui-original.v1.json}`: approved corrected baseline was promoted by PR #196. Historical/experimental warehouse objects are distinct and may be archived during promotion.
- **Materialized UI cache (draft PR #200)** `results/materialized/v1/current.json` points at immutable `versions/<hash>/` manifest, summaries, pages and public-safe per-game replay. This is NOT a complete analytical source: excludes private object/intent/hand evidence, is approved+decisive-only, and its full-cohort named-card insights are not built yet. Do not train from UI summaries or 25-row pages.
- **Event player attribution fix (merged PR #201)**: missing actor `player` in native Gorge event means seat 0; do not substitute active turn seat. Historical object `controller_at_end` is NOT the caster. Existing `gorge_event_features.py` counts pod kinds and hero-**owned** card casts; actor-attributed cast/draw/mana/token indicators must not be produced until separately tested.

## Required analytics changes before cohort append

1. **Introduce an immutable full game ID** `<batch>/<hero>/<shard>/<seed>`, plus `cohort_id`, source SHA-256/replay chain, engine/rules/deck/pilot/opponent fingerprints, and feature extractor version. Current analysis prototype uses seed-only keys in `gorge_assemble_model_table.py`, `gorge_event_features.py`, `gorge_landmark_features.py`, `gorge_sparse_card_features.py`, and `gorge_stream_card_features.py`; these are safe only for an exact one-batch/hero audit.
2. **Discover batches and source shards through manifests**, not by scanning or hardcoding a single corrected-pilot key. Retain a reader for legacy verified experimental archives alongside a future generic native-manifest-backed reader. Never silently treat `warehouse/v1` as full omniscient native evidence.
3. **Model population includes all attempts**, keeping failed/stalled/drawn/unverified runs and missing native counts visible; mark inference eligibility separately. Approved UI decisive-only denominators are insufficient for unbiased failure/missingness analysis.
4. **Append is an analytical dataset rebuild**: reconcile source runs by immutable game_id, fail on hash/identity conflicts, union only compatible cohorts, recompute feature coverage and derived aggregate statistics from the complete population, and create new versioned results. Do NOT concatenate aggregate rates or reuse old fitted coefficients.
5. **Pin versions for reproducibility**: compute source-manifest digests, extractor commit/schema and feature dictionary digest. Write immutable Parquet partitions and manifest **last**; record a separate current approved analytics version if needed. No coupling to the mutable UI `current.json`.
6. **Enforce temporal leakage protection** and actor attribution: landmark rows may use only prior event sequence and observed snapshots; derive exact player-turn mapping from verified `turn_change` semantics, not guessed from snapshot turn or active seat. Fix seat-zero omitted-player handling in new actor-level features with off-turn test.
7. **Keep separate API surfaces**: private authenticated analytics manifest/partition retrieval versus approved and sanitized UI routes `/v1/ui/catalog`, `/v1/ui/page`, `/v1/ui/game`. PR #200 is not yet merged/deployed and is not a valid analytics endpoint.

## Immediate compatibility status

- Existing source-backed 12+12 experimental extraction and field coverage audit remain valid as **single-batch schema checks**.
- Original cohort is now user-approved as best-available current baseline, but 12 games per commander remain too small for calibrated inference.
- PR #200 is draft. It does not require modifying or migrating raw native keys. PR #201 is merged; new actor-level analytics must honor it.
- **Do not merge arbitrary pilot changes into PR #163**. Keep this document as a coordination record; apply game-id/schema changes together with tests on a dedicated analysis follow-on PR once the new analytical storage manifest contract is finalized.
