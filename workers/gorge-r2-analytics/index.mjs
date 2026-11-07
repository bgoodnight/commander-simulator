// Private, read-only R2 evidence bridge. No cohort approval or public UI filters.
const ROOTS = ["warehouse/", "native/", "results/", "archives/"];
const HARD_MAX = 32 * 1024 * 1024;
const enc = new TextEncoder();
const respond = (body, status=200, extra={}) => new Response(JSON.stringify(body), {status, headers: {
  "content-type":"application/json", "cache-control":"no-store", "x-content-type-options":"nosniff",
  "referrer-policy":"no-referrer", ...extra
}});
const validKey = key => typeof key === "string" && key.length > 0 && key.length < 1024 &&
  ROOTS.some(root => key.startsWith(root)) && !key.includes("\\") &&
  !key.split("/").some(p => p === ".." || p === ".") && !/[\x00-\x1f\x7f]/.test(key);
function tokenEqual(a,b) {
  const x = enc.encode(a), y = enc.encode(b);
  let diff = x.length ^ y.length;
  for(let i=0;i<Math.max(x.length,y.length);i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}
function authorized(request, env) {
  const expected = env.ANALYTICS_READ_TOKEN;
  if(typeof expected !== "string" || expected.length < 32) return false;
  const header = request.headers.get("authorization") || "";
  return header.startsWith("Bearer ") && tokenEqual(header.slice(7), expected);
}
export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD")
      return respond({error:"method_not_allowed"},405,{allow:"GET, HEAD"});
    const url = new URL(request.url);
    if(url.pathname === "/health") return respond({status:"alive",access:"private"});
    if(!authorized(request, env)) return respond({error:"unauthorized"},401);
    if(!env.GORGE_R2) return respond({error:"bucket_unavailable"},503);
    if(url.pathname === "/v1/analytics/inventory") {
      const prefix = url.searchParams.get("prefix");
      if(!ROOTS.includes(prefix)) return respond({error:"invalid_prefix"},400);
      const cursor = url.searchParams.get("cursor") || undefined;
      if(cursor && cursor.length > 2048) return respond({error:"invalid_cursor"},400);
      const listed = await env.GORGE_R2.list({prefix, limit:500,...(cursor ? {cursor}:{})});
      return respond({schema:"gorge-analytics-r2-list-v1",prefix,
        objects:listed.objects.map(o=>({key:o.key,bytes:o.size,uploaded:o.uploaded?.toISOString?.() ?? null,
          etag:o.httpEtag ?? null})),truncated:listed.truncated,cursor:listed.truncated?listed.cursor:null});
    }
    if(url.pathname === "/v1/analytics/object") {
      const key = url.searchParams.get("key");
      if(!validKey(key)) return respond({error:"invalid_key"},400);
      const info = await env.GORGE_R2.head(key);
      if(!info) return respond({error:"not_found"},404);
      if(info.size > HARD_MAX) return respond({error:"object_too_large",bytes:info.size,max_bytes:HARD_MAX},413);
      const object = await env.GORGE_R2.get(key);
      if(!object) return respond({error:"not_found"},404);
      const headers = new Headers({"content-type":"application/octet-stream","cache-control":"no-store",
        "x-content-type-options":"nosniff","content-disposition":"attachment"});
      if(request.method === "HEAD") return new Response(null,{status:200,headers});
      return new Response(object.body,{status:200,headers});
    }
    return respond({error:"not_found"},404);
  }
};
