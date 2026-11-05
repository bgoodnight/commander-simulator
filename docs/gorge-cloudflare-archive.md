# Gorge long-term archive: Cloudflare R2 bootstrap

This first increment is intentionally **archive-only**. It does not provision
Cloudflare resources, migrate the GitHub Pages UI, or claim to provide a live
queryable database. It prevents permanent loss of full Gorge native logs once
Cloudflare is connected.

## One-time Cloudflare setup (same account as Wasted Wargaming)

1. In Cloudflare **R2 Object Storage**, create a **private** bucket named
   `gorge-simulations`. Keep public access disabled.
2. Create an R2 API token restricted to **Object Read & Write** for only that
   bucket. Record the **Access Key ID** and **Secret Access Key**. Use the R2
   account ID from your Cloudflare dashboard.
3. In `bgoodnight/commander-simulator` → Settings → Secrets and variables →
   Actions, create these **repository secrets**:
   - `GORGE_R2_ACCOUNT_ID` (account ID)
   - `GORGE_R2_ACCESS_KEY_ID`
   - `GORGE_R2_SECRET_ACCESS_KEY`
4. Run the **Gorge · four-deck 500-game benchmark** workflow manually only
   after the configuration is complete and the associated PR is merged.

The workflow first verifies and extracts results from all 100 games per shard.
When configured, it packages all 100 original native Gorge logs, `runs.jsonl`,
`pod.json`, and `card-insights.json` into one gzip archive. It uploads the
archive to `native/v1/<deck>/<shard>/<run-id>-<attempt>.tar.gz` under the
private R2 bucket **before** pruning 98 local native logs. A failed upload
fails the shard rather than silently discarding the recordings.

If no secrets are set, the existing workflow still runs and retains only the
legacy two native recordings per shard. Partial credential configuration fails
explicitly.

**Security:** never commit Cloudflare credentials or native hidden-state
recordings into the public repository. Archives include omniscient synthetic
game logs and are private by design.

## Next increments (not implemented in this PR)

- Create deterministic versioned Parquet datasets for all outcomes, turn/event
  records, and card-level features, retaining source checksums and provenance.
- Maintain an indexed D1 game catalog and cached summaries; retain full Parquet
  and authoritative recordings in R2.
- Implement authenticated ingestion and a read-only Worker query API. Use
  scheduled batch DuckDB analysis for expensive whole-cohort queries rather
  than scanning the full warehouse in every HTTP request.
- Integrate selective API fetching with the existing GitHub Pages UI, while
  preserving its static manifest/replay fallback.
- Backfill historical GitHub Actions artifacts where source recordings are
  still available; analytics-only historical runs cannot recreate deleted
  authoritative native event logs.

## Verification

Review the modified workflow's `Extract all card measurements...` step and
its action logs. A configured shard should report archival of 100 native games
before its existing assertion confirms two local replay sources remain.
Check the private bucket for the gzip archive and validate 100 native JSON
members, the runs JSONL, pod metadata and insights before relying on retention.
