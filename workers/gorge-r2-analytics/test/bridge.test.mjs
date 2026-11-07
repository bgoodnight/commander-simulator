import test from "node:test";
import assert from "node:assert/strict";
import worker from "../index.mjs";

const token="a".repeat(48);
const key="native/experimental/legacy/v1/test.tar.gz";
const body="raw omniscient data";
const objects=[{key,size:body.length},{key:"warehouse/v1/legacy/hero/0/manifest.json",size:12}];
const env={ANALYTICS_READ_TOKEN:token,GORGE_R2:{
  list:async ({prefix,cursor})=>({objects:objects.filter(o=>o.key.startsWith(prefix)),truncated:false}),
  head:async k=>objects.find(o=>o.key===k)||null,
  get:async (k,options)=>{
    if(k!==key)return null;
    const {offset=0,length=body.length}=options?.range||{};
    return {body:new Blob([body.slice(offset,offset+length)]).stream()};
  }
}};
const req=(path,opts={})=>new Request("https://analytics.example.test"+path,opts);
const auth={authorization:"Bearer "+token};

test("unauthenticated requests cannot list or read omniscient traces",async()=>{
  assert.equal((await worker.fetch(req("/v1/analytics/inventory"),env)).status,401);
  assert.equal((await worker.fetch(req("/v1/analytics/object?key="+encodeURIComponent(key)),env)).status,401);
});
test("fails closed without secret",async()=>{
  assert.equal((await worker.fetch(req("/v1/analytics/inventory",{headers:auth}),{GORGE_R2:env.GORGE_R2})).status,401);
});
test("all-prefix inventory includes raw legacy recordings and has no public CORS",async()=>{
  const res=await worker.fetch(req("/v1/analytics/inventory",{headers:auth}),env);
  assert.equal(res.status,200);
  const data=await res.json();
  assert.equal(data.objects.length,2);
  assert.equal(data.objects[0].key,key);
  assert.equal(res.headers.get("access-control-allow-origin"),null);
});
test("authorized original raw content and exact range",async()=>{
  const path="/v1/analytics/object?key="+encodeURIComponent(key);
  let res=await worker.fetch(req(path,{headers:auth}),env);
  assert.equal(res.status,200);
  assert.equal(await res.text(),body);
  res=await worker.fetch(req(path,{headers:{...auth,range:"bytes=4-12"}}),env);
  assert.equal(res.status,206);
  assert.equal(res.headers.get("content-range"),"bytes 4-12/"+body.length);
  assert.equal(await res.text(),body.slice(4,13));
});
test("rejects invalid key, mutation and impossible ranges",async()=>{
  const path="/v1/analytics/object?key="+encodeURIComponent(key);
  assert.equal((await worker.fetch(req("/v1/analytics/object?key=../secret",{headers:auth}),env)).status,400);
  assert.equal((await worker.fetch(req(path,{method:"POST",headers:auth}),env)).status,405);
  assert.equal((await worker.fetch(req(path,{headers:{...auth,range:"bytes=8-9999"}}),env)).status,416);
});
test("oversized objects are available through bounded 206 streaming",async()=>{
  const huge={...env,GORGE_R2:{...env.GORGE_R2,head:async()=>({size:40*1024*1024})}};
  const res=await worker.fetch(req("/v1/analytics/object?key="+encodeURIComponent(key),{headers:auth}),huge);
  assert.equal(res.status,206);
  assert.equal(res.headers.get("content-range"),"bytes 0-16777215/41943040");
});
