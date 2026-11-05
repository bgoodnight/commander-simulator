"use strict";
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const adapter=require("../web/pages/gorge_legacy_adapter.js");
const renderer=require("../web/pages/game_outcomes.js");
function extract(dir,summary,podFile,catalogFile,target){
  const rows=fs.readFileSync(summary,"utf8").trim().split("\n").map(JSON.parse);
  const pod=JSON.parse(fs.readFileSync(podFile,"utf8"));
  const catalog=JSON.parse(fs.readFileSync(catalogFile,"utf8"));
  const deck=catalog.decks.find(d=>d.key===pod.hero);
  assert(deck&&rows.length>0);
  const cards=new Map(Object.values(catalog.cards).flatMap(c=>
    [c.name,...(c.face_names||[])].filter(Boolean).map(n=>[n,c])));
  const games=rows.map(row=>{
    assert(row.finished&&row.replay_verified&&!row.error);
    assert(row.decks[row.hero_seat]===pod.hero);
    const g=JSON.parse(fs.readFileSync(path.join(dir,"gorge-seed-"+row.seed+".ui.json"),"utf8"));
    assert(g.seed===row.seed&&g.chain===row.replay_chain);
    assert.deepEqual(g.decks,row.decks);
    g.player_seat=row.hero_seat;g.player_deck=pod.hero;
    assert(adapter.validateReplay(g));
    assert.equal(adapter.realWinner(g),row.draw?"draw":row.winner_seat);
    return g;
  });
  const batch=adapter.adapt(games,pod.hero,pod.deck_sha256);
  assert(batch&&renderer.validate(batch));
  const model=renderer.model([batch],pod.hero,pod.deck_sha256[pod.hero]);
  const runs=model.groups.flatMap(group=>group.runs);
  assert.equal(runs.length,rows.length);
  const stats=renderer.observationCardStats(runs,n=>cards.get(n)||null,deck.commander);
  assert.equal(stats.coverage,rows.length);
  const categories={};
  for(const [kind,items] of Object.entries(stats.ranked)){
    categories[kind]=items.map(item=>({
      name:item.name,
      counts:[...item.counts].map(([run,count])=>[run.seed,count]),
      seen:[...item.seen].map(run=>run.seed),
      durations:item.durations,
      timesPlayed:item.timesPlayed,
      events:item.events.filter(e=>Number.isInteger(e.turn)).map(e=>[e.seed,e.turn])
    }));
  }
  fs.writeFileSync(target,JSON.stringify({
    schema:"gorge-card-insights-shard-v1",deck:pod.hero,
    deck_sha256:pod.deck_sha256[pod.hero],completed_verified_games:rows.length,
    seed_chains:rows.map(row=>[row.seed,row.replay_chain]),
    confirmed_tutors:stats.confirmedTutors,categories
  })+"\n");
  console.log("Verified card features",pod.hero,rows.length,"games");
}
if(require.main===module)extract(...process.argv.slice(2));
module.exports={extract};
