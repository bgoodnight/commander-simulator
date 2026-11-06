import test from "node:test";
import assert from "node:assert/strict";
import worker from "../index.mjs";
import registry from "../../../data/gorge_analytics_cohort_registry_v1.json" with {type:"json"};
import {sha256,stableJson,IDENTITY_FIELDS} from "../core.mjs";

const deck="mortarion_current",version="c".repeat(64),uiHash="a".repeat(64);
const gid="123456-1/mortarion_current/0/123";
const base="results/materialized/v1/";
const enc=new TextEncoder();

async function fixture(){
  const store=new Map();
  function put(key,obj){
    const raw=enc.encode(JSON.stringify(obj));
    store.set(key,raw);
    return sha256(new TextDecoder().decode(raw));
  }
  const cohort=registry.cohorts.find(c=>c.deck===deck&&c.approved);
  const fingerprint=await sha256(stableJson({cohort_id:cohort.cohort_id,
    ...Object.fromEntries(IDENTITY_FIELDS.map(k=>[k,cohort[k]]))}));
  const game={schema:"gorge-r2-materialized-game-v1",deck,version,game_id:gid,
    batch:{deck_sha256:uiHash,runs:[{seed:123}]}};
  const gameHash=await put(base+"versions/"+version+"/"+deck+"/games/"+await sha256(gid)+".json",game);
  const page={schema:"gorge-r2-materialized-page-v1",deck,version,page:0,
    total:1,games:[{game_id:gid,result:"win",sha256:gameHash}],has_more:false};
  const pageHash=await put(base+"versions/"+version+"/"+deck+"/pages/000000.json",page);
  const summary={schema:"gorge-r2-live-summary-v1",deck,cohort_version:version,
    n:1,wins:1,losses:0,status:"ready"};
  const summaryHash=await put(base+"versions/"+version+"/"+deck+"/summary.json",summary);
  const manifest={schema:"gorge-r2-materialized-results-v1",version,
    decks:{[deck]:{cohort_id:cohort.cohort_id,cohort_fingerprint:fingerprint,
      n:1,wins:1,losses:0,ui_deck_sha256:uiHash,
      summary:{path:"summary.json",sha256:summaryHash},
      pages:[{path:"pages/000000.json",sha256:pageHash,count:1}]}}};
  const manifestHash=await put(base+"versions/"+version+"/manifest.json",manifest);
  await put(base+"current.json",{schema:"gorge-r2-results-current-v1",
    version,manifest_sha256:manifestHash});
  const bucket={async get(key){
    const data=store.get(key);
    if(!data)return null;
    return {size:data.byteLength,
      async arrayBuffer(){return data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength)},
      async json(){return JSON.parse(new TextDecoder().decode(data))}};
  }};
  return {bucket,store};
}
async function request(bucket,path){
  const url=new URL(path,"https://unit.example");
  const res=await worker.fetch(new Request(url),{GORGE_R2:bucket});
  return {status:res.status,body:await res.json()};
}

test("R2 materialized catalog, 25-game index and on-demand game use verified hashes",async()=>{
  const {bucket}=await fixture();
  const catalog=await request(bucket,"/v1/ui/catalog?deck="+deck);
  assert.equal(catalog.status,200);
  assert.equal(catalog.body.summary.n,1);
  assert.equal(catalog.body.version,version);
  const page=await request(bucket,"/v1/ui/page?deck="+deck+"&page=0");
  assert.equal(page.status,200);
  assert.equal(page.body.page.games[0].game_id,gid);
  assert.equal("batch" in page.body.page,false);
  const game=await request(bucket,"/v1/ui/game?deck="+deck+"&page=0&game_id="+encodeURIComponent(gid));
  assert.equal(game.status,200);
  assert.equal(game.body.game.batch.runs.length,1);
  const out=await request(bucket,"/v1/ui/page?deck="+deck+"&page=1");
  assert.equal(out.status,404);
});

test("source digest mutation fails closed without falling back to legacy results",async()=>{
  const {bucket,store}=await fixture();
  store.set(base+"versions/"+version+"/"+deck+"/summary.json",enc.encode('{"n":999}'));
  const out=await request(bucket,"/v1/ui/catalog?deck="+deck);
  assert.equal(out.status,503);
  assert.equal(out.body.error,"r2_query_unavailable");
});

test("missing active pointer permits the original verified Results route",async()=>{
  const {bucket,store}=await fixture();
  store.delete(base+"current.json");
  const out=await request(bucket,"/v1/ui/catalog?deck="+deck);
  assert.equal(out.status,404);
  assert.equal(out.body.error,"materialized_not_published");
});
