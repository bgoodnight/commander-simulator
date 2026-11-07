import test from "node:test";
import assert from "node:assert/strict";
import worker from "../index.mjs";
const token = "a".repeat(48);
const objects = [{key:"warehouse/v1/legacy/mortarion/0/manifest.json",size:17}];
const env = {ANALYTICS_READ_TOKEN:token,GORGE_R2:{
 list:async ({prefix})=>({objects:objects.filter(o=>o.key.startsWith(prefix)),truncated:false}),
 head:async key=>objects.find(o=>o.key===key) || null,
 get:async key=>key===objects[0].key ? {body:new Blob(["old native source"]).stream()} : null,
}};
const req=(path, opts={})=>new Request("https://analytics.example.test"+path,opts);
test("unauthenticated requests cannot list or fetch",async()=>{
 assert.equal((await worker.fetch(req("/v1/analytics/inventory?prefix=warehouse/"),env)).status,401);
 assert.equal((await worker.fetch(req("/v1/analytics/object?key="+encodeURIComponent(objects[0].key)),env)).status,401);
});
test("fail closed without configured secret",async()=>{
 assert.equal((await worker.fetch(req("/v1/analytics/inventory?prefix=warehouse/",{headers:{authorization:"Bearer "+token}}),{GORGE_R2:env.GORGE_R2})).status,401);
});
test("authorized historical inventory includes unapproved batches",async()=>{
 const res=await worker.fetch(req("/v1/analytics/inventory?prefix=warehouse/",{headers:{authorization:"Bearer "+token}}),env);
 assert.equal(res.status,200);
 assert.equal((await res.json()).objects[0].key,objects[0].key);
 assert.equal(res.headers.get("access-control-allow-origin"),null);
});
test("authorized object download returns full content",async()=>{
 const res=await worker.fetch(req("/v1/analytics/object?key="+encodeURIComponent(objects[0].key),{headers:{authorization:"Bearer "+token}}),env);
 assert.equal(res.status,200); assert.equal(await res.text(),"old native source");
});
test("restricts operations, prefix and oversized responses",async()=>{
 assert.equal((await worker.fetch(req("/v1/analytics/object?key=../secret",{headers:{authorization:"Bearer "+token}}),env)).status,400);
 assert.equal((await worker.fetch(req("/v1/analytics/inventory?prefix=anything/",{headers:{authorization:"Bearer "+token}}),env)).status,400);
 assert.equal((await worker.fetch(req("/v1/analytics/object?key="+encodeURIComponent(objects[0].key),{method:"POST",headers:{authorization:"Bearer "+token}}),env)).status,405);
 const big={...env,GORGE_R2:{...env.GORGE_R2,head:async()=>({size:40*1024*1024})}};
 assert.equal((await worker.fetch(req("/v1/analytics/object?key="+encodeURIComponent(objects[0].key),{headers:{authorization:"Bearer "+token}}),big)).status,413);
});
