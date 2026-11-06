import { canEditDeck } from "./permissions.mjs";
import { canManagePublication } from "./publications.mjs";

export class ApiError extends Error {
  constructor(status, code) { super(code); this.status = status; this.code = code; }
}
const err = (s,c) => { throw new ApiError(s,c); };
const token = () => crypto.randomUUID();
const MAX_BYTES = 100_000;
const enc = new TextEncoder();
export const sha256 = async text =>
  Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",enc.encode(text))))
    .map(b=>b.toString(16).padStart(2,"0")).join("");
const validId = id => typeof id === "string" && /^[a-zA-Z0-9_-]{1,100}$/.test(id);
function requireOwner(account) {
  if (!account?.subject) err(403,"stable_identity_required");
}
function validateDraft(body) {
  if (!body || typeof body !== "object" || Array.isArray(body) ||
      Object.keys(body).sort().join(",") !== "decklist,label" ||
      typeof body.label !== "string" || !body.label.trim() ||
      body.label.length > 120 || typeof body.decklist !== "string" ||
      !body.decklist.trim() || enc.encode(body.decklist).length > MAX_BYTES) {
    err(400,"invalid_deck");
  }
  return { label: body.label.trim(), decklist: body.decklist };
}
export async function storeContent(bucket, text) {
  if (!bucket) err(503,"private_storage_not_configured");
  const hash = await sha256(text);
  const key = "account-decks/objects/sha256/" + hash + ".txt";
  const existing = await bucket.head(key);
  if (!existing) await bucket.put(key,text,{httpMetadata:{contentType:"text/plain; charset=utf-8"}});
  // Require a readback before changing any database pointer.
  if (await readContent(bucket,key,hash) !== text) err(503,"r2_readback_mismatch");
  return { key, hash };
}
export async function readContent(bucket,key,expected) {
  if (!bucket || typeof key !== "string" || !key.startsWith("account-decks/objects/sha256/"))
    err(503,"invalid_storage_key");
  const object = await bucket.get(key);
  if (!object) err(503,"r2_object_missing");
  const text = await object.text();
  if (await sha256(text) !== expected) err(503,"r2_hash_mismatch");
  return text;
}
const selectDeck = (db,id) => db.prepare(
  "SELECT id,label,owner_id,private_content_key,content_sha256,revision FROM decks WHERE id=?"
).bind(id).first();
const selectPublication = (db,id) => db.prepare(
  "SELECT id,label,owner_id,source_deck_id,status,current_revision_id FROM publications WHERE id=?"
).bind(id).first();
const selectRevision = (db,id) => db.prepare(
  "SELECT id,publication_id,revision_no,content_sha256,immutable_content_key FROM publication_revisions WHERE id=?"
).bind(id).first();
function ownDeck(account,deck) {
  if (!deck || !canEditDeck(account,deck)) err(404,"deck_not_found");
}
function ownPublication(account,pub) {
  if (!pub || !canManagePublication(account,pub)) err(404,"publication_not_found");
}
const draftView = d => ({id:d.id,label:d.label,revision:d.revision,content_sha256:d.content_sha256});
const listingView = (p,r) => ({
  id:p.id,label:p.label,current_revision_id:r.id,
  revision_no:r.revision_no,content_sha256:r.content_sha256
});
export async function createDeck(env,account,body) {
  requireOwner(account);
  const {label,decklist}=validateDraft(body);
  const blob=await storeContent(env.COMMUNITY_DECKS_R2,decklist);
  const id=token();
  await env.COMMUNITY_DB.prepare(
    "INSERT INTO decks(id,owner_id,label,private_content_key,content_sha256,revision) VALUES(?,?,?,?,?,1)"
  ).bind(id,account.subject,label,blob.key,blob.hash).run();
  return {id,label,revision:1,content_sha256:blob.hash};
}
export async function getPrivateDeck(env,account,id) {
  requireOwner(account);
  const d=await selectDeck(env.COMMUNITY_DB,id);
  ownDeck(account,d);
  return {...draftView(d),decklist:await readContent(env.COMMUNITY_DECKS_R2,d.private_content_key,d.content_sha256)};
}
export async function updateDeck(env,account,id,body) {
  requireOwner(account);
  if (!body || !Number.isSafeInteger(body.expected_revision) || body.expected_revision<1)
    err(400,"expected_revision_required");
  const {label,decklist}=validateDraft({label:body.label,decklist:body.decklist});
  if(Object.keys(body).sort().join(",")!=="decklist,expected_revision,label")
    err(400,"invalid_deck");
  const d=await selectDeck(env.COMMUNITY_DB,id);
  ownDeck(account,d);
  if (d.revision!==body.expected_revision) err(409,"stale_deck_revision");
  const blob=await storeContent(env.COMMUNITY_DECKS_R2,decklist);
  const updated=await env.COMMUNITY_DB.prepare(
    "UPDATE decks SET label=?,private_content_key=?,content_sha256=?,revision=revision+1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND owner_id=? AND revision=?"
  ).bind(label,blob.key,blob.hash,id,account.subject,body.expected_revision).run();
  if (updated.meta?.changes!==1) err(409,"stale_deck_revision");
  return {id,label,revision:body.expected_revision+1,content_sha256:blob.hash};
}
export async function listPrivateDecks(env,account) {
  requireOwner(account);
  const rows=await env.COMMUNITY_DB.prepare(
    "SELECT id,label,revision,content_sha256 FROM decks WHERE owner_id=? ORDER BY label"
  ).bind(account.subject).all();
  return rows.results.map(draftView);
}
export async function publishDeck(env,account,id) {
  requireOwner(account);
  const d=await selectDeck(env.COMMUNITY_DB,id);
  ownDeck(account,d);
  // Verify the source content still matches its immutable hash before publishing.
  await readContent(env.COMMUNITY_DECKS_R2,d.private_content_key,d.content_sha256);
  const publicationId=token(),revisionId=token();
  const statements=[
    env.COMMUNITY_DB.prepare(
      "INSERT INTO publications(id,owner_id,source_deck_id,label,status,current_revision_id) VALUES(?,?,?,?,'listed',?)"
    ).bind(publicationId,account.subject,d.id,d.label,revisionId),
    env.COMMUNITY_DB.prepare(
      "INSERT INTO publication_revisions(id,publication_id,revision_no,content_sha256,immutable_content_key,source_deck_revision) VALUES(?,?,1,?,?,?)"
    ).bind(revisionId,publicationId,d.content_sha256,d.private_content_key,String(d.revision))
  ];
  await env.COMMUNITY_DB.batch(statements);
  return {id:publicationId,current_revision_id:revisionId,revision_no:1,content_sha256:d.content_sha256};
}
export async function replacePublication(env,account,id,body) {
  requireOwner(account);
  if (!body || Object.keys(body).sort().join(",")!=="expected_revision_id,source_deck_id" ||
      !validId(body.expected_revision_id) || !validId(body.source_deck_id))
    err(400,"invalid_replace_request");
  const pub=await selectPublication(env.COMMUNITY_DB,id);
  ownPublication(account,pub);
  if(pub.status!=="listed") err(409,"publication_unlisted");
  if(pub.current_revision_id!==body.expected_revision_id) err(409,"stale_publication_revision");
  const deck=await selectDeck(env.COMMUNITY_DB,body.source_deck_id);
  ownDeck(account,deck);
  const previous=await selectRevision(env.COMMUNITY_DB,pub.current_revision_id);
  if(!previous) err(503,"missing_publication_revision");
  await readContent(env.COMMUNITY_DECKS_R2,deck.private_content_key,deck.content_sha256);
  const rev=token(),number=previous.revision_no+1;
  // Batch is transactional. Insertion is conditional on current pointer to avoid
  // writing an orphan revision after another replacement wins the race.
  const inserted=env.COMMUNITY_DB.prepare(
    "INSERT INTO publication_revisions(id,publication_id,revision_no,content_sha256,immutable_content_key,source_deck_revision) SELECT ?,id,?,?,?,? FROM publications WHERE id=? AND owner_id=? AND status='listed' AND current_revision_id=?"
  ).bind(rev,number,deck.content_sha256,deck.private_content_key,String(deck.revision),
    id,pub.owner_id,body.expected_revision_id);
  const updated=env.COMMUNITY_DB.prepare(
    "UPDATE publications SET current_revision_id=?,source_deck_id=?,label=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND owner_id=? AND status='listed' AND current_revision_id=?"
  ).bind(rev,deck.id,deck.label,id,pub.owner_id,body.expected_revision_id);
  const results=await env.COMMUNITY_DB.batch([inserted,updated]);
  if(results[0].meta?.changes!==1||results[1].meta?.changes!==1)
    err(409,"stale_publication_revision");
  return {id,current_revision_id:rev,revision_no:number,content_sha256:deck.content_sha256};
}
export async function unpublish(env,account,id) {
  requireOwner(account);
  const pub=await selectPublication(env.COMMUNITY_DB,id);
  ownPublication(account,pub);
  if(pub.status==="unlisted")return {id,status:"unlisted"};
  const result=await env.COMMUNITY_DB.prepare(
    "UPDATE publications SET status='unlisted',updated_at=CURRENT_TIMESTAMP WHERE id=? AND owner_id=? AND status='listed'"
  ).bind(id,pub.owner_id).run();
  if(result.meta?.changes!==1)err(409,"publication_changed");
  return {id,status:"unlisted"};
}
export async function getListedPublication(env,id) {
  const pub=await selectPublication(env.COMMUNITY_DB,id);
  if(!pub||pub.status!=="listed")err(404,"publication_not_found");
  const rev=await selectRevision(env.COMMUNITY_DB,pub.current_revision_id);
  if(!rev||rev.publication_id!==pub.id)err(503,"missing_publication_revision");
  const decklist=await readContent(env.COMMUNITY_DECKS_R2,rev.immutable_content_key,rev.content_sha256);
  return {...listingView(pub,rev),decklist};
}
export async function listPublications(env) {
  const rows=await env.COMMUNITY_DB.prepare(
    "SELECT p.id,p.label,r.id AS current_revision_id,r.revision_no,r.content_sha256 FROM publications p JOIN publication_revisions r ON r.id=p.current_revision_id WHERE p.status='listed' ORDER BY p.label"
  ).all();
  return rows.results.map(x=>({
    id:x.id,label:x.label,current_revision_id:x.current_revision_id,
    revision_no:x.revision_no,content_sha256:x.content_sha256
  }));
}
export async function copyPublication(env,account,id) {
  requireOwner(account);
  // Readlisted again and revalidate at operation time; copies become independent.
  const pub=await getListedPublication(env,id);
  return createDeck(env,account,{label:pub.label,decklist:pub.decklist});
}
