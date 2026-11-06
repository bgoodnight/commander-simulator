import { COMMUNITY_DECKS, resolveAccount, canRunSimulations } from "./permissions.mjs";

// Standalone proof of integration: no simulation dispatch, no R2 access, no production routes.
// Set Cloudflare Access to protect ALL traffic to this Worker; ctx.access is trusted only
// when Cloudflare has authenticated this invocation. Do not accept client-supplied roles.
const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "private, no-store",
    "x-content-type-options": "nosniff",
    "vary": "Cookie"
  },
});
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method !== "GET" && request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
    // Never run this sample as a public auth service: explicit deploy switch and
    // Cloudflare-verified identity are mandatory. Missing Access context fails closed.
    if (env.ENABLE_COMMUNITY_ACCESS !== "true" || !ctx?.access) {
      return json({ error: "access_not_configured" }, 403);
    }
    let identity;
    try { identity = await ctx.access.getIdentity(); }
    catch { return json({ error: "invalid_access_identity" }, 403); }
    const account = resolveAccount(identity, env);
    if (!account) return json({ error: "identity_required" }, 403);
    if (request.method === "GET" && url.pathname === "/v1/account/me") {
      return json({ account, permissions: { run_simulations: canRunSimulations(account) } });
    }
    if (request.method === "GET" && url.pathname === "/v1/decks/community") {
      return json({ decks: COMMUNITY_DECKS });
    }
    if (request.method === "POST" && url.pathname === "/v1/simulations") {
      if (!canRunSimulations(account)) return json({ error: "forbidden" }, 403);
      // Intentionally not dispatched until budget controls, approval & audit are designed.
      return json({ error: "simulation_dispatch_not_implemented" }, 501);
    }
    return json({ error: "not_found" }, 404);
  },
};
