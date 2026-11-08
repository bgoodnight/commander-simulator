# Account publication ↔ Results visibility integration contract

Status: design compatibility note for draft PR #218. No runtime integration, Cloudflare deployment,
or modification to the staging Results branch.

## Reviewed upstream
- `feature/unified-results-visibility-20261106`:
  `docs/RESULTS_VISIBILITY_CONTRACT.md`, `web/pages/r2_original_results.js`
  and `web/pages/game_outcomes.js`.
- PR #220: Key Insights visibility remains a *source-backed evidence* decision.
- The staging contract says Worker/R2 controls viewer authorization and approved-current
  cohort eligibility; the frontend has `loading`, `unavailable`, `ready`.
- Missing insights must never invalidate otherwise verified outcome/replay data.

## Namespace distinction (important)
- **Deck publication** is a shared, immutable *decklist* revision.
  Identifiers: `publication_id`, `publication_revision_id`, `deck_content_sha256`.
- **Results publication** is a verified, immutable *simulation cohort* snapshot.
  Identifiers: `results_snapshot_version`, `cohort_id`, source/provenance hashes.
- They are different objects. Do not reuse `version` or `visibility` for both.
- Every cohort is pinned to the **exact decklist revision/content hash used to run it**,
  whether from an owner-private deck or a public publication revision.
- Replacing the listed deck revision must not relabel an old results cohort as belonging
  to the replacement. The frontend must select an exact eligible revision.

## Worker responsibilities (one authoritative read gate)
For each requested deck/revision + results request:
1. Verify Cloudflare Access identity for protected requests. Public-to-members means
   *invited authenticated members* in this first phase, not anonymous internet users.
2. Resolve allowed deck revision: owner of personal deck, or currently listed community
   snapshot. Never trust a client supplied owner/role/visibility flag.
3. Verify requested R2 cohort is approved/current **for that exact deck hash** and
   that all summary/replay/insight fields match the cohort ID/version.
4. Return only an authorized, source-verified Results response. The frontend renders
   the existing `ready` / `unavailable` states with independent optional-metric checks.
5. Preserve unavailable/403/404 semantics deliberately: prevent lookup of another
   user's private deck or simulation existence. Do not return raw archive keys.
6. Enforce authorization on every result endpoint, not just catalog:
   `/v1/ui/catalog`, `/v1/ui/page`, `/v1/ui/game`, `/v1/ui/events`,
   `/v1/ui/insights` and legacy equivalents if still enabled.

## Lifecycle
- **Publish community deck:** create immutable deck snapshot, *no automatic simulation approval*.
  Existing results only appear if their exact deck revision/hash has an independently
  verified approved cohort. No simulation jobs run merely because a deck was published.
- **Replace deck:** create new immutable revision; old results remain pinned to old
  revision. New revision shows `R2 results not available` until an eligible cohort is
  independently published; optional explicit historical view can be added later.
- **Unpublish deck:** remove normal community discovery and block ordinary public
  API reads of its revision and associated results. Keep owner access and restricted
  audit/simulation references; never delete copies other users already made.
- **Copy deck:** create new *private* revision with new owner and recorded provenance.
  It does not inherit permission to view another owner's private analytics.
- **Archive cohort:** the cohort is excluded from current results regardless of
  deck publication status. Archival does not delete its immutable evidence.

## Frontend scope
Deck List controls (`Publish snapshot`, `Replace`, `Remove from community`,
`Copy to My Decks`) are separate from the Results UI state machine.
Deck eligibility and Results readiness should arrive as server-calculated response
fields, not be inferred from whether a row is displayed in a list. Existing
Results rendering must remain unchanged for authorized valid snapshots.

## Integration tests required before merge
- Owner vs invited member vs unauthenticated.
- Private deck ID probing across **all** R2 endpoints: no metadata or replay leaks.
- Shared deck visible to invited members; no ability to edit someone else's listing.
- Replaced publication keeps old hashes/evidence and never shows old results under
  the new revision.
- Unpublished publication disappears from community and results while owner/audit
  evidence remains accessible through restricted paths.
- Approved cohort without verified insights still renders valid Outcomes and replay.
- Invalid/mismatched cohort hash or revoked account fails closed.
- Cross-origin and CSRF tests after choosing same-origin authenticated routing.

## Release ordering
Do NOT merge account work into the staging Results integration yet.
First stabilize PR #220 / unified Results visibility, then introduce authenticated
Worker read access and immutable deck-content storage with contract tests, and
only then mount community controls and enable publish/replace/unpublish operations.
