# Invite-only account onboarding — staging handoff

This is **development-only** code on draft PR #218. Nothing is deployed.

## Launch behavior
1. Owner adds a friend's verified email manually to the Cloudflare Access
   application allowlist. The friend signs in via Cloudflare email one-time PIN.
2. The protected account Worker accepts only Cloudflare-verified identities.
   Roles/ownership remain server-side; no in-app passwords or account credentials.
3. When ready to expand, an optional **Request invitation** form submits a
   Turnstile-verified email, name and note into the isolated D1 invitation queue.
4. The owner can review pending requests in the owner-only API/UI and choose
   Decline or **Approve for invitation**.
5. Approving for invitation sets `awaiting_access_allowlist`: this is NOT a
   Cloudflare account or an active permission. The owner must still add that
   email to the actual Cloudflare Access allowlist. Do not tell applicants their
   account is active until Cloudflare access is verified.

## Components
- Protected Worker: `workers/community-access/index.mjs`
  - `GET /v1/admin/invitations` owner only
  - `POST /v1/admin/invitations/:id/review` owner only;
    `{"status":"declined"}` or `{"status":"awaiting_access_allowlist"}`.
- Separate *public* intake Worker: `workers/invitation-intake/index.mjs`
  - `POST /request-invitation` with `email`, optional `display_name`,
    optional `note`, and `turnstile_token`.
  - `OPTIONS` restricted to configured form origin.
  - Requires Turnstile siteverify success **and expected hostname**.
  - D1 `invitation_requests` table has a unique normalized email.
  - Repeated submissions return generic `received:true` and do not reveal status.
- Unmounted UI: `web/pages/invitation_access.js`: email request and admin queue.
  Must receive a real Turnstile token from a deployed Cloudflare widget.

## Safeguards / staging requirements
- Configure separately deployed, public intake Worker at a restricted host.
  Enable only after `TURNSTILE_SECRET_KEY`, `REQUEST_FORM_ORIGIN`,
  `REQUEST_FORM_HOSTNAME` and `REQUEST_DB` are set.
- Protect the public endpoint from abuse with Cloudflare WAF/rate limits
  (per-IP and distributed), bot checks and monitoring. Turnstile is not a
  replacement for rate limits.
- Keep private Access API and public intake API on **different Workers/routes**.
  No public Access bypass paths on the private API.
- Configure CORS only for exact trusted form origin; no wildcard credentials.
- Configure same-origin admin review writes and test Access revocation,
  email invite lifecycle and separate user sessions.
- Actual notifications, email verification to guard against email spoofed
  requests, dashboard allowlist automation and request deletion/privacy policy
  are later enhancements. A request email is **unverified** until its user signs
  into Cloudflare Access.
- Provision `0001_deck_visibility.sql` then
  `0002_invitation_requests.sql` on isolated staging D1.
- Full CI: `node --test workers/community-access/*.test.mjs`.

The existing R2 Results worker, site, and simulation approval pipeline are
unchanged. Invitation approval does not publish decks or approve simulations.
