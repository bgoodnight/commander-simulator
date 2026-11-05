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

## Draft approved game-detail and event-segment endpoints (PR #175)

- `GET /v1/games/{encoded_game_id}?deck=<deck>`: a single approved-current decisive game's public-safe metadata. Encode the complete game ID as a URL path segment (including its slashes), and send the selected hero deck separately.
- `GET /v1/games/{encoded_game_id}/timeline?deck=<deck>`: a bounded **event-family segment preview**. Segments begin at native Gorge kind 9 (`turn_change`), not necessarily the start of a complete player round. The response reports counts per kind for non-secret events, withheld-event counts, and segment sequence bounds. It does not expose individual actions, cards, object IDs, event JSON, player-private zones, or native intents.
- Both endpoints require source-backed explicit cohort approval. An empty current registry fails closed, returning no game. They are a development preview, **not** a complete replay UI.
- The timeline reader projects only `game_id`, `seq`, `kind_id`, and `secret` from private `events.parquet`, with a 16 MiB / 100,000-event shard guard. Larger shards require a separate indexed projection architecture; do not relax limits without benchmarking.
- Do not claim complete native timeline coverage for a game until its R2 source and full segment count have been validated. The authoritative recording remains private and immutable.

## Deploy and benchmark

1. Create an account-scoped Cloudflare API token with **Edit Cloudflare
   Workers** permission. Add it as GitHub Actions secret
   `CLOUDFLARE_API_TOKEN` (do not paste it in chat or commit it).
   `GORGE_R2_ACCOUNT_ID` already supplies the Cloudflare account ID.
2. Once the isolated Worker-only PR is reviewed and merged, navigate to
   GitHub Actions > **Deploy private-bucket Gorge R2 read-only Worker** >
   **Run workflow** on `main`. It is manual-only, never triggered by
   unrelated commits.
3. The manual deployment workflow will automatically verify `/health`,
   generate a temporary randomly generated `BENCHMARK_TOKEN` Worker secret,
   run seven actual bounded, private R2 Parquet reads, publish median and
   P95 phase timings to its GitHub Actions summary, and **delete the token**
   afterward. If revocation fails, the workflow fails and explicitly flags
   manual cleanup. No token is included in the report.
4. Save the `workers.dev` URL from the successful action. Compare R2 listing,
   manifest, decoding and total API time to an initial target of P95
   below one second. Repeat benchmarks across larger warehouse panels later.
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
