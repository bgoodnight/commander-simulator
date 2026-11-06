// Pure authorization helpers. Never trust roles, deck ownership or email from the browser.
export const COMMUNITY_DECKS = Object.freeze([
  Object.freeze({ id: "mortarion_current", label: "Mortarion", visibility: "community" }),
  Object.freeze({ id: "magnus_premium", label: "Magnus the Red", visibility: "community" }),
]);
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
  return Object.freeze({ email, role: owners.has(email) ? "owner" : "member" });
}
export function canRunSimulations(account) {
  return account?.role === "owner";
}
export function canReadDeck(account, deck) {
  if (!deck || !["community", "private"].includes(deck.visibility)) return false;
  if (deck.visibility === "community") return true;
  return Boolean(account && normalizeEmail(deck.owner_email) === account.email);
}
export function canEditDeck(account, deck) {
  return Boolean(account && deck && normalizeEmail(deck.owner_email) === account.email);
}
