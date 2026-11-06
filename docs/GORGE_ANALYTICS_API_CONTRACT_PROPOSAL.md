# Gorge analytics API contract proposal (v0.1)

Status: proposed coordination contract for the Worker and analysis branches. NOT an implemented Worker route, NOT production approval. Analytic source remains private.

## Separate data planes

1. **Public/UI**: approved-current cohort only; no raw event JSON, object IDs, hidden zones, source seeds, or privileged decision history. Existing Worker endpoints stay unchanged and are not overloaded for offline analysis.
2. **Private analytics**: authenticated service-to-service requests for versioned, provenance-checked derived datasets. Never make private raw-snapshot artifacts accessible via public CORS or unauthenticated signed URLs. Native recordings remain authoritative in R2.
3. **Batch extraction**: execute high-dimensional feature engineering in a trusted GitHub Actions runner or other batch compute, reading full native recordings and writing immutable, partitioned Parquet to private R2. The Worker lists, authorizes, validates manifests and serves bounded views or authorized object downloads. Heavy extraction is NOT performed on every HTTP request.

## Minimal first-class analytics objects

- `cohort_manifest`: immutable run/cohort IDs, SHA-256, full eight-field identity fingerprints, attempted/finished/verified counts, status {experimental,archived,current}, approval reference, source native/warehouse keys, counts per hero.
- `feature_dictionary`: feature ID/name, version, family, grain, dtype, units, observations/censoring semantics, source kinds, cutoff, evidence provenance, zero/null policy, extraction version.
- `datasets`: `attempts` (all attempts incl. errors/turn caps), `game_features` (one per hero game), `landmark_features` (game/hero/cutoff), `card_exposures` (sparse game/hero/landmark/card), `opponent_context`, `event_evidence` (private only), `model_run_metadata`.
- `partition_manifest`: path, dataset schema version, cohort, hero, feature extraction commit/digest, rows, byte size, SHA-256, source population counts, complete flag. Publish completion marker LAST.
- Card dictionary joins use **pinned decklist / Oracle version**. Card `in_deck` and `drawn` differ from `observed` and `cast`; absent positive sparse rows are unobserved, not automatically zero. Timing uses exact native event seq until per-player turn mapping audited. Never infer caster from card owner or end-state controller.

## Suggested authenticated API (private /v1/analytics)

- `GET /v1/analytics/cohorts?hero=<key>&status=<status>`: compact source-backed cohort catalog with approval/version flags.
- `GET /v1/analytics/cohorts/<cohort_id>/manifest`: immutable population and fingerprint metadata.
- `GET /v1/analytics/features/dictionary?version=<feature_schema>`: machine-readable, versioned feature definitions.
- `GET /v1/analytics/datasets?cohort=<id>&hero=<key>`: immutable partition manifest + counts, schema IDs, data completeness and available landmarks.
- `GET /v1/analytics/datasets/<dataset_id>/partitions?cursor=...`: page partition metadata and private access handles.
- `GET /v1/analytics/datasets/<dataset_id>/partitions/<partition_id>`: bounded authenticated Parquet bytes or a short-lived, narrowly scoped access route if a trusted backend is available; no unconstrained full-bucket listing.
- `GET /v1/analytics/quality?cohort=<id>&hero=<key>`: source/native/feature completeness, eligibility and missingness, unresolved attribution, censoring counts.

**NOT recommended:** `GET /analytics/extract-all` that decompresses an arbitrary native archive and engineers millions of features inside one Worker request; public raw recording endpoints; URL user-controlled R2 key prefixes; exposing internal R2 credentials; silently combining experimental and approved cohorts.

## Authorization / integrity

- Distinct credentials and scopes from public UI and short-lived diagnostic Worker tokens: e.g. `analytics:catalog`, `analytics:features`, and `analytics:private-evidence`. Consider Cloudflare Access service tokens or equivalent trusted service credentials, rotate/revoke and rate-limit.
- Enforce normalized path keys, strict cohort+hero+dataset allowlists, pagination, response byte caps, and signed manifest/source digests. Refuse partial/uncommitted partitions.
- Public API is **approved-only**. Private analytics API may explicitly request `experimental`, but returns status and `production_eligible=false` until reviewed registry approval; no contamination of current UI.
- Derivative private data may include hidden hand/library details or decision alternatives. Do not publish source payloads in GitHub Pages, public CI artifacts, or public access logs.
- Never infer zero from absent recording; preserve attempted-game denominator and failed/turn-cap observations.
- Stable row identity: cohort_id / run_id / attempt / hero / seed, not seed alone. Scope object IDs to a single game. Avoid leakage of post-landmark data.

## Performance and modeling

- Co-locate bulk Parquet storage and scheduled materialization in R2; prefer predicate pushdown, partition pruning, compressed columnar data and bulk reads.
- Do not request every event for every experiment via thousands of tiny Worker API calls. Training jobs can fetch **immutable partition files** after an authenticated manifest query, or use trusted direct R2 Parquet access if allowed.
- Model comparison: opponent-only baseline, logistic elastic net, EBM, grouped seed/scene splits, nested selection, held-out calibration/Brier/log loss, stability and feature availability.
- OOB generalization estimates apply only to applicable estimators; neither OOB nor grouped CV is a confirmatory null-hypothesis test. Follow promising card/pilot findings with independently seeded, controlled card-swap or policy A/B simulations.
- Add scalable **source-evidence-linked** sparse card indicators and time-to-cast with audited turn mapping, all card deck roster, censoring, and early resource/board features as source semantics mature.

## Coordination steps

1. Worker branch keeps UI endpoint changes bounded and backward-compatible.
2. Analysis branch materializes normalized private datasets and publishes versioned feature manifest contracts on a **separate branch**.
3. Once new native batches are available, run cross-check: cohort catalog -> manifest -> per-shard digest -> game/event/feature counts -> filtered feature query -> compare original source replay.
4. Only after successful private smoke tests and auth/security review, implement and deploy the private Worker `/v1/analytics` endpoints.
