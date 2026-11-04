"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const adapt=require("../web/pages/gorge_legacy_adapter.js");
const old=require("../web/pages/game_outcomes.js");
const root=path.join(__dirname,"fixtures/gorge");
const game=seed=>{
  const g=JSON.parse(fs.readFileSync(path.join(root,
    "gorge-seed-"+seed+".ui.json"),"utf8"));
  // Archived recordings did not declare designated player roles. Assign
  // explicit roles only to controlled test fixtures, never public results.
  g.player_deck=seed===300?"mortarion_current":"magnus_premium";
  g.player_seat=0;
  return g;
};
const a=game(300),b=game(301);
const magnusA={...a,player_deck:"magnus_premium",player_seat:1};
const hashes={
  mortarion_current:"a".repeat(64),magnus_premium:"b".repeat(64),
  necron_dynasties:"c".repeat(64),wretched_ranks:"d".repeat(64),
  "avengers-assemble":"e".repeat(64),
};
test("explicit player-seat games become valid original-renderer batches",()=>{
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
  assert.equal(run.opening_hand_count,7);
  assert.equal(run.ui_observations[0].hand_count,6);
  if(a.visibility==="omniscient"){
    assert.deepEqual(run.opening_hand,
      a.snapshots[0].players[0].zones.hand.map(x=>x.name));
    assert.equal(run.ui_observations[0].hand.length,6);
    assert.equal(run.opening_hands_by_seat.length,3);
  }else{
    assert.equal(run.opening_hand,null);
    assert.equal(run.ui_observations[0].hand,null);
    assert.equal(run.opening_hands_by_seat,null);
  }
  assert.ok(run.ui_observations[0].battlefield.includes("Swamp"));
  assert.ok(run.ui_observations[0].battlefield.includes("Sol Ring"));
  assert.ok(run.ui_observations[0].actions.some(x=>
    x.type==="land_play"&&x.card==="Swamp"&&x.seat===0));
  assert.ok(run.ui_observations[0].actions.some(x=>
    x.type==="reviewed_generic_spell_cast"&&x.card==="Sol Ring"&&x.seat===0));
  assert.ok(run.ui_observations[0].mana_produced_by_color.B>0);
  const sourcedDraws=run.ui_observations.flatMap(x=>x.actions)
    .filter(x=>x.type==="draw");
  if(a.visibility==="omniscient"){
    assert.ok(sourcedDraws.some(x=>x.seat===0&&x.card),
      "Omniscient synthetic draws are native and named");
  }else assert.equal(sourcedDraws.length,0,
    "Private draws must not be inferred from a public-only export");
  assert.equal(run.opponent_decks.length,3);
  assert.deepEqual(run.opponent_decks.map(d=>d.deck_key),[
    "magnus_premium","necron_dynasties","wretched_ranks"]);
});
test("player seats rotate so the selected deck is always the old UI's seat zero",()=>{
  const batch=adapt.adapt([magnusA,b],"magnus_premium",hashes);
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
test("a deck appearing only as an opponent is not a player result",()=>{
  assert.equal(adapt.adapt([a],"magnus_premium",hashes),null);
  assert.equal(adapt.adapt([b],"mortarion_current",hashes),null);
  const unmarked={...a,player_seat:undefined,player_deck:undefined};
  assert.equal(adapt.adapt([unmarked],"mortarion_current",hashes),null);
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
test("unmarked hidden zones, public leaks and altered 40-life genesis are rejected",()=>{
  const unmarked=structuredClone(a);
  unmarked.visibility="omniscient";
  delete unmarked.synthetic_simulation_only;
  assert.equal(adapt.validateReplay(unmarked),false,
    "Never accept an unmarked hidden-data payload as synthetic");
  const leaked=structuredClone(a);
  leaked.visibility="public_events_only";
  for(const snap of leaked.snapshots)
    for(const p of snap.players){
      p.zones.hand=[];
      p.zones.library=[];
    }
  assert.equal(adapt.validateReplay(leaked),false,
    "Public-only replay must not contain hidden hand or library zones");
  const altered=structuredClone(a);
  altered.snapshots[0].players[0].life=20;
  assert.equal(adapt.validateReplay(altered),false);
});
test("explicit synthetic omniscience restores named hands, opponent hands and sourced draws",()=>{
  const g=structuredClone(a);
  g.visibility="omniscient";
  g.synthetic_simulation_only=true;
  for(const snap of g.snapshots){
    for(const p of snap.players){
      p.zones.hand=Array.from({length:p.hand_count},(_,i)=>({
        object_id:100000+p.seat*1000+i,
        name:p.seat===0?(i===0?"Swamp":"Simulated Card "+i):
          "Opponent "+p.seat+" Card "+i,token:false
      }));
      p.zones.library=Array.from({length:p.library_count},(_,i)=>({
        object_id:200000+p.seat*1000+i,name:"Library Card "+i,token:false
      }));
    }
  }
  const row=g.turns.find(t=>t.turn===5);
  row.events.push({seq:999999,kind:"draw",obj:4321,player:0,
    card_name:"Dark Ritual"});
  row.events.push({seq:999998,kind:"draw",obj:4322,player:1,
    card_name:"Opponent Secret"});
  row.events.sort((a,b)=>a.seq-b.seq);
  g.object_identity["4321"]="Dark Ritual";
  assert.equal(adapt.validateReplay(g),true);
  const batch=adapt.adapt([g],"mortarion_current",hashes);
  assert.equal(old.validate(batch),true);
  const run=batch.runs[0];
  assert.equal(run.opening_hand.length,7);
  assert.equal(run.opening_hand[0],"Swamp");
  assert.equal(run.opening_hands_by_seat.length,3);
  assert.equal(run.opening_hands_by_seat[0].hand[0],"Opponent 1 Card 0");
  assert.equal(run.ui_observations[0].hand.length,
    run.ui_observations[0].hand_count);
  assert.equal(run.ui_observations[0].opponent_hands.length,3);
  assert.ok(run.ui_observations.some(t=>t.actions.some(e=>
    e.type==="draw"&&e.card==="Dark Ritual"&&e.seat===0)));
  const stats=old.observationCardStats([run],()=>null,"Mortarion, Daemon Primarch");
  assert.ok(stats.seen&&stats.ranked.seen.some(x=>x.name==="Dark Ritual"));
  assert.ok(!stats.ranked.seen.some(x=>x.name==="Opponent Secret"),
    "Enemy draws cannot contaminate hero's seen/unplayed insights");
  assert.ok(stats.ranked.longest.some(x=>x.name==="Simulated Card 1"));
  assert.equal(run.gorge_source.visibility,"omniscient");
});


test("native ability pushes are translated with correct off-turn controllers",()=>{
  const g=game(300);
  const batch=adapt.adapt([g],"mortarion_current",hashes);
  assert.equal(old.validate(batch),true);
  const run=batch.runs[0];
  const actions=run.ui_observations.flatMap(o=>o.actions);
  const activations=actions.filter(a=>a.type==="ability_activated");
  const triggers=actions.filter(a=>a.type==="ability_triggered");
  const source=g.turns.flatMap(t=>t.events);
  const activIds=new Set([34,55,67,79,88]);
  const triggerIds=new Set([27,38,46,54,72,80]);
  assert.equal(activations.length,
    source.filter(e=>activIds.has(e.kind_id)).length,
    "Capture every source-native activated ability push from all four players");
  assert.equal(triggers.length,
    source.filter(e=>triggerIds.has(e.kind_id)).length,
    "Capture every supported native triggered ability push from all four players");
  assert.ok(activations.some(a=>
    a.card==="Myriad Landscape"&&a.seat===0&&a.native_kind_id===34));
  assert.ok(activations.some(a=>
    a.card==="Riptide Laboratory"&&a.seat===1&&a.native_kind_id===34));
  assert.ok(triggers.some(a=>
    a.card==="Yahenni, Undying Partisan"&&a.seat===0&&
    a.source_seq===2888),
    "Seat zero's omitted player field must not become active player seat two");
  assert.ok(triggers.some(a=>
    a.card==="Magnus the Red"&&a.seat===1));
  assert.ok(activations.every(a=>Number.isInteger(a.source_seq)&&
    Number.isInteger(a.source_object_id)));
  assert.ok(triggers.every(a=>Number.isInteger(a.source_seq)&&
    Number.isInteger(a.source_object_id)));
  assert.ok(actions.every(a=>a.type!=="ability_resolved"),
    "A naked Resolve stack-object ID cannot establish a source ability");
});
test("separate source ability rankings exclude opponent actions and include commander triggers",()=>{
  const mortarion=adapt.adapt([a],"mortarion_current",hashes);
  const run=old.model([mortarion],"mortarion_current",hashes.mortarion_current)
    .groups.flatMap(g=>g.runs)[0];
  const stats=old.observationCardStats([run],()=>null,"Mortarion, Daemon Primarch");
  assert.ok(stats.activated);
  assert.ok(stats.triggered);
  assert.ok(stats.ranked.activated.some(x=>x.name==="Pestilence Demon"));
  assert.ok(stats.ranked.activated.some(x=>x.name==="Myriad Landscape"));
  assert.ok(!stats.ranked.activated.some(x=>x.name==="Riptide Laboratory"),
    "Opposing Izzet pilot must not inflate the Mortarion activated card rankings");
  assert.ok(stats.ranked.triggered.some(x=>x.name==="Yahenni, Undying Partisan"));
  assert.ok(!stats.ranked.triggered.some(x=>x.name==="Magnus the Red"),
    "Opponent commander's triggers are visible in the replay but not our rankings");
  assert.ok(stats.ranked.triggered.every(x=>x.eventCount>=x.games));
  const magnus=adapt.adapt([a,b],"magnus_premium",hashes);
  const magnusRuns=old.model([magnus],"magnus_premium",hashes.magnus_premium)
    .groups.flatMap(g=>g.runs);
  const enemyStats=old.observationCardStats(magnusRuns,()=>null,"Magnus the Red");
  assert.ok(enemyStats.ranked.triggered.some(x=>x.name==="Magnus the Red"),
    "Commander triggers must not be filtered out of ability usage rankings");
});
test("legacy Python ability metrics stay combined when native Gorge mode is absent",()=>{
  const run=old.model([adapt.adapt([a],"mortarion_current",hashes)],
    "mortarion_current",hashes.mortarion_current).groups[0].runs[0];
  const copy=structuredClone(run);
  copy.batch={engine:"python"};
  copy.ui_observations=[{
    ...copy.ui_observations[0],
    actions:[{type:"reviewed_activated_ability",card:"Phyrexian Altar",seat:0},
             {type:"trigger",card:"Phyrexian Altar",seat:0}]
  }];
  copy.completed_rounds=1;
  const signals=old.observationCardStats([copy],()=>null);
  assert.equal(signals.activated.eventCount,2);
  assert.equal(signals.triggered,null);
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
