import test from "node:test";
import assert from "node:assert/strict";
import { aggregate, isApproved, isDecisive, sha256, stableJson, validateDeck, normalizeRow, IDENTITY_FIELDS, approvedGameIndex, approvedGameDetail } from "../core.mjs";

const fp = Object.fromEntries(IDENTITY_FIELDS.map(k=>[k,"pinned-"+k]));
const approved={cohort_id:"baseline-1",status:"current",approved:true,approval_ref:"reviewed",...fp};
const registry={schema:"gorge-analytics-cohort-registry-v1",cohorts:[approved]};
async function game(overrides={}){
  const fingerprint=await sha256(stableJson({cohort_id:"baseline-1",...fp}));
  return {game_id:"batch/a/0/1",deck:"mortarion_current",finished:true,replay_verified:true,
    error:null,draw:false,hero_seat:0,winner_seat:0,turns:18,
    decks_json:JSON.stringify(["mortarion_current","precon1","precon2","precon3"]),
    source_sha256:"f".repeat(64),cohort_id:"baseline-1",cohort_manifest_sha256:fingerprint,...fp,...overrides};
}
test("approval requires exact identity and a source-backed decisive outcome",async()=>{
  const g=await game();
  assert.equal(await isApproved(g,registry),true);
  for(const delta of [{draw:true,winner_seat:null},{replay_verified:false},
    {finished:false},{engine_commit:"older"},{cohort_id:"unknown"},
    {source_sha256:null},{cohort_manifest_sha256:"0".repeat(64)}]){
    assert.equal(await isApproved({...g,...delta},registry),false,JSON.stringify(delta));
  }
  assert.equal(await isApproved(g,{schema:registry.schema,cohorts:[]}),false);
});
test("groups count each game once and only decisive records",async()=>{
  const a=await game(),b=await game({game_id:"batch/a/0/2",winner_seat:2,turns:22});
  const draws=await game({game_id:"batch/a/0/3",draw:true,winner_seat:null});
  const result=aggregate([a,b,draws],"mortarion_current");
  assert.equal(result.n,2);assert.equal(result.win_rate,.5);
  assert.equal(result.median_game_turns,20);
  assert.equal(result.groups.opponents.length,3);
  assert.equal(result.groups.opponents[0].n,2);
  assert.throws(()=>aggregate([a,a],"mortarion_current"),/Duplicate/);
});
test("never accept keys or usernames as R2 object paths",()=>{
  assert.equal(validateDeck("magnus_premium"),"magnus_premium");
  for(const bad of ["../private","", "x?token=1","A".repeat(100)])
    assert.throws(()=>validateDeck(bad));
  assert(!isDecisive({finished:false}));
});

test("Parquet INT64 preserves exact seat and turn values safely",async()=>{
  const g=await game();
  const row=normalizeRow({...g,hero_seat:0n,winner_seat:0n,turns:18n});
  assert.equal(typeof row.hero_seat,"number");
  assert.equal(typeof row.turns,"number");
  assert.equal((await isApproved(row,registry)),true);
  assert.throws(()=>normalizeRow({winner_seat:9007199254740993n}),/Unsafe/);
});

test("approved game index reveals only safe, deterministic summaries",async()=>{
  const a=await game({game_id:"batch/a/0/2"});
  const b=await game({game_id:"batch/a/0/1",winner_seat:1});
  const out=approvedGameIndex([a,b],"mortarion_current",1);
  assert.equal(out.schema,"gorge-r2-approved-game-index-v1");
  assert.equal(out.total,2);
  assert.equal(out.has_more,true);
  assert.equal(out.games[0].result,"loss");
  assert.deepEqual(out.games[0].opponent_decks,["precon1","precon2","precon3"]);
  assert.equal("source_sha256" in out.games[0],false);
  assert.equal("seed" in out.games[0],false);
  assert.equal("event_json" in out.games[0],false);
  assert.deepEqual(approvedGameIndex([],"mortarion_current").games,[]);
  assert.throws(()=>approvedGameIndex([a,a],"mortarion_current"),/duplicate/i);
  const drawn=await game({draw:true,winner_seat:null});
  assert.throws(()=>approvedGameIndex([drawn],"mortarion_current"),/unapproved/);
  assert.throws(()=>approvedGameIndex([a],"mortarion_current",26),/limit/);
});

test("individual approved game detail is limited to public-safe metadata",async()=>{
  const g=await game({event_json:"SECRET",seed:891,object_key:"PRIVATE"});
  const out=approvedGameDetail([g],"mortarion_current",g.game_id);
  assert.equal(out.game_id,g.game_id);
  assert.equal(out.result,"win");
  assert.equal(out.replay_status,"not_available");
  for(const field of ["event_json","seed","object_key","source_sha256","decks_json"])
    assert.equal(field in out,false);
  assert.equal(approvedGameDetail([g],"mortarion_current","absent"),null);
  assert.throws(()=>approvedGameDetail([g,g],"mortarion_current",g.game_id),/duplicate/);
});
