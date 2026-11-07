# Private analytical R2 access (not the public Results API)

The analytics branch is allowed to read historical, incomplete, experimental, unapproved and corrected simulations. This access is independent of the cohort-approval filters in the public Results Worker. A full recording is evidence for research, not publication eligibility.

## Dedicated Worker
`workers/gorge-r2-analytics` binds the existing R2 bucket and exposes authenticated, read-only listings and exact-object GETs for any R2 object key in the dedicated Gorge bucket. This is deliberately not the public Results Worker. It never uses the approved-cohort registry, excludes no simulations by winner/status, and never writes to R2.

**Security configuration:** `workers_dev=false`; deploy only to a dedicated Cloudflare Access-protected custom hostname/route, with `ANALYTICS_READ_TOKEN` as a Worker secret (at least 32 characters). Access service tokens or an identity policy are enforced at the Cloudflare edge in addition to the bearer token. Do not commit tokens, enable permissive CORS, or mount this route in the public Pages UI. Restrict secret availability to trusted analytics deployment workflows. Rotate/revoke it if compromised.

Example (authenticated client):
```bash
curl --fail -H "Authorization: Bearer $ANALYTICS_READ_TOKEN" \
  "https://<private-analytics-host>/v1/analytics/inventory?prefix=warehouse/"
```

Pagination uses the returned cursor. A blank inventory prefix lists the full bucket, including unknown historical layouts. `/v1/analytics/object?key=...` returns original raw source bytes, including omniscient events, intents, object registries, hidden hands and libraries. For large objects use authenticated `Range: bytes=start-end` requests in chunks of at most 16 MiB, checking `Content-Range` and source integrity on assembly. This is not an automatic durable modeling staging export. A Worker binding allows underlying R2 access, so endpoint code and authorized clients must be trusted even though all server routes are GET-only.

## Branch execution and permissions
GitHub branch permissions do not grant Cloudflare R2 access by themselves. For the isolated analytics branch, authorize a separate CI environment/credential with read access to the Gorge bucket, and permit read-only experimental extraction regardless of cohort approval. Keep production publishing roles and public UI cohort gating unchanged.

No Cloudflare account permissions, Access policies, secrets, DNS routes, or Worker deployments are changed simply by committing this code. Those are separate account-authorized configuration actions.

## Modeling
Stage source-verified datasets in a separate restricted analytics workspace. Retain all attempts and native evidence; version each game by batch/hero/shard/seed, engine/rules/deck fingerprints, and source hash. Source availability and model eligibility are independent. Never train from sanitized UI pages or treat old versions as current card efficacy.
