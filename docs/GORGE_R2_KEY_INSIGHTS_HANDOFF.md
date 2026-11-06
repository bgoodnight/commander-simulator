# R2 full-cohort Key Insights — integration handoff

## Scope and status

This change is stacked on scalable Results PR #200 and isolated as PR #204.
It only adds full-cohort card features: it does **not** change simulation
rules, approve cohorts, or perform R2 writes during normal Worker requests.

- Per-approved-shard native evidence: `warehouse/v1/{batch}/{deck}/{shard}/card-insights.v1.json`.
- Derived immutable report: `results/materialized/v1/versions/{version}/{deck}/insights.json`.
- Public Worker: `GET /v1/ui/insights?deck=<deck>`; same pointer, registry, digest and version as catalog, game pages and replays.
- The frontend passes the returned deck report to the original renderer as
  `fullCardInsights`, with the **entire cohort count** as `fullCohortGames`.
- The answer is `insights_pending` until **every** approved source game has
  explicitly verified native features. Do not compute rankings from 25 rendered
  games, and never silently use the last complete but stale insight population.

## Producer and publication

The native evidence producer is
`python -m tools.gorge_r2_insight_evidence --native-source <full-native-artifact-directory> --shard <approved-warehouse-shard-directory> --out <private-card-insights-sidecar-path>`.

It requires `runs.jsonl` plus **all corresponding native/gorge-seed-*.json**
recordings, the stamped approved Parquet shard, original sanitized UI
projection and the selected UI catalog revision. It checks SHA-256 source
identity, recorded seat/chain/outcome, **exact** full-shard game coverage and
cards belonging to the pinned hero deck. The source-backed extractor must
include the reviewed player-attribution fix; an opponent-owned spell credited
as played by the hero fails closed.

The manual GitHub Action **Publish verified native card insight evidence to R2**
accepts the exact run ID, source artifact name, batch, deck and shard. It
compares an existing sidecar byte-for-byte rather than overwriting it, verifies
readback, and triggers a full-cohort materialized rebuild on successful
completion (after the workflows are merged to the default branch).

For the existing corrected pilot candidate, the source run is
`42143344243`; source artifacts were archived for
`mortarion_current` and `magnus_premium`, but **do not run this action**
until the attribution-corrected extractor is merged and source digest
compatibility is verified. Feature objects are never published into the
public bucket path without complete approval and native evidence verification.

## Browser validation owned by Work mode

Use the stacked branch
`feature/r2-full-cohort-key-insights-20261106` to check Key Insights UI;
the base branch of PR #200 does not include this feature until integration.
Preview materialized layout with `?materializedResults=1`. The catalog and
insights responses must share `version`, `deck`, and full cohort
`total/verified_games/observed_games`. Confirm page 0/1 changes do **not**
alter named-card rankings, and the missing evidence state shows a pending
message rather than made-up data.

A release smoke should exercise at least one corrected Mortarion game and
assert **Exclude** (or any other opponent-owned card absent from the hero
library) never appears in hero played-card rankings. Also check distinct
simulation batches that reuse numeric seeds, wrong UI deck SHA, incomplete
shard coverage, and appended batch recomputation. Existing outcomes and
turn-reviewer views must continue working if card insights are pending.

## Remaining gate

This is implemented and fixture-tested but is **not** a claim that real
source-backed reports have been published. First approved native feature
sidecars, actual R2 materialized publication, end-to-end UI checks, and a
clean dependency review of attribution-fix PR #199 remain release gates.
