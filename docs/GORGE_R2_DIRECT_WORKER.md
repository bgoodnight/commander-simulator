# Gorge R2 direct-query Worker (experimental)

This is a read-only Cloudflare Worker prototype. It does **not** replace the live
Deck Lab, move R2 objects, or run simulations. Existing authoritative native
recordings and `warehouse/v1/.../games.parquet` remain intact.

## Architecture

Gorge -> private `gorge-simulations` R2 bucket -> Worker `GORGE_R2` binding
-> eligible game rows / aggregate results -> optional GitHub Pages client.

The Worker uses hyparquet + hyparquet-compressors to read the **existing ZSTD
Parquet files** using byte ranges, only when a current cohort is explicitly
approved. No additional analytical tables or static GitHub data publication
are required for win rates and matchup summaries.

Public GET routes:

- `/health`: API alive, R2 binding present. No source data.
- `/v1/summary?deck=mortarion_current`: per-deck decisive win/loss and
  opponent matchup summary, with server processing time and number of R2
  shards examined. Current cohort approval is mandatory.
- `/v1/benchmark?deck=mortarion_current`: **disabled unless**
  `BENCHMARK_TOKEN` has been configured as a Worker secret and the request
  includes `Authorization: Bearer <BENCHMARK_TOKEN>`. Times listing,
  manifest retrieval, and decoding one actual raw Parquet shard. Returns
  counts/timings, not any source game rows. This diagnostic does not approve
  a cohort.

The R2 bucket remains private. The Worker has **no writes**, arbitrary object
key paths, full native logs, event queries, object catalogs, or hidden-zone
retrieval. The approved cohort registry is imported from the repository's
versioned `data/gorge_analytics_cohort_registry_v1.json`, and the same
fingerprint/status/decisive checks apply to all returned aggregate rows.
Historical/unversioned data stays excluded. The registry currently has zero
approved current cohorts, so the correct live response is
`awaiting_cohort_approval` if source shards exist.

## Deploy and benchmark

1. Create an account-scoped Cloudflare API token with **Edit Cloudflare
   Workers** permission. Add it as GitHub Actions secret
   `CLOUDFLARE_API_TOKEN` (do not paste it in chat or commit it).
   `GORGE_R2_ACCOUNT_ID` already supplies the Cloudflare account ID.
2. Once the isolated Worker-only PR is reviewed and merged, navigate to
   GitHub Actions > **Deploy private-bucket Gorge R2 read-only Worker** >
   **Run workflow** on `main`. It is manual-only, never triggered by
   unrelated commits.
3. Save the returned `workers.dev` URL. Visit `<URL>/health`.
   For the private benchmark, run from an authenticated Cloudflare Wrangler
   session in `workers/gorge-r2-api`:
   `npx wrangler secret put BENCHMARK_TOKEN`
   using a newly generated random value, then
   `curl -H 'Authorization: Bearer <token>' '<URL>/v1/benchmark?deck=mortarion_current'`.
   Do not put tokens in browser query parameters or Pages JavaScript.
4. Measure 10 cold and 10 warm requests, reporting median/P95 total,
   R2 listing, and Parquet decoding time. Compare to the current static
   page and query the other player deck(s).
5. For the visual preview, the separate, still-unmerged UI adapter uses
   `?r2Api=<URL>`. It displays explicitly approved statistics and actual
   server/client latency. When the Worker is unavailable the existing
   static UI remains usable.

## Limits and decision gates

- Up to 40 source shards and 16 MiB per games Parquet. Shard discovery
  scans a bounded number of R2 list pages; if truncated it **fails closed**
  rather than claiming a complete win rate. That is intentional for an
  initial performance experiment, not a permanent warehouse-scale solution.
- Event-level details and full replays are **not yet served**. Those remain
  private until a separate authorization and redaction review. Regressions
  remain offline/versioned; we do not refit elastic net per HTTP request.
- Current `games.parquet` rows predate cohort stamping and should not be
  silently upgraded. A new, verified current cohort is needed to exercise
  a nonempty approved win-rate response.
- This tests a Worker-backed Parquet read, not Cloudflare Basin SQL.
  The API should not perform broad full-bucket scans in production.
- We have **not yet measured actual deployed R2 latency** until Cloudflare
  deployment credentials are available. Offline unit tests and Wrangler
  dry-run builds only confirm the code compiles.

Recommended acceptance: P95 under ~1 second on the initial panel, with
correct cohort/games count, successful mobile CORS, and no unapproved game
leakage. If too slow, evaluate caching a compact approved per-batch games
index or Cloudflare's query services; retain R2 as authoritative storage.
