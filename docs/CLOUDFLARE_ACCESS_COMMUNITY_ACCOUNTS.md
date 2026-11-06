# Cloudflare Access community accounts and deck visibility (draft, NOT deployed)

## Design
The isolated Worker in `workers/community-access/` verifies Cloudflare Access identity
and uses a future isolated D1 `COMMUNITY_DB` binding for persistent per-deck visibility.
No password handling, deployment, simulation dispatch or current R2/Pages alterations.

### Visibility semantics
- `private` (default for newly created personal decks): only the deck owner can list/read/edit.
- `community`: visible to **all authenticated invited members** of the Access app,
  not publicly accessible without sign-in. The deck owner alone controls this toggle.
- The current Magnus and Mortarion entries are **initial database migration seeds**,
  each shared with invited members and owned by the special `site-owner` role.
  These are metadata, not newly stored decklist contents.
- Visibility is a database field, not a hardcoded deck-name allowlist. A new public
  deck needs no code changes, just an owner-controlled visibility update.

### API endpoints
- `GET /v1/account/me`: signed-in identity, owner/member permissions.
- `GET /v1/decks`: shared metadata plus caller-owned private deck metadata, with `can_edit`.
- `GET /v1/decks/community`: shared metadata only.
- `PATCH /v1/decks/:id/visibility`: exact body `{"visibility":"private"}` or
  `{"visibility":"community"}`; identity-derived owner permission, parameter binding,
  fail-closed on missing database. Requires Access-authenticated session.
- `POST /v1/simulations`: still intentionally nonfunctional (owner receives 501,
  other users 403). No simulation workload can be started.

The unmounted `web/pages/deck_visibility.js` exports `mountDeckVisibility(root)` for
the eventual signed-in deck list. It displays owner-only Public-to-members toggles,
calls PATCH, and restores the checkbox after errors. It is not referenced by the live UI.

## Next staging steps (not performed)
1. Configure a **separate Cloudflare Access protected Worker** for all routes and
   hostnames. Limit policy to specifically invited emails. Do not allow public bypass.
2. Create isolated development D1 and apply
   `workers/community-access/migrations/0001_deck_visibility.sql`.
   Bind it as `COMMUNITY_DB` to this isolated Worker only.
3. Set `ACCESS_OWNER_EMAILS` privately and enable `ENABLE_COMMUNITY_ACCESS=true`
   only after verified Access enforcement. Do not commit real account data.
4. Run `node --test workers/community-access/permissions.test.mjs` and
   staging integration tests for unauthorized/owner/friend requests, logout/revocation,
   persistence across Worker restarts, two-account visibility changes and browser cookies.
5. Integrate `mountDeckVisibility` into the actual signed-in Deck Editor only after
   the current R2 UI stabilization and branch reconciliation.

## Critical security boundaries
**The toggle does not make existing GitHub Pages decklists private.**
Files already checked into this public repository or served as static Pages assets
remain accessible at their original URLs even when database metadata says private.
Before offering a real private deck feature, migrate decklist contents to protected
R2 or D1 storage and enforce the visibility filter for every retrieval and mutation.
Never treat a hidden UI button as authorization.

No Access account is created by this code. Private deck ownership uses the verified
Access identity ID (`access:<id>`) rather than a mutable email; current site-owned
catalog seeds are editable only by the explicitly configured owner role.
Design separate idempotent deck migration and authenticated CRUD before onboarding
private deck records. The frontend must not download private contents in its public
static assets.

Review CORS, CSRF/session mechanics, write rate limits, audit records, and abuse
controls before connecting real signed-in browser mutations or allowing workflows.
Prefer same-origin authenticated deployment or deliberate CSRF protections.
The current branch is **prototype only**, with Access and D1 unset and
`ENABLE_COMMUNITY_ACCESS=false`.

Reference: https://developers.cloudflare.com/workers/configuration/cloudflare-access/
