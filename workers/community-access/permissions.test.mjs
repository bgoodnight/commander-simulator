import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.mjs";
import { resolveAccount, canEditDeck } from "./permissions.mjs";
import { canManagePublication, planPublish, planReplace, planUnpublish } from "./publications.mjs";
const env = { ENABLE_COMMUNITY_ACCESS: "true", ACCESS_OWNER_EMAILS: "OWNER@example.test" };
const context = (email, id = email) => ({ access: { getIdentity: async () => ({ email, id }) } });
const req = (path, method = "GET", origin) => new Request("https://example.test" + path, {
  method, ...(origin ? { headers: { origin } } : {})
});
const owner = resolveAccount({ email: "owner@example.test", id: "person-a" }, env);
const friend = resolveAccount({ email: "friend@example.test", id: "person-b" }, env);
const contentSha256 = "a".repeat(64);
test("untrusted browser role cannot grant access", () => {
  assert.equal(owner.role, "owner");
  assert.equal(resolveAccount({ email: friend.email, role: "owner" }, env).role, "member");
  assert.equal(canEditDeck(friend, { owner_id: owner.subject }), false);
});
test("publication is an independent content-addressed snapshot", () => {
  const deck = { id: "magnus-draft", owner_id: owner.subject, label: "Magnus" };
  const planned = planPublish({ deck, account: owner, contentSha256 });
  assert.equal(planned.source_deck_id, deck.id);
  assert.equal(planned.revision_no, 1);
  assert.equal(planned.content_sha256, contentSha256);
  assert.equal(deck.visibility, undefined);
  assert.throws(() => planPublish({ deck, account: friend, contentSha256 }), /forbidden/);
  assert.throws(() => planPublish({ deck, account: owner, contentSha256: "unverified" }), /unverified/);
});
test("replace creates a revision, never changes prior revision", () => {
  const publication = Object.freeze({ id: "pub1", owner_id: owner.subject, current_revision_id: "rev1" });
  const initial = Object.freeze({ id: "rev1", revision_no: 1, content_sha256: contentSha256 });
  const next = planReplace({ publication, account: owner, contentSha256: "b".repeat(64), nextRevisionNo: 2 });
  assert.equal(next.revision_no, 2);
  assert.equal(initial.content_sha256, contentSha256);
  assert.equal(publication.current_revision_id, "rev1");
  assert.throws(() => planReplace({ publication, account: friend, contentSha256, nextRevisionNo: 2 }), /forbidden/);
});
test("unpublish hides discovery while preserving revisions and historical evidence", () => {
  const publication = { id: "pub1", owner_id: owner.subject, status: "listed" };
  const plan = planUnpublish({ publication, account: owner });
  assert.equal(plan.status, "unlisted");
  assert.equal(plan.preserve_revisions, true);
  assert.equal(plan.preserve_simulation_references, true);
  assert.equal(publication.status, "listed");
  assert.throws(() => planUnpublish({ publication, account: friend }), /forbidden/);
  assert.equal(canManagePublication(friend, publication), false);
});
test("Access and DB missing fail closed", async () => {
  assert.equal((await worker.fetch(req("/v1/publications"), env, {})).status, 403);
  assert.equal((await worker.fetch(req("/v1/publications"), env, context(friend.email))).status, 503);
  assert.equal((await worker.fetch(req("/v1/publications"), { ...env, ENABLE_COMMUNITY_ACCESS: "false" }, context(owner.email))).status, 403);
});
test("public listing includes only listed immutable snapshot metadata", async () => {
  const db = { prepare: () => ({ all: async () => ({
    results: [{ id: "pub1", label: "Magnus", owner_id: owner.subject,
      current_revision_id: "rev2", content_sha256: "b".repeat(64) }]
  }) }) };
  const response = await worker.fetch(req("/v1/publications"), { ...env, COMMUNITY_DB: db }, context(friend.email));
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.deepEqual(body.publications, [{
    id: "pub1", label: "Magnus", current_revision_id: "rev2", content_sha256: "b".repeat(64)
  }]);
});
test("all snapshot writes disabled, old toggles retired, simulations disabled", async () => {
  const e = { ...env, COMMUNITY_DB: {} };
  assert.equal((await worker.fetch(req("/v1/decks/magnus/visibility", "PATCH"), e, context(owner.email))).status, 410);
  assert.equal((await worker.fetch(req("/v1/decks/magnus/publications", "POST", "https://example.test"), e, context(owner.email))).status, 501);
  assert.equal((await worker.fetch(req("/v1/publications/pub1/replace", "POST", "https://example.test"), e, context(owner.email))).status, 501);
  assert.equal((await worker.fetch(req("/v1/publications/pub1/unpublish", "POST", "https://evil.test"), e, context(owner.email))).status, 403);
  assert.equal((await worker.fetch(req("/v1/simulations", "POST"), e, context(owner.email))).status, 501);
  assert.equal((await worker.fetch(req("/v1/simulations", "POST"), e, context(friend.email))).status, 403);
});
