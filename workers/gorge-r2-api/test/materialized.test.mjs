import test from "node:test";
import assert from "node:assert/strict";
import {getMaterialized} from "../materialized.mjs";
import registry from "../../../data/gorge_analytics_cohort_registry_v1.json" with {type:"json"};
import {sha256,stableJson,IDENTITY_FIELDS} from "../core.mjs";

const deck="mortarion_current",version="c".repeat(64),uiHash="a".repeat(64);
const gid="123456-1/mortarion_current/0/123";
const base="results/materialized/v1/";
const enc=new TextEncoder();

async function fixture(withInsights=false){
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
  let insightsRef=null;
  if(withInsights){
    const insights={schema:"gorge-card-insights-v1",deck,cohort_version:version,
      verified_games:1,observed_games:1,coverage:{
        denominator:1,numerator:1,missing:0,level:"full-cohort"
      },categories:{played:[{name:"Sol Ring",games:1,eventCount:1}]}};
    insightsRef={path:"insights.json",sha256:await put(
      base+"versions/"+version+"/"+deck+"/insights.json",insights)};
  }
  const manifest={schema:"gorge-r2-materialized-results-v1",version,
    decks:{[deck]:{cohort_id:cohort.cohort_id,cohort_fingerprint:fingerprint,
      n:1,wins:1,losses:0,ui_deck_sha256:uiHash,
      summary:{path:"summary.json",sha256:summaryHash},
      insights:insightsRef,
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
test("R2 materialized catalog, 25-game index and on-demand game use verified hashes",async()=>{
  const {bucket}=await fixture();
  const catalog=await getMaterialized(bucket,deck,registry);
  assert.equal(catalog.status,"ready");
  assert.equal(catalog.summary.n,1);
  assert.equal(catalog.version,version);
  const page=await getMaterialized(bucket,deck,registry,0);
  assert.equal(page.status,"ready");
  assert.equal(page.page.games[0].game_id,gid);
  assert.equal("batch" in page.page,false);
  const game=await getMaterialized(bucket,deck,registry,0,gid);
  assert.equal(game.status,"ready");
  assert.equal(game.game.batch.runs.length,1);
  const out=await getMaterialized(bucket,deck,registry,1);
  assert.equal(out.status,"page_not_found");
});

test("source digest mutation fails closed without falling back to legacy results",async()=>{
  const {bucket,store}=await fixture();
  store.set(base+"versions/"+version+"/"+deck+"/summary.json",enc.encode('{"n":999}'));
  await assert.rejects(getMaterialized(bucket,deck,registry),/materialized_digest_mismatch/);
});

test("missing active pointer explicitly signals old-route compatibility",async()=>{
  const {bucket,store}=await fixture();
  store.delete(base+"current.json");
  const out=await getMaterialized(bucket,deck,registry);
  assert.equal(out,null);
});

test("full-cohort card insights are served only at exact active version",async()=>{
  const {bucket}=await fixture(true);
  const report=await getMaterialized(bucket,deck,registry,null,null,"insights");
  assert.equal(report.status,"ready");
  assert.equal(report.total,1);
  assert.equal(report.insights.categories.played[0].name,"Sol Ring");
});

test("unmaterialized card insights do not produce fabricated rankings",async()=>{
  const {bucket}=await fixture();
  const report=await getMaterialized(bucket,deck,registry,null,null,"insights");
  assert.equal(report.status,"insights_pending");
  assert.equal("insights" in report,false);
});

test("incorrect complete-cohort card coverage is rejected",async()=>{
  const {bucket,store}=await fixture(true);
  const key=base+"versions/"+version+"/"+deck+"/insights.json";
  store.set(key,enc.encode(JSON.stringify({verified_games:999})));
  await assert.rejects(
    getMaterialized(bucket,deck,registry,null,null,"insights"),
    /materialized_digest_mismatch/
  );
});
