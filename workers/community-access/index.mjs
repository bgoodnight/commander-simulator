import { resolveAccount, canRunSimulations } from "./permissions.mjs";

// Isolated, intentionally undeployed Cloudflare Access prototype.
// Publishing requires durable content-addressed storage and atomic metadata updates;
// all write operations fail closed until those are implemented and reviewed.
const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "private, no-store",
    "x-content-type-options": "nosniff",
    "vary": "Cookie"
  }
});
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (!["GET", "POST", "DELETE", "PATCH"].includes(request.method)) return json({ error: "method_not_allowed" }, 405);
    if (env.ENABLE_COMMUNITY_ACCESS !== "true" || !ctx?.access) return json({ error: "access_not_configured" }, 403);
    let identity;
    try { identity = await ctx.access.getIdentity(); }
    catch { return json({ error: "invalid_access_identity" }, 403); }
    const account = resolveAccount(identity, env);
    if (!account) return json({ error: "identity_required" }, 403);

    if (request.method === "GET" && url.pathname === "/v1/account/me") {
      return json({ account, permissions: { run_simulations: canRunSimulations(account) } });
    }
    if (request.method === "POST" && url.pathname === "/v1/simulations") {
      return canRunSimulations(account)
        ? json({ error: "simulation_dispatch_not_implemented" }, 501)
        : json({ error: "forbidden" }, 403);
    }

    // No direct visibility toggle: a personal deck NEVER becomes a public object.
    // Publish, replace and unpublish will manage distinct immutable snapshots.
    const publicationAction = url.pathname.match(/^\/v1\/decks\/([a-zA-Z0-9_-]{1,100})\/publications$/);
    const snapshotAction = url.pathname.match(/^\/v1\/publications\/([a-zA-Z0-9_-]{1,100})(?:\/(replace|unpublish|copy))?$/);
    if (request.method === "PATCH" && /\/visibility$/.test(url.pathname)) {
      return json({ error: "visibility_toggle_retired_use_publish_snapshot" }, 410);
    }
    if ((request.method === "POST" && publicationAction) ||
        (request.method === "POST" && snapshotAction) ||
        (request.method === "DELETE" && snapshotAction)) {
      if (request.headers.get("origin") !== url.origin) return json({ error: "origin_forbidden" }, 403);
      return json({ error: "snapshot_mutations_not_implemented" }, 501);
    }

    const listing = request.method === "GET" &&
      (url.pathname === "/v1/decks/community" || url.pathname === "/v1/publications");
    if (!listing) return json({ error: "not_found" }, 404);
    if (!env.COMMUNITY_DB) return json({ error: "deck_store_not_configured" }, 503);
    const rows = await env.COMMUNITY_DB.prepare(
      "SELECT p.id, p.label, p.owner_id, p.current_revision_id, r.content_sha256 " +
      "FROM publications p JOIN publication_revisions r ON r.id = p.current_revision_id " +
      "WHERE p.status = 'listed' ORDER BY p.label"
    ).all();
    // No unpublished metadata or draft content is sent to community clients.
    return json({ publications: rows.results.map(row => ({
      id: row.id, label: row.label, current_revision_id: row.current_revision_id,
      content_sha256: row.content_sha256
    })) });
  }
};
