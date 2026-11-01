"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {test}=require("node:test");
const {assess,performanceEvidence,combineEvidence}=require("../web/pages/brackets.js");
const registry=JSON.parse(fs.readFileSync(path.join(__dirname,"../web/pages/game-changers.json"),"utf8"));
const fixtures=(names)=>({
  entries:names.map((name,i)=>({name,qty:1,oracle_id:"card-"+i})).concat([{name:"Island",qty:100-names.length,oracle_id:"basic"}]),
  cards:Object.fromEntries(names.map((name,i)=>["card-"+i,{name,face_names:[],oracle_text:""}]).concat([["basic",{name:"Island",face_names:[],oracle_text:""}]]))
});
test("Game Changers reference is exactly 53 unique names",()=>{
  assert.equal(registry.names.length,53);
  assert.equal(new Set(registry.names).size,53);
});
test("no Game Changers gives provisional Core screen, not an official adjudication",()=>{
  const {entries,cards}=fixtures(["Arcane Signet"]);
  const result=assess(entries,cards,registry);
  assert.equal(result.status,"provisional");assert.equal(result.estimated_bracket,2);
  assert.equal(result.count,0);assert.equal(result.total,100);
});
test("one Game Changer screens at least Bracket 3",()=>{
  const {entries,cards}=fixtures(["Underworld Breach"]);
  const result=assess(entries,cards,registry);
  assert.equal(result.estimated_bracket,3);
  assert.deepEqual(result.matches.map(x=>x.name),["Underworld Breach"]);
});
test("four Game Changers screen at least Bracket 4",()=>{
  const {entries,cards}=fixtures(["Underworld Breach","Rhystic Study","Mystical Tutor","Ancient Tomb"]);
  assert.equal(assess(entries,cards,registry).minimum_by_game_changers,4);
});
test("unrecognized edited card does not silently receive a confident result",()=>{
  const {entries,cards}=fixtures(["Underworld Breach"]);
  delete cards["card-0"];
  const result=assess(entries,cards,registry);
  assert.equal(result.status,"incomplete");assert.deepEqual(result.unknown,["Underworld Breach"]);
});
test("cautious signals do not mistake all library searches for game changers",()=>{
  const {entries,cards}=fixtures(["Fabricate"]);
  cards["card-0"].oracle_text="Search your library for an artifact card, reveal it, put it into your hand, then shuffle.";
  const result=assess(entries,cards,registry);
  assert.equal(result.count,0);assert.deepEqual(result.tutors,["Fabricate"]);
});

test("bounded six-turn simulations cannot change a bracket estimate",()=>{
  const {entries,cards}=fixtures(["Arcane Signet"]);
  const base=assess(entries,cards,registry);
  const bounded=Array.from({length:100},()=>({
    deck_sha256:"deck-1",mode:"bounded_authoritative_early_actions",
    game_complete:true,opponents_modeled:true,win_conditions_modeled:true,winning_turn:3,won:true
  }));
  const combined=combineEvidence(base,bounded,"deck-1");
  assert.equal(combined.evidence_mode,"cards_only");
  assert.equal(combined.estimated_bracket,2);
});
test("complete matched multiplayer runs can add qualifying evidence",()=>{
  const {entries,cards}=fixtures(["Arcane Signet"]);
  const base=assess(entries,cards,registry);
  const runs=Array.from({length:40},(_,i)=>({
    deck_sha256:"deck-1",mode:"complete_multiplayer_game",game_complete:true,
    opponents_modeled:true,win_conditions_modeled:true,winning_turn:i<12?5:10,won:i<12
  }));
  assert.equal(performanceEvidence(runs,"different revision"),null);
  const combined=combineEvidence(base,runs,"deck-1");
  assert.equal(combined.evidence_mode,"cards_and_games");
  assert.equal(combined.performance.sample,40);
  assert.equal(combined.estimated_bracket,4);
});
test("insufficient complete games preserve card-only assessment",()=>{
  const {entries,cards}=fixtures(["Underworld Breach"]);
  const base=assess(entries,cards,registry);
  const runs=Array.from({length:5},()=>({
    deck_sha256:"deck-1",mode:"complete_multiplayer_game",game_complete:true,
    opponents_modeled:true,win_conditions_modeled:true,winning_turn:5,won:true
  }));
  assert.equal(combineEvidence(base,runs,"deck-1").evidence_mode,"cards_only");
});
