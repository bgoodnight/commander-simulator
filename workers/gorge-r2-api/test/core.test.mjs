import test from "node:test";
import assert from "node:assert/strict";
import { aggregate, uiOverview, originalUiBatch, isApproved, isDecisive, sha256, stableJson, validateDeck, normalizeRow, IDENTITY_FIELDS, approvedGameIndex, approvedGameDetail, approvedEventSegments, approvedEventWindow, isDiagnosticAuthorized } from "../core.mjs";

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

test("native event segments retain only non-secret family counts",()=>{
  const gid="batch/mortarion_current/0/1";
  const events=[
    {game_id:gid,seq:1,kind_id:0,secret:false},
    {game_id:gid,seq:2,kind_id:3,secret:true},
    {game_id:gid,seq:3,kind_id:9,secret:false},
    {game_id:gid,seq:4,kind_id:5,secret:false},
    {game_id:"other",seq:5,kind_id:4,secret:false}
  ];
  const result=approvedEventSegments(events,gid);
  assert.equal(result.event_count,4);
  assert.equal(result.segments.length,2);
  assert.equal(result.segments[0].public_events,1);
  assert.equal(result.segments[0].withheld_events,1);
  assert.equal(result.segments[1].kinds.damage,1);
  assert.equal(result.raw_events_exposed,false);
  assert(!JSON.stringify(result).includes("other"));
  assert.throws(()=>approvedEventSegments([events[0],events[0]],gid),/invalid/);
  assert.throws(()=>approvedEventSegments([{...events[0],secret:null}],gid),/invalid/);
});

test("approved event windows are bounded to one source-backed game",()=>{
  const g={event_start_row:10000,native_event_count:15218};
  assert.deepEqual(approvedEventWindow(g,123434),{
    rowStart:10000,rowEnd:25218,count:15218});
  // A shard may have >100k events; the *requested game* is bounded.
  for(const bad of [
    {event_start_row:-1,native_event_count:5},
    {event_start_row:5,native_event_count:0},
    {event_start_row:123430,native_event_count:5},
    {event_start_row:0,native_event_count:30001},
    {native_event_count:12},
    {event_start_row:5}
  ])assert.throws(()=>approvedEventWindow(bad,123434),/unindexed/);
  assert.throws(()=>approvedEventWindow({event_start_row:1n,native_event_count:2},100),
    /unindexed/);
});

test("private diagnostic auth cannot be enabled by default or short tokens",()=>{
  const token="a".repeat(64);
  assert.equal(isDiagnosticAuthorized("Bearer "+token,token),true);
  for(const [header,secret] of [
    [null,token],["Bearer "+token,null],["Bearer "+token,"short"],
    ["Bearer "+token,"a".repeat(63)],["bearer "+token,token],
    ["Bearer "+token+"x",token],["Bearer "+"b".repeat(64),token]
  ])assert.equal(isDiagnosticAuthorized(header,secret),false);
});

test("UI overview retains source-backed outcomes, histogram, and no invented card details",async()=>{
  const first=await game();
  const second=await game({game_id:"batch/a/0/2",winner_seat:1,turns:16});
  const source={...aggregate([first,second],"mortarion_current"),status:"ready"};
  const view=uiOverview(source);
  assert.equal(view.schema,"gorge-r2-ui-overview-v1");
  assert.deepEqual(view.outcomes,{n:2,wins:1,losses:1,win_rate:.5,baseline:.25});
  assert.deepEqual(view.game_turn_histogram,[{turn:16,games:1},{turn:18,games:1}]);
  assert.equal(view.groups.opponents.length,3);
  assert.equal(view.coverage.turn_histogram_games,2);
  assert.equal(view.coverage.card_insights,"not_exported_from_warehouse");
  for(const secret of ["source_sha256","seed","event_json","source_object_id","intent","hand"]){
    // "hand" can appear only as an explicit unavailable coverage key.
    const serialized=JSON.stringify(view);
    if(secret==="hand") assert.equal(view.coverage.hand_durations,"requires_source_backed_ui_projection");
    else assert.equal(serialized.includes('"'+secret+'"'),false);
  }
});
test("UI overview cannot advertise results for an unapproved or invalid cohort",()=>{
  const pending={schema:"gorge-r2-live-summary-v1",deck:"magnus_premium",
    status:"awaiting_cohort_approval",n:0,wins:0,losses:0,win_rate:null,
    groups:{opponents:[]},median_game_turns:null,game_turn_histogram:[]};
  const view=uiOverview(pending);
  assert.equal(view.outcomes.n,0);
  assert.equal(view.outcomes.win_rate,null);
  assert.deepEqual(view.game_turn_histogram,[]);
  assert.deepEqual(view.groups.opponents,[]);
  assert.throws(()=>uiOverview({...pending,status:"ready",n:2}),/invalid_ui_outcomes/);
  assert.throws(()=>uiOverview({...pending,status:"experimental"}),/invalid_ui_overview_source/);
});

test("approved public projection produces an original Results-compatible batch",async()=>{
  const row=await game({seed:712,chain:"source-chain-712",
    player_deck_sha256:"revised-deck",game_id:"b/d/0/712"});
  const run={
    seed:712,completed_rounds:1,
    life_history:[
      {round:0,life_totals:{"0":40,"1":40,"2":40,"3":40},
       life_changes:[],new_eliminations:[],alive_seats:[0,1,2,3]},
      {round:1,life_totals:{"0":37,"1":40,"2":40,"3":40},
       life_changes:[],new_eliminations:[],alive_seats:[0,1,2,3]}
    ],
    ui_observations:[{turn:1,actions:[],hand:null,opponent_hands:null,
      board_states:[{seat:0,hand:null}],snapshot_is_turn_end:false}],
    opening_hand:null,opening_hands_by_seat:null,
    gorge_source:{chain:"source-chain-712",visibility:"public_events_only",
      synthetic_simulation_only:false},
    outcome:{status:"win",complete:true,winner_seat:0,
      completed_rounds:1,requested_rounds:1}
  };
  const source={schema:"gorge-r2-original-ui-projection-v1",deck:"mortarion_current",
    games:[{game_id:row.game_id,chain:row.chain,source_sha256:row.source_sha256,run}]};
  const batch=originalUiBatch([row],source,"mortarion_current");
  assert.equal(batch.format,"commander-gorge-outcomes-v1");
  assert.equal(batch.schema_version,1);
  assert.equal(batch.deck_sha256,"revised-deck");
  assert.equal(batch.opponent_fidelity,"gorge_native_full_100_card_decks");
  assert.equal(batch.runs.length,1);
  assert.equal(batch.runs[0].outcome.status,"win");
  assert.equal(batch.runs[0].outcome.requested_rounds,batch.requested_rounds);
  assert.equal(batch.runs[0].ui_observations.length,1);
  assert.equal(JSON.stringify(batch).includes('"intents"'),false);
  for(const change of [
    {games:[]},
    {games:[{...source.games[0],chain:"wrong"}]},
    {games:[{...source.games[0],run:{...run,opening_hand:["Private Card"]}}]},
    {games:[{...source.games[0],run:{...run,log:{events:[]}}}]},
    {games:[{...source.games[0],run:{...run,source_object_id:123}}]},
    {games:[{...source.games[0],run:{...run,outcome:{...run.outcome,status:"loss"}}}]}
  ])assert.throws(()=>originalUiBatch([row],{...source,...change},"mortarion_current"));
  assert.throws(()=>originalUiBatch([row,{...row,game_id:"b/d/0/713"}],
    source,"mortarion_current"),/incomplete_original_ui_projection/);
  assert.throws(()=>originalUiBatch([row,{...row,game_id:"b/d/0/713",
    player_deck_sha256:"other"}],source,"mortarion_current"),
    /mixed_original_ui_deck_revisions/);
});
