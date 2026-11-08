// Authorization is enforced server-side, never by UI visibility alone.
export function normalizeEmail(value) {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}
export function ownerEmails(raw) {
  return new Set(String(raw ?? "").split(",").map(normalizeEmail).filter(Boolean));
}
export function resolveAccount(identity, env) {
  const email = normalizeEmail(identity?.email);
  if (!email) return null;
  const owners = ownerEmails(env.ACCESS_OWNER_EMAILS);
  const role = owners.has(email) ? "owner" : "member";
  // Cloudflare Access's stable identity id is needed for personal deck ownership.
  // Don't silently use a mutable email address as a persistent identity key.
  const subject = typeof identity?.id === "string" && identity.id.trim()
    ? "access:" + identity.id.trim() : null;
  return Object.freeze({ email, subject, role });
}
export function canRunSimulations(account) {
  return account?.role === "owner";
}
export function canReadDeck(account, deck) {
  if (!deck || !["community", "private"].includes(deck.visibility)) return false;
  if (deck.visibility === "community") return Boolean(account);
  return canEditDeck(account, deck);
}
export function canEditDeck(account, deck) {
  if (!account || !deck) return false;
  if (deck.owner_id === "site-owner") return account.role === "owner";
  return Boolean(account.subject && deck.owner_id === account.subject);
}
export function isValidVisibility(value) {
  return value === "private" || value === "community";
}
