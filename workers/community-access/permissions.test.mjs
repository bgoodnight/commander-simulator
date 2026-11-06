import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.mjs";
import { canEditDeck, canReadDeck, resolveAccount } from "./permissions.mjs";

const env = { ENABLE_COMMUNITY_ACCESS: "true", ACCESS_OWNER_EMAILS: " OWNER@example.test " };
const context = (email, id = email) => ({ access: { getIdentity: async () => ({ email, id }) } });
const req = (path, method = "GET", body) => new Request("https://example.test" + path, {
  method, ...(body ? { headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : {})
});
const rows = [
  { id: "magnus_premium", label: "Magnus the Red", visibility: "community", owner_id: "site-owner" },
  { id: "mortarion_current", label: "Mortarion", visibility: "community", owner_id: "site-owner" },
  { id: "my_private_deck", label: "Private deck", visibility: "private", owner_id: "access:owner@example.test" },
  { id: "friend_private", label: "Friend's deck", visibility: "private", owner_id: "access:friend@example.test" }
];
function database() {
  const records = rows.map(x => ({ ...x }));
  return {
    records,
    prepare(sql) {
      const args = [];
      return {
        bind(...values) { args.push(...values); return this; },
        async first() { return records.find(r => r.id === args[0]) || null; },
        async all() {
          if (sql.includes("WHERE visibility = 'community' ORDER")) {
            return { results: records.filter(r => r.visibility === "community") };
          }
          return { results: records.filter(r => r.visibility === "community" || r.owner_id === args[0] || (r.owner_id === "site-owner" && args[1] === "owner")) };
        },
        async run() {
          const r = records.find(r => r.id === args[1] && r.owner_id === args[2]);
          if (!r) return { meta: { changes: 0 } };
          r.visibility = args[0];
          return { meta: { changes: 1 } };
        }
      };
    }
  };
}
test("owner identity normalization and stable subject", () => {
  const account = resolveAccount({ email: "OWNER@EXAMPLE.test", id: "a123", role: "owner" }, env);
  assert.deepEqual(account, { email: "owner@example.test", subject: "access:a123", role: "owner" });
  assert.equal(resolveAccount({ email: "friend@example.test", role: "owner" }, env).role, "member");
  assert.equal(resolveAccount({}, env), null);
});
test("private deck access is owner-only; site community decks editable only by site owner", () => {
  const owner = resolveAccount({ email: "owner@example.test", id: "owner@example.test" }, env);
  const friend = resolveAccount({ email: "friend@example.test", id: "friend@example.test" }, env);
  assert.equal(canReadDeck(friend, rows[2]), false);
  assert.equal(canReadDeck(owner, rows[2]), true);
  assert.equal(canEditDeck(friend, rows[0]), false);
  assert.equal(canEditDeck(owner, rows[0]), true);
});
test("fail closed without Access or database", async () => {
  assert.equal((await worker.fetch(req("/v1/decks/community"), env, {})).status, 403);
  assert.equal((await worker.fetch(req("/v1/decks/community"), env, context("friend@example.test"))).status, 503);
  assert.equal((await worker.fetch(req("/v1/decks/community"), { ...env, ENABLE_COMMUNITY_ACCESS: "false" }, context("owner@example.test"))).status, 403);
});
test("visibility toggles are persistent, and immediately change account lists", async () => {
  const db = database(), e = { ...env, COMMUNITY_DB: db };
  const friend = context("friend@example.test"), owner = context("owner@example.test");
  let r = await worker.fetch(req("/v1/decks/community"), e, friend);
  assert.deepEqual((await r.json()).decks.map(d => d.id), ["magnus_premium", "mortarion_current"]);
  r = await worker.fetch(req("/v1/decks/magnus_premium/visibility", "PATCH", { visibility: "private" }), e, friend);
  assert.equal(r.status, 404);
  r = await worker.fetch(req("/v1/decks/magnus_premium/visibility", "PATCH", { visibility: "private" }), e, owner);
  assert.equal(r.status, 200);
  r = await worker.fetch(req("/v1/decks/community"), e, friend);
  assert.deepEqual((await r.json()).decks.map(d => d.id), ["mortarion_current"]);
  r = await worker.fetch(req("/v1/decks"), e, owner);
  const decks = (await r.json()).decks;
  assert.equal(decks.find(d => d.id === "magnus_premium").can_edit, true);
  assert.equal(decks.find(d => d.id === "friend_private"), undefined);
  r = await worker.fetch(req("/v1/decks/magnus_premium/visibility", "PATCH", { visibility: "community" }), e, owner);
  assert.equal(r.status, 200);
  r = await worker.fetch(req("/v1/decks/community"), e, friend);
  assert.equal((await r.json()).decks.length, 2);
});
test("validate payload and prevent ownership spoofing", async () => {
  const e = { ...env, COMMUNITY_DB: database() };
  for (const visibility of ["public", null, true]) {
    const r = await worker.fetch(req("/v1/decks/magnus_premium/visibility", "PATCH", { visibility }), e, context("owner@example.test"));
    assert.equal(r.status, 400);
  }
  const forged = await worker.fetch(req("/v1/decks/magnus_premium/visibility", "PATCH", { visibility: "private", owner_id: "site-owner" }), e, context("owner@example.test"));
  assert.equal(forged.status, 400);
  const r = await worker.fetch(req("/v1/decks/my_private_deck/visibility", "PATCH", { visibility: "community" }), e, context("friend@example.test"));
  assert.equal(r.status, 404);
});
test("simulations remain disabled even for owner", async () => {
  const r = await worker.fetch(req("/v1/simulations", "POST"), env, context("owner@example.test"));
  assert.equal(r.status, 501);
});
