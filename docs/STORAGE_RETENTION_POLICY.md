# Commander Simulator: Git, Pages and R2 storage policy (2026-11-05)

## Canonical data locations

**Git:** Versioned source code, contracts, tests, decklists, pinned card identities, and a small validated public replay catalog. Git must not become the durable store for full Gorge simulation outputs.

**Private R2 / native/v1:** Complete source-backed native Gorge logs, intents, omniscient game states, original run summaries, pod configuration and provenance, archived before any sampled replay pruning. Preserve immutable batch/seed/deck identifiers.

**Private R2 / warehouse/v1:** Source-backed Parquet game and event tables, versioned by batch/deck/shard, with hashes and manifests. Use these for all-cohort statistics and analysis, not the limited UI replay selection.

**Public UI source / web/pages/data/gorge:** Validated manifest, small full-cohort aggregate stats, card insights, and selectively retained, verified detailed replay projections. The site must never expose R2 credentials or raw private recordings.

**GitHub Actions artifacts:** Temporary transfer and diagnostic bundles (typically 7–14 days), not a durable backup.

## Why today's checkout is large

The existing branch-based GitHub Pages deployment has a generated mirror under docs/deck-lab, built from web/pages plus published data. It includes 53 historical bounded-simulation release identifiers also present under web/pages/data/simulation-archive/releases. Gorge UI replays and historical game outcomes are mirrored as well.

Git stores identical object blobs only once in a commit, so repeated checked-out bytes are not directly equal to additional billed Git storage. But working directories and generated Pages payloads are larger, and repeatedly committing the generated site creates Git history.

A saved Git archive branch is not proof that an independent R2 backup exists. Removing files from main also does not purge old Git history.

## Safeguards introduced by this audit

- Full 2,000-game Gorge workflow fails closed if any R2 credential is absent, rather than discarding 98/100 recordings per shard.
- Native-to-UI conversion must be deliberately dispatched against a specified simulation run. Changing converter source no longer automatically processes the obsolete fallback recording.
- Static Pages build warns at 175 MiB and fails at the project's 250 MiB budget, avoiding unbounded publication.
- Pages runs for the same branch cancel older queued or in-progress builds.
- Weekly/on-demand storage audit measures tracked file sizes and identical mirrored files; where secrets are configured it also reports R2 bucket, native and warehouse sizes.
- Git ignore rules cover new local build outputs and binary archive formats.

## Next migration, only after backup validation

1. Inventory old Python and Gorge source recordings; ensure every batch being removed from Git has an independently verified R2 archive, provenance manifest, and checksums.
2. Preserve historical result catalog references and archived statistical comparisons; keep an immutable mapping from old URLs to any replacements.
3. Replace large browser-loaded historical bundles with small full-cohort precomputed summaries and lazy-loaded selected replays. For authorized full recordings, use an access-controlled service/Worker in front of private R2.
4. Deliberately switch the GitHub Pages source setting to GitHub Actions after a live and staging UI smoke test. Then stop committing the generated docs/deck-lab mirror to main.
5. Only then retire corresponding old data directories from the active branch. Do not force-push or rewrite Git history just to make the storage figure smaller.

## Suggested retention

| Data | Where | Policy |
| --- | --- | --- |
| Decks, code, tests, data contracts | Git | Versioned |
| Native Gorge recordings and provenance | Private R2, native/v1 | Keep until explicit archival review |
| Full Parquet game/event warehouse | Private R2, warehouse/v1 | Versioned; retire superseded derivatives only with verification |
| Published aggregate stats and selected replays | UI source / published Pages | Bounded active catalog |
| Actions bundles and diagnostics | GitHub Actions | 7–14 days |
| Legacy Python release snapshots | Existing Git tree/archive until independent backup is verified | No bulk deletion yet |

**Do not enable automatic R2 expiration for the only verified source copy of any study or batch.**