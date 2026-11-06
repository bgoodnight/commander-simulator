# Cloudflare Access + immutable community deck snapshots (draft, undeployed)

## Decision
Personal deck = editable, owned, protected source of truth. Publishing makes a **distinct
immutable snapshot** with a content SHA-256, stable publication ID, and revision ID.
The personal source is never made public or modified by publication. Cloudflare Access
limits community browsing to invited authenticated accounts.

Actions:
1. **Publish snapshot** copies verified deck content to an immutable, privately held
   object accessible only through an authenticated Worker. Publishing must only
   succeed after byte-for-byte content hash readback and a D1 transaction.
2. **Replace snapshot** publishes a NEW immutable revision, advances the listing
   pointer atomically, and leaves the prior revision available by exact ID for
   reproducible simulations. Do not mutate the original revision.
3. **Remove from Community** marks listing `unlisted` immediately; removes it from
   discovery and blocks new ordinary community reads. The underlying immutable
   revisions remain in protected archival storage for simulation audit references.
   Owner-held copies and previously downloaded decks cannot be retracted.
4. **Copy to My Decks** creates a separate new private deck owned by the copier,
   with recorded `source_publication_revision_id`; later replacements/unpublishes
   cannot change that copy. This action is future work, not implemented.

## First Magnus and Mortarion publications
They are intended as the first two community snapshots, but must **not** be
hardcoded or seeded as fake snapshot metadata. First import the real decklists,
hash content, verify storage, then create listings pointing to those revisions.
The public GitHub Pages files remain public until content is migrated.

## Implemented now
- Standalone undeployed Cloudflare Access Worker; login identity from verified
  Access context only; owner/member roles; fail closed without credentials or D1.
- Read-only `GET /v1/publications` (alias `GET /v1/decks/community`) returns
  the current listed revision metadata from D1, not private personal decks.
- `workers/community-access/publications.mjs` pure ownership and lifecycle
  planning helpers; tests for publication, replacement, unpublication and auth.
- D1 **new-database-only** migration defining private decks, publication listings
  and immutable publication revisions.
- Unmounted `web/pages/deck_visibility.js` now offers `Publish snapshot`
  rather than a reversible public/private checkbox; no production UI changes.
- Existing PATCH visibility route retired (410). Planned publish/replace/unpublish
  routes return 501 and do not write data. Simulations likewise remain disabled.

## Not yet implemented
- Real publication writes, content storage, R2 hash verification, D1 transactions,
  account-owned deck CRUD, personal-deck content delivery, community snapshot
  content retrieval, copy-to-my-decks, logged-in UI, or Cloudflare configuration.
- Access revocation, origin/CSRF and rollback tests on a deployed staging Worker.
- Versioned simulation inputs pinned to `publication_revision_id` and content SHA.

## Important production conditions
A hidden UI toggle cannot secure data. A deck stored under a public GitHub Pages
URL remains public even if a private database record exists; migrate the content
before offering private decks. Keep public discovery distinct from private historical
revision resolution: unpublishing must stop new public reads but not invalidate
restricted internal simulation evidence. Never expose content keys or private
archive endpoints to normal community users.

All publishing/mutation endpoints must check Access identity, verify exact ownership
server-side, enforce an origin/CSRF policy, be idempotent, rate limited, audited,
and transactionally update current revision pointers only after object readback.

Suggested future API shapes:
- POST /v1/decks/:id/publications (publish)
- POST /v1/publications/:id/replace (new revision)
- POST /v1/publications/:id/unpublish (remove from discovery)
- POST /v1/publications/:id/copy (private copy)
- GET /v1/publications (listed snapshots only)
- GET /v1/publications/:id/revisions/:revision_id (owner/authorized use only)

The existing separate development branch is deliberately NOT integrated with
the R2 Results UI or production Worker.
