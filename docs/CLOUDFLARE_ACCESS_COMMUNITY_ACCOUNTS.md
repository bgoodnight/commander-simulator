# Cloudflare Access community decks — isolated implementation (draft)

Status: development branch only, **not deployed**. This backend is deliberately
independent of the current R2 Results rollout and GitHub Pages frontend.

## Current implementation
- Worker `workers/community-access/index.mjs` obtains verified identity from
  `ctx.access.getIdentity()` and denies all requests unless Access is active AND
  `ENABLE_COMMUNITY_ACCESS=true`.
- Database: isolated Cloudflare D1 binding `COMMUNITY_DB`, migration
  `workers/community-access/migrations/0001_deck_visibility.sql`.
- Content: isolated **private** R2 bucket binding `COMMUNITY_DECKS_R2`.
  Decklist bytes are stored under SHA-256-addressed keys. The Worker verifies
  R2 readback before pointing D1 records at the content. Keys are never returned
  to clients. Failed writes may leave harmless, unreachable R2 objects; do not
  garbage collect them without a reference audit.
- Every deck belongs to a verified Access user ID, not a mutable email.
- Community publications are separate immutable revisions. Each listing has one
  current revision pointer. Old revisions remain preserved for simulation evidence.
- Browser writes are same-origin only; a different host will require a reviewed
  cookie/CSRF integration before connecting the GitHub Pages interface.
- No Cloudflare Access app, D1 database, R2 bucket or secrets have been created.
  No production or staging Results Worker changes are made.

## Functional API
All API paths require Access and private storage bindings.

| Method | Path | Access | Meaning |
| --- | --- | --- | --- |
| GET | /v1/account/me | invited account | Identity and permissions |
| GET | /v1/decks | stable account ID | Own private deck metadata |
| POST | /v1/decks | stable account ID | Create own private deck |
| GET | /v1/decks/:id | owner only | Read exact deck contents |
| PUT | /v1/decks/:id | owner only | Change draft with expected revision |
| POST | /v1/decks/:id/publications | owner only | Publish saved deck as immutable revision 1 |
| GET | /v1/publications | invited account | Current listed snapshot metadata |
| GET | /v1/publications/:id | invited account | Current listed snapshot content |
| POST | /v1/publications/:id/replace | owner only | New immutable revision and atomic pointer advance |
| POST | /v1/publications/:id/unpublish | owner only | Unlist, retain historical revision records |
| POST | /v1/publications/:id/copy | invited account | Make independent private copy with source revision ID |
| POST | /v1/simulations | owner only | Still intentionally returns 501; does not run games |

Every write requires a matching Origin. Existing direct visibility PATCH is retired
(410), because publishing does not change privacy of the personal original.

## Verification
`node --test workers/community-access/permissions.test.mjs`
uses Node's built-in SQLite adapter to execute the actual D1 SQL migration and
uses an in-memory R2 mock. This exercises API requests end-to-end for two accounts,
revisions, unpublish, copying, hash mismatch, optimistic edit conflict, and disabled
simulation dispatch. This is not a substitute for live Cloudflare Worker/D1/R2 tests.

The backend accepts plain text decklists bounded by size, but **does not yet check
Commander deck legality, canonical Oracle identities or 100-card quantities**.
That must be done at the deck import/validation boundary before enabling UI
publication. Existing Magnolia/Mortarion deck lists have NOT been copied into
account storage, nor auto-seeded as public listings. They should be imported only
after verified source choice and explicit staging testing.

## Next release gates
1. Wait for ongoing Results staging to move to production; do not merge this PR
   until there is one stable Worker access and Results API contract.
2. Create a separate Cloudflare Access-protected development Worker (all traffic),
   invite specific email addresses and verify identity+revocation; never configure
   a broad public email-domain allow rule.
3. Create isolated D1 and private R2 bucket, bind them, apply migration,
   and verify persisted data after Worker restart and actual R2 readback.
4. Confirm D1 `batch()` transaction rollback and stale-revision concurrency,
   and verify unpublish revokes ordinary community reads on every endpoint.
5. Validate account identity stability, source content and policy for private
   deck deletion and archival retention; add audit logging, rate limits,
   idempotency keys and safe origin/session architecture.
6. Migrate decklist contents out of publicly accessible Pages assets before
   offering genuine private decks; UI hiding is not security.
7. Mount public snapshot controls in the existing Deck Editor and add browser
   tests, then connect the authenticated Result Worker with exact deck revision
   and approved cohort IDs, as described in
   `docs/ACCOUNT_RESULTS_VISIBILITY_INTEGRATION.md`.

## Historical integrity
Replacing or unlisting a community publication never mutates the saved personal
deck, existing publication revisions, another member's private copy, or an R2
simulation cohort. Analytics must always point at the exact source content SHA
and publication revision ID used during its simulation.

Reference: https://developers.cloudflare.com/workers/configuration/cloudflare-access/
