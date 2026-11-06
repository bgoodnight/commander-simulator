# Community accounts Worker: local smoke test and isolated Cloudflare staging

This PR is **not live**. Protected accounts Worker and public request intake
must be deployed separately, never on the production Results Worker.

## 1. Locally verify the actual Workers
From the repository root with Node 22+ and Wrangler 4:

```sh
node --test workers/community-access/*.test.mjs
npx --yes wrangler@4 deploy --dry-run --config workers/community-access/wrangler.toml
npx --yes wrangler@4 deploy --dry-run --config workers/invitation-intake/wrangler.toml

# Local-only D1, local-only R2; no Cloudflare credentials required.
npx --yes wrangler@4 d1 execute commander-community-local --local \
  --config workers/community-access/wrangler.local.toml \
  --file workers/community-access/migrations/0001_deck_visibility.sql
npx --yes wrangler@4 d1 execute commander-community-local --local \
  --config workers/community-access/wrangler.local.toml \
  --file workers/community-access/migrations/0002_invitation_requests.sql
npx --yes wrangler@4 dev --config workers/community-access/wrangler.local.toml
```

The **local-only config** simulates a signed-in `owner@example.test` via
`access.dev`, which Cloudflare documents for local Worker testing. It
must **never** be used for actual deployment: simulated identity is not real authentication.
The local API should respond at `/v1/account/me`, then allow creating a private
deck and publishing a snapshot. Use a separate local identity to test denied
private reads. Real policies cannot be validated with a simulated identity.

## 2. Actual Cloudflare staging resources (not yet created)
1. Verify the Cloudflare account has Zero Trust enabled and you have permission
   to administer Workers, Access, D1, and R2.
2. Create dedicated **private** `commander-decks-staging` R2 bucket and D1
   `commander-community-staging` (capture its generated database UUID).
   Never use `gorge-simulations` / the Results R2 binding.
3. Bind `COMMUNITY_DECKS_R2` and `COMMUNITY_DB` in the isolated account
   Worker config and apply both database migrations using Wrangler.
4. Configure a Cloudflare Access allow policy listing your invited emails.
   Deploy to a distinct Worker with `ENABLE_COMMUNITY_ACCESS=false`, then in
   **Workers & Pages > Worker > Access** select **Protect this Worker behind
   Access > All traffic**, and verify an uninvited browser cannot enter.
   **Only after confirmation** change `ENABLE_COMMUNITY_ACCESS=true` and set
   `ACCESS_OWNER_EMAILS` privately to your verified email address.
5. Test `GET /v1/account/me` for owner and friend, denied outsider,
   owner/private deck storage, publication replace/unpublish/copy, and data
   persistence across Worker redeploy.
6. Confirm the same-origin browser design and CSRF guarantees before connecting
   GitHub Pages Deck Editor (currently separate origin). Existing API rejects
   cross-origin writes intentionally.
7. Treat the public **invitation-intake** Worker as an independent deployment,
   with `ENABLE_INVITATION_INTAKE=false` until a real Turnstile widget,
   siteverify secret, request origin/hostname, D1 binding and WAF rate limits
   are configured and tested.

## 3. Go/no-go
Do not mark this as staged if only CI bundles or Node tests pass.
Production needs a real Access policy, verified user sessions, isolated R2+D1,
correct member privileges, verified account revocation, and safe public
request intake. No secrets or Cloudflare account IDs belong in Git.

Cloudflare Access Worker docs:
https://developers.cloudflare.com/workers/configuration/cloudflare-access/
