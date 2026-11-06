// Store invitation requests, not credentials or implicit access grants.
import { ApiError } from "./store.mjs";
import { normalizeEmail } from "./permissions.mjs";
const error=(status,code)=>{throw new ApiError(status,code)};
export function validateRequest(body) {
  if(!body || typeof body!=="object" || Array.isArray(body) ||
     Object.keys(body).some(k=>!["email","display_name","note"].includes(k)))
    error(400,"invalid_request");
  const email=normalizeEmail(body.email);
  if(email.length>254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    error(400,"invalid_email");
  const display_name=typeof body.display_name==="string" ? body.display_name.trim() : "";
  const note=typeof body.note==="string" ? body.note.trim() : "";
  if(display_name.length>80 || note.length>500)error(400,"invalid_request");
  return {email,display_name,note};
}
export async function submitInvitation(db,body){
  if(!db)error(503,"request_store_unavailable");
  const data=validateRequest(body);
  // Idempotent: do not reveal existence or current status of an email to the caller.
  await db.prepare(
    "INSERT OR IGNORE INTO invitation_requests(id,email,display_name,note) VALUES(?,?,?,?)"
  ).bind(crypto.randomUUID(),data.email,data.display_name,data.note).run();
  return {received:true};
}
function ensureAdmin(account){
  if(account?.role!=="owner" || !account.subject)error(403,"forbidden");
}
export async function listInvitations(db,account){
  ensureAdmin(account);
  if(!db)error(503,"request_store_unavailable");
  const rows=await db.prepare(
    "SELECT id,email,display_name,note,status,created_at,reviewed_at FROM invitation_requests ORDER BY created_at DESC LIMIT 200"
  ).all();
  return rows.results;
}
export async function reviewInvitation(db,account,id,status){
  ensureAdmin(account);
  if(!db)error(503,"request_store_unavailable");
  if(!["declined","awaiting_access_allowlist"].includes(status))
    error(400,"invalid_review_status");
  if(!/^[a-z0-9-]{36}$/.test(id))error(404,"request_not_found");
  const result=await db.prepare(
    "UPDATE invitation_requests SET status=?,reviewed_by=?,reviewed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'"
  ).bind(status,account.subject,id).run();
  if(result.meta?.changes!==1)error(409,"not_pending");
  // IMPORTANT: awaiting_access_allowlist is not approved access. Admin must
  // add the email in the Cloudflare Access policy out of band.
  return {id,status,cloudflare_allowlist_updated:false};
}
