"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const adapter=require("../web/pages/gorge_legacy_adapter.js");
const renderer=require("../web/pages/game_outcomes.js");
// Stable test fixtures are distinct from the mutable published results
// catalog, which can legitimately be empty after archiving.
const dir=path.join(__dirname,"fixtures/gorge");
const games=[300,301].map(seed=>{
  const g=JSON.parse(fs.readFileSync(path.join(dir,
    "gorge-seed-"+seed+".ui.json"),"utf8"));
  g.player_seat=0;
  g.player_deck=g.decks[0];
  return g;
});
assert.equal(games.length,2);
const hashes=Object.fromEntries([...new Set(games.flatMap(g=>g.decks))]
  .map((key,i)=>[key,String(i).padStart(64,"0")]));
for(const game of games){
  assert(adapter.validateReplay(game),
    "Current original Results adapter must validate the source replay");
  assert.equal(game.snapshots[0].players.length,4);
  assert(game.snapshots[0].players.every(p=>p.life===40));
  assert(game.snapshots.every(s=>
    s.boundary==="first_pending_decision_of_turn"),
    "Never relabel a source turn-entry snapshot as an end-of-turn state");
  const abilityIds=new Set([34,55,67,79,88]);
  const triggerIds=new Set([27,38,46,54,72,80]);
  const native=game.turns.flatMap(t=>t.events);
  for(let hero=0;hero<4;hero++){
    const projected=adapter.projectRun(game,hero,30,hashes);
    assert.equal(projected.gorge_source.original_seat,hero);
    assert.equal(projected.life_history.length,projected.completed_rounds+1);
    assert(projected.ui_observations.every(o=>o.snapshot_is_turn_end===false));
    const actions=projected.ui_observations.flatMap(o=>o.actions);
    assert(actions.filter(x=>x.type==="ability_activated").every(x=>
      abilityIds.has(x.native_kind_id)&&Number.isInteger(x.source_seq)));
    assert(actions.filter(x=>x.type==="ability_triggered").every(x=>
      triggerIds.has(x.native_kind_id)&&Number.isInteger(x.source_seq)));
    assert(actions.every(x=>Number.isInteger(x.seat)&&x.seat>=0&&x.seat<4));
    if(game.visibility==="omniscient"){
      assert.equal(projected.opening_hand.length,7);
      assert.equal(projected.opening_hands_by_seat.length,3);
      assert(projected.opening_hands_by_seat.every(x=>x.hand?.length===x.hand_count));
    }else assert.equal(projected.opening_hand,null);
  }
  assert(native.some(e=>abilityIds.has(e.kind_id)));
  assert(native.some(e=>triggerIds.has(e.kind_id)));
  const batch=adapter.adapt(games,game.decks[0],hashes);
  assert(renderer.validate(batch));
}
assert.throws(()=>adapter.projectRun({schema:"gorge-ui-replay-v1"},0,30,hashes));
const html=fs.readFileSync(path.join(__dirname,"../web/pages/index.html"),"utf8");
assert.match(html,/id="key-insights-grid"/);
assert.match(html,/id="turn-reviewer-results"/);
assert.match(html,/id="gorge-replay-panel"/);
assert.doesNotMatch(html,/gorge-canonical-intro/);
assert.doesNotMatch(html,/id="gorge-dashboard"/);
assert.doesNotMatch(html,/legacy-simulation-archive/);
const app=fs.readFileSync(path.join(__dirname,"../web/pages/app.js"),"utf8");
assert.match(app,/window\.GorgeDeckLabCardInfo=cardInfo/);
console.log("PASS original Gorge-compatible Deck Lab: abilities, seats, source counts and original DOM verified");
