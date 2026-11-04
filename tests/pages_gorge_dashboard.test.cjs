"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const dashboard=require("../web/pages/gorge_dashboard.js");
const dir=path.join(__dirname,"../docs/deck-lab/gorge-data");
const manifest=JSON.parse(fs.readFileSync(path.join(dir,"manifest.json"),"utf8"));
const games=manifest.games.map(g=>JSON.parse(fs.readFileSync(path.join(dir,g.file),"utf8")));
assert.equal(games.length,2);
for(const game of games){
  assert(dashboard.valid(game));
  const a=dashboard.analyze(game);
  assert.equal(a.turns,38);
  assert.equal(a.snapshots,38);
  assert.equal(a.bySeat.length,4);
  assert.equal(a.winner,null,"Do not infer winners from turn-entry snapshots");
  assert.equal(a.bySeat.reduce((n,x)=>n+x.casts,0),
    game.turns.flatMap(t=>t.events).filter(e=>e.kind==="cast").length);
  assert.equal(a.bySeat.reduce((n,x)=>n+x.lands,0),
    game.turns.flatMap(t=>t.events).filter(e=>e.kind==="land_played").length);
  assert(a.timeline[0].state.players.every(p=>p.life===40));
}
const all=dashboard.summary(games);
assert.equal(all.analyses.length,2);
assert(all.decks.length>=4);
assert(all.decks.every(x=>x.games>=1));
assert.throws(()=>dashboard.analyze({schema:"gorge-ui-replay-v1"}));
console.log("PASS gorge dashboard source-based metrics for both verified games");
