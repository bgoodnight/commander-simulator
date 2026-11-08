// Pure, side-effect-free publication lifecycle rules.
// Storage, Access verification and transactions are separate required gates.
export function canManagePublication(account, publication) {
  if (!account || !publication) return false;
  if (publication.owner_id === "site-owner") return account.role === "owner";
  return Boolean(account.subject && account.subject === publication.owner_id);
}
export function planPublish({ deck, account, contentSha256 }) {
  if (!deck || !account || !account.subject || deck.owner_id !== account.subject) {
    throw new Error("forbidden");
  }
  if (!/^[0-9a-f]{64}$/.test(contentSha256 || "")) throw new Error("unverified_content");
  return Object.freeze({
    source_deck_id: deck.id,
    owner_id: deck.owner_id,
    revision_no: 1,
    content_sha256: contentSha256,
    status: "listed"
  });
}
export function planReplace({ publication, account, contentSha256, nextRevisionNo }) {
  if (!canManagePublication(account, publication)) throw new Error("forbidden");
  if (!/^[0-9a-f]{64}$/.test(contentSha256 || "")) throw new Error("unverified_content");
  if (!Number.isSafeInteger(nextRevisionNo) || nextRevisionNo < 2) throw new Error("invalid_revision");
  return Object.freeze({
    publication_id: publication.id, revision_no: nextRevisionNo,
    content_sha256: contentSha256, status: "listed"
  });
}
export function planUnpublish({ publication, account }) {
  if (!canManagePublication(account, publication)) throw new Error("forbidden");
  return Object.freeze({ publication_id: publication.id, status: "unlisted",
    preserve_revisions: true, preserve_simulation_references: true });
}
