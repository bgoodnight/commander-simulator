# Cloudflare Access account experiment (isolated branch, not deployed)

## Purpose
Start with a private invite-only authentication layer for Commander Deck Lab without storing
passwords or interfering with the public GitHub Pages frontend and current R2 Results Worker.
Magnus the Red (`magnus_premium`) and Mortarion (`mortarion_current`) are **community**
decks visible to any invited authenticated member. Neither is a private deck in this phase.

## What is implemented
- Standalone **undeployed** Worker in `workers/community-access/`, no changes to existing Worker,
  frontend, production cohorts, publication, secrets, Cloudflare settings or simulation actions.
- Explicit `ctx.access` verified identity; no user-supplied roles or unverified JWT decoding.
- `GET /v1/account/me` and `GET /v1/decks/community` (authenticated only).
- Owner-only placeholder `POST /v1/simulations`: denies nonowners (403), returns 501
  for owners; it **does not start games**.
- Pure deck visibility/ownership rules and Node tests.
- Disabled by default with `ENABLE_COMMUNITY_ACCESS=false`.

## Cloudflare configuration required before any preview
1. Create an **Access-protected Worker application** for the isolated development Worker.
   Set Access to protect **all traffic**, including its workers.dev hostname and previews.
2. In Access policies, **allow only specifically invited email addresses** (not any email
   on a public domain). Cloudflare's one-time PIN login is sufficient for initial testing.
3. Set `ENABLE_COMMUNITY_ACCESS=true` only after Access policies protect all routes,
   and privately configure `ACCESS_OWNER_EMAILS` to the site owner's verified email.
   Never commit real email allowlists or credentials.
4. Verify unauthorized and uninvited requests cannot reach Worker endpoints; verify
   owner/member `/v1/account/me` role distinction and account logout/revocation.
5. Run `node --test workers/community-access/permissions.test.mjs`.
   Do not connect frontend buttons until browser cross-origin/session behavior is reviewed.

## Security boundaries and future migration
Cloudflare Access establishes **identity**, not deck row-level authorization. Every private
deck API, D1 query, and simulation endpoint must validate the server-side account and scope
queries by owner ID; never trust a hidden button, request body ownership, or a client-provided
email. For stable ownership, use an immutable provider identity subject rather than email alone
when implementing persistent user profiles, with explicit account-linking and migration policy.

Currently the community list is metadata only. It does not create personal decks or protect
decklist files from public GitHub Pages: anything committed to the public repository is public.
Personal decklist storage must use private D1/R2 plus authenticated Worker reads and writes.
Do **not** add the future private deck lists to Pages assets.

### Future phases (not implemented)
- Account-backed personal deck CRUD, D1 ownership tables, explicit community sharing.
- Signed-in UI and account/session status, protected API and CORS/cookie integration.
- Quota-controlled simulation queue, audit, rate-limits, explicit approval and automatic
  R2 publication; continue to keep production simulation/publication separate.
- Optional self-service registration only after invite-only workflows prove reliable.

Reference: https://developers.cloudflare.com/workers/configuration/cloudflare-access/
