#!/usr/bin/env bash
# One-time trusted operator bootstrap. Does not publish a public route.
set -euo pipefail
cd "$(dirname "$0")"
: "${CLOUDFLARE_API_TOKEN:?Set a Workers-edit scoped Cloudflare API token}"
: "${GORGE_R2_ACCOUNT_ID:?Set the Cloudflare account ID}"
: "${ANALYTICS_READ_TOKEN:?Set a strong private analytics bearer token}"
if [[ "${#ANALYTICS_READ_TOKEN}" -lt 32 ]]; then
  echo "ANALYTICS_READ_TOKEN must have at least 32 characters" >&2
  exit 1
fi
export CLOUDFLARE_ACCOUNT_ID="$GORGE_R2_ACCOUNT_ID"
npm install --ignore-scripts --no-audit --no-fund
npm test
# No workers.dev, preview URL or custom domain is configured at this stage.
npx wrangler deploy --name gorge-r2-analytics-private
printf '%s' "$ANALYTICS_READ_TOKEN" | npx wrangler secret put ANALYTICS_READ_TOKEN --name gorge-r2-analytics-private >/dev/null
echo "Private Worker deployed without a public route."
echo "NEXT (Cloudflare dashboard): protect the Worker with Access; attach a private"
echo "custom domain; grant only your analytics identities/service tokens."
echo "Then verify anonymous GET /v1/analytics/inventory is denied and"
echo "authenticated requests succeed before using it for bulk source retrieval."
