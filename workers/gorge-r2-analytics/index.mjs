// Private, read-only R2 evidence bridge. No cohort approval or public UI filters.
// This bucket is dedicated to Gorge; preserve legacy and unforeseen object families.
const MAX_PAGE = 500;
const MAX_RANGE = 16 * 1024 * 1024;
const enc = new TextEncoder();
const respond = (body, status=200, extra={}) => new Response(JSON.stringify(body), {status, headers: {
  "content-type":"application/json", "cache-control":"no-store", "x-content-type-options":"nosniff",
  "referrer-policy":"no-referrer", ...extra
}});
const validKey = key => typeof key === "string" && key.length > 0 && key.length < 1024 &&
  !key.includes("\\") &&
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
      const prefix = url.searchParams.get("prefix") ?? "";
      if(prefix.length > 1024 || /[\\x00-\\x1f\\x7f]/.test(prefix) || prefix.includes(".."))
        return respond({error:"invalid_prefix"},400);
      const cursor = url.searchParams.get("cursor") || undefined;
      if(cursor && cursor.length > 2048) return respond({error:"invalid_cursor"},400);
      const listed = await env.GORGE_R2.list({prefix, limit:MAX_PAGE,...(cursor ? {cursor}:{})});
      return respond({schema:"gorge-analytics-r2-list-v1",prefix,
        objects:listed.objects.map(o=>({key:o.key,bytes:o.size,uploaded:o.uploaded?.toISOString?.() ?? null,
          etag:o.httpEtag ?? null})),truncated:listed.truncated,cursor:listed.truncated?listed.cursor:null});
    }
    if(url.pathname === "/v1/analytics/object") {
      const key = url.searchParams.get("key");
      if(!validKey(key)) return respond({error:"invalid_key"},400);
      const info = await env.GORGE_R2.head(key);
      if(!info) return respond({error:"not_found"},404);
      const rangeHeader = request.headers.get("range");
      let offset = 0, length = Math.min(info.size, MAX_RANGE), partial = info.size > MAX_RANGE;
      if(rangeHeader) {
        const match = /^bytes=(\\d+)-(\\d+)$/.exec(rangeHeader);
        if(!match) return respond({error:"invalid_range"},416);
        const start = Number(match[1]), end = Number(match[2]);
        if(!Number.isSafeInteger(start) || !Number.isSafeInteger(end) ||
           start > end || end >= info.size || end-start+1 > MAX_RANGE)
          return respond({error:"invalid_range"},416);
        offset=start; length=end-start+1; partial=true;
      }
      const headers = new Headers({"content-type":"application/octet-stream","cache-control":"no-store",
        "x-content-type-options":"nosniff","content-disposition":"attachment",
        "accept-ranges":"bytes","content-length":String(length),
        "x-gorge-object-bytes":String(info.size)});
      if(partial) headers.set("content-range",`bytes ${offset}-${offset+length-1}/${info.size}`);
      const status = partial ? 206 : 200;
      if(request.method === "HEAD") return new Response(null,{status,headers});
      const object = await env.GORGE_R2.get(key,{range:{offset,length}});
      if(!object) return respond({error:"not_found"},404);
      return new Response(object.body,{status,headers});
    }
    return respond({error:"not_found"},404);
  }
};
