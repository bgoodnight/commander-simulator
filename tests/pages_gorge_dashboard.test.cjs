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
  const totals={casts:0,lands:0,tokens:0};
  for(let seat=0;seat<4;seat++){
    const a=dashboard.analyze(game,seat);
    assert.equal(a.seat,seat);
    assert.equal(a.key,game.decks[seat]);
    assert(a.timeline.length>=8);
    assert(a.timeline.every((t,i)=>t.number===i+1));
    assert(a.timeline.every(t=>t.atStart?.boundary==="first_pending_decision_of_turn"));
    assert(a.timeline[0].atStart.players.every(p=>p.life===40));
    assert(a.timeline.every(t=>!t.atNext||
      t.atNext.boundary==="first_pending_decision_of_turn"),
      "Never label turn-entry snapshots as turn-end state");
    totals.casts+=a.casts;totals.lands+=a.lands;totals.tokens+=a.tokens;
  }
  const ev=game.turns.flatMap(t=>t.events);
  assert.equal(totals.casts,ev.filter(e=>e.kind==="cast").length);
  assert.equal(totals.lands,ev.filter(e=>e.kind==="land_played").length);
  assert.equal(totals.tokens,ev.filter(e=>e.kind==="token_created").length);
}
const all=dashboard.summary(games);
assert(all.decks.length>=4);
assert(all.decks.every(x=>x.games>=1));
assert.throws(()=>dashboard.analyze({schema:"gorge-ui-replay-v1"},0));
const html=fs.readFileSync(path.join(__dirname,"../web/pages/index.html"),"utf8");
assert.match(html,/id="key-insights-grid"/);
assert.match(html,/id="turn-reviewer-results"/);
assert.match(html,/id="gorge-replay-panel"/);
assert.doesNotMatch(html,/gorge-canonical-intro/);
assert.doesNotMatch(html,/id="gorge-dashboard"/);
assert.doesNotMatch(html,/legacy-simulation-archive/);
const app=fs.readFileSync(path.join(__dirname,"../web/pages/app.js"),"utf8");
assert.match(app,/window\.GorgeDeckLabCardInfo=cardInfo/);
console.log("PASS original Deck Lab Results UI reads two real Gorge samples; source counts, original DOM and privacy boundaries verified");
