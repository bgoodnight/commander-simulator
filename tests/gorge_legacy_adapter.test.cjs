"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const adapt=require("../web/pages/gorge_legacy_adapter.js");
const old=require("../web/pages/game_outcomes.js");
const root=path.join(__dirname,"../web/pages/data/gorge");
const game=seed=>JSON.parse(fs.readFileSync(path.join(root,
  "gorge-seed-"+seed+".ui.json"),"utf8"));
const a=game(300),b=game(301);
const hashes={
  mortarion_current:"a".repeat(64),magnus_premium:"b".repeat(64),
  necron_dynasties:"c".repeat(64),wretched_ranks:"d".repeat(64),
  "avengers-assemble":"e".repeat(64),
};
test("actual public Gorge games become valid original-renderer batches",()=>{
  const batch=adapt.adapt([a,b],"mortarion_current",hashes);
  assert.equal(batch.format,"commander-gorge-outcomes-v1");
  assert.equal(batch.engine,"gorge");
  assert.equal(batch.opponent_fidelity,"gorge_native_full_100_card_decks");
  assert.equal(old.validate(batch),true);
  assert.equal(batch.runs.length,1);
  const run=batch.runs[0];
  assert.equal(run.seed,300);
  assert.equal(run.outcome.status,"win");
  assert.equal(run.outcome.winner_seat,0);
  assert.equal(run.gorge_source.outcome_provenance,"native_game_over_event");
  assert.equal(run.gorge_source.chain,a.chain);
  assert.equal(run.life_history.length,run.completed_rounds+1);
  assert.equal(run.ui_observations.length,run.completed_rounds);
  assert.equal(run.ui_observations[0].snapshot_is_turn_end,false);
  assert.equal(run.opening_hand,null);
  assert.equal(run.opening_hand_count,7);
  assert.equal(run.ui_observations[0].hand,null);
  assert.equal(run.ui_observations[0].hand_count,6);
  assert.ok(run.ui_observations[0].battlefield.includes("Swamp"));
  assert.ok(run.ui_observations[0].battlefield.includes("Sol Ring"));
  assert.ok(run.ui_observations[0].actions.some(x=>
    x.type==="land_play"&&x.card==="Swamp"&&x.seat===0));
  assert.ok(run.ui_observations[0].actions.some(x=>
    x.type==="reviewed_generic_spell_cast"&&x.card==="Sol Ring"&&x.seat===0));
  assert.ok(run.ui_observations[0].mana_produced_by_color.B>0);
  assert.equal(run.ui_observations[0].actions.filter(x=>x.type==="draw").length,0,
    "Private draws must not be inferred");
  assert.equal(run.opponent_decks.length,3);
  assert.deepEqual(run.opponent_decks.map(d=>d.deck_key),[
    "magnus_premium","necron_dynasties","wretched_ranks"]);
});
test("player seats rotate so the selected deck is always the old UI's seat zero",()=>{
  const batch=adapt.adapt([a,b],"magnus_premium",hashes);
  assert.equal(old.validate(batch),true);
  assert.equal(batch.runs.length,2);
  for(const run of batch.runs){
    assert.equal(run.outcome.status,"loss");
    assert.equal(run.gorge_source.original_seat,
      run.seed===300?1:0);
    assert.ok(run.ui_observations.some(o=>o.actions.some(action=>
      action.seat===0&&action.card)), "Rotated hero has source-backed named plays");
    if(run.seed===300)
      assert.ok(run.ui_observations.some(o=>o.actions.some(action=>
        action.seat===0&&action.card==="Preordain")));
    assert.equal(run.life_history[0].life_totals[0],40);
  }
});
test("winner is sourced only from an exact native game-over identifier",()=>{
  assert.equal(adapt.realWinner(a),0);
  assert.equal(adapt.realWinner(b),3);
  const incomplete=structuredClone(a);
  for(const t of incomplete.turns)
    t.events=t.events.filter(e=>e.kind!=="game_over");
  assert.equal(adapt.realWinner(incomplete),null);
  const batch=adapt.adapt([incomplete],"mortarion_current",hashes);
  assert.equal(batch.runs[0].outcome.status,"unresolved");
  assert.equal(batch.runs[0].outcome.complete,false);
});
test("no hidden-content projection or altered 40-life genesis is accepted",()=>{
  const altered=structuredClone(a);
  altered.visibility="omniscient";
  assert.equal(adapt.validateReplay(altered),false);
  altered.visibility="public_events_only";
  altered.snapshots[0].players[0].life=20;
  assert.equal(adapt.validateReplay(altered),false);
});
test("genuine cast records populate the ORIGINAL source statistics",()=>{
  const batch=adapt.adapt([a],"mortarion_current",hashes);
  const names={ 
    "Sol Ring":{type_line:"Artifact"},
    "Plague Drone":{type_line:"Creature — Demon"},
  };
  const runs=old.model([batch],"mortarion_current",hashes.mortarion_current)
    .groups.flatMap(g=>g.runs);
  const stats=old.observationCardStats(runs,name=>names[name]||null,
    "Mortarion, Daemon Primarch");
  assert.equal(stats.coverage,1);
  assert.ok(stats.ranked.played.some(x=>x.name==="Sol Ring"));
  assert.ok(stats.ranked.artifact.some(x=>x.name==="Sol Ring"));
  assert.ok(stats.ranked.creature.some(x=>x.name==="Plague Drone"));
  assert.ok(!stats.ranked.played.some(x=>x.name==="Baral, Chief of Compliance"),
    "Opponent wizard spells must not become Mortarion card insights");
  assert.ok(!stats.ranked.played.some(x=>x.name==="Gravecrawler"),
    "Opponent zombie spells must not contaminate the hero ranking");
});
