import { resolveAccount, canRunSimulations, canReadDeck, canEditDeck, isValidVisibility } from "./permissions.mjs";

// Standalone Cloudflare Access proof of integration; does not dispatch simulations,
// mutate R2, or alter the production GitHub Pages application.
const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "private, no-store",
    "x-content-type-options": "nosniff",
    "vary": "Cookie"
  },
});
const publicFields = row => ({ id: row.id, label: row.label, visibility: row.visibility });
const ownFields = row => ({ ...publicFields(row), owner_id: row.owner_id });
const getDeck = (db, id) => db.prepare(
  "SELECT id, label, visibility, owner_id FROM decks WHERE id = ?"
).bind(id).first();

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (!["GET", "POST", "PATCH"].includes(request.method)) return json({ error: "method_not_allowed" }, 405);
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
      if (!canRunSimulations(account)) return json({ error: "forbidden" }, 403);
      return json({ error: "simulation_dispatch_not_implemented" }, 501);
    }
    const isList = request.method === "GET" && ["/v1/decks", "/v1/decks/community"].includes(url.pathname);
    const match = url.pathname.match(/^\/v1\/decks\/([a-zA-Z0-9_-]{1,100})\/visibility$/);
    if (!isList && !(request.method === "PATCH" && match)) return json({ error: "not_found" }, 404);
    if (!env.COMMUNITY_DB) return json({ error: "deck_store_not_configured" }, 503);

    if (isList) {
      // Community rows are visible to invited users. Private deck rows are returned
      // only for their owner, with no information about other users' private decks.
      if (url.pathname === "/v1/decks/community") {
        const rows = await env.COMMUNITY_DB.prepare(
          "SELECT id, label, visibility, owner_id FROM decks WHERE visibility = 'community' ORDER BY label"
        ).all();
        return json({ decks: rows.results.map(publicFields) });
      }
      const rows = await env.COMMUNITY_DB.prepare(
        "SELECT id, label, visibility, owner_id FROM decks WHERE visibility = 'community' OR owner_id = ? OR (owner_id = 'site-owner' AND ? = 'owner') ORDER BY label"
      ).bind(account.subject || "", account.role).all();
      return json({ decks: rows.results.map(row => ({
        ...publicFields(row), can_edit: canEditDeck(account, row)
      })) });
    }
    // Cookie-authenticated writes require a same-origin browser request.
    // Cross-origin Pages integration needs a reviewed CSRF/session design first.
    if (request.headers.get("origin") !== url.origin) return json({ error: "origin_forbidden" }, 403);
    const deckId = match[1];
    // Never accept owner_id, owner email, or arbitrary fields from the client.
    let body;
    try {
      if (Number(request.headers.get("content-length")) > 1024) return json({ error: "invalid_request" }, 400);
      body = await request.json();
    } catch { return json({ error: "invalid_json" }, 400); }
    if (!body || typeof body !== "object" || Array.isArray(body)
      || Object.keys(body).length !== 1 || !isValidVisibility(body.visibility)) {
      return json({ error: "invalid_visibility" }, 400);
    }
    const deck = await getDeck(env.COMMUNITY_DB, deckId);
    // Nonowners cannot discover the existence of a private deck through this API.
    if (!deck || !canEditDeck(account, deck)) return json({ error: "not_found" }, 404);
    // Conditional update avoids a stale owner/visibility change taking precedence.
    const updated = await env.COMMUNITY_DB.prepare(
      "UPDATE decks SET visibility = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND owner_id = ?"
    ).bind(body.visibility, deck.id, deck.owner_id).run();
    if (updated.meta?.changes !== 1) return json({ error: "update_conflict" }, 409);
    return json({ deck: { ...ownFields(deck), visibility: body.visibility } });
  },
};
