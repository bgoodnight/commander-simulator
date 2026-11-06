import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.mjs";
import { canEditDeck, canReadDeck, resolveAccount } from "./permissions.mjs";

const owner = { email: "owner@example.test", role: "owner" };
const member = { email: "friend@example.test", role: "member" };
const req = (path, method = "GET") => new Request("https://example.test" + path, { method });
const env = { ENABLE_COMMUNITY_ACCESS: "true", ACCESS_OWNER_EMAILS: " OWNER@example.test " };
const context = (email) => ({ access: { getIdentity: async () => ({ email }) } });
test("owner matching is exact and normalized, never supplied by client", () => {
  assert.equal(resolveAccount({ email: "owner@EXAMPLE.test" }, env).role, "owner");
  assert.equal(resolveAccount({ email: "friend@example.test", role: "owner" }, env).role, "member");
  assert.equal(resolveAccount({}, env), null);
});
test("private decks require matching ownership, community decks remain shared", () => {
  const privateDeck = { visibility: "private", owner_email: owner.email };
  const community = { visibility: "community" };
  assert.equal(canReadDeck(member, privateDeck), false);
  assert.equal(canReadDeck(owner, privateDeck), true);
  assert.equal(canReadDeck(member, community), true);
  assert.equal(canEditDeck(member, privateDeck), false);
});
test("missing verified Access context and disabled deployments fail closed", async () => {
  assert.equal((await worker.fetch(req("/v1/account/me"), env, {})).status, 403);
  assert.equal((await worker.fetch(req("/v1/account/me"), { ...env, ENABLE_COMMUNITY_ACCESS: "false" }, context(owner.email))).status, 403);
  assert.equal((await worker.fetch(req("/v1/account/me"), env, context(""))).status, 403);
});
test("friends can view community decks, cannot dispatch simulations", async () => {
  const me = await worker.fetch(req("/v1/account/me"), env, context(member.email));
  assert.equal((await me.json()).permissions.run_simulations, false);
  const decks = await worker.fetch(req("/v1/decks/community"), env, context(member.email));
  assert.deepEqual((await decks.json()).decks.map(d => d.id), ["mortarion_current", "magnus_premium"]);
  assert.equal((await worker.fetch(req("/v1/simulations", "POST"), env, context(member.email))).status, 403);
});
test("owner dispatch intentionally remains unimplemented", async () => {
  const r = await worker.fetch(req("/v1/simulations", "POST"), env, context(owner.email));
  assert.equal(r.status, 501);
  assert.equal(r.headers.get("cache-control"), "private, no-store");
});
