"use strict";
const assert=require("node:assert/strict");
const test=require("node:test");
const {summarize,findings}=require("../web/pages/results_insights.js");

function record(seed,{lands=[1,2,3,4,5,6],candidateTurns=[4,5,6],
  opening=["Swamp","Swamp","Sol Ring","Dark Ritual","Island","Forest","Lightning Bolt"]}={}){
  return {
    mode:"observation",seed,opening_hand:opening,
    trace:lands.map((count,index)=>({
      turn:index+1,modeled_sources:Array.from({length:count},(_,i)=>({card:"Swamp",colors:["B"]})),
      land_played:count>0?"Swamp":null,
      candidate_if_supported:candidateTurns.includes(index+1)?[
        {card:"Sol Ring",mana_value:1,status:"candidate_if_supported"}]:[],
      hand_count:8-index
    }))
  };
}

test("aggregates the archive, not only the selected seed",()=>{
  const runs={};
  for(let i=0;i<11;i++)runs[String(i)]=record(i);
  const value=summarize(runs);
  assert.equal(value.n,11);
  assert.deepEqual(value.meanSources,[1,2,3,4,5,6]);
  assert.equal(value.metrics.earlyLand.count,11);
  assert.equal(value.metrics.t3Sources.pct,100);
  assert.equal(value.metrics.t4Candidate.pct,100);
  assert.deepEqual(value.openingGroups.find(x=>x.label==="4").seeds,
    Array.from({length:11},(_,i)=>String(i)));
  assert.equal(value.candidateGroups[3].numerator,11);
});

test("narrative changes based on measured data and never invents a win rate",()=>{
  const weak={};
  const strong={};
  for(let i=0;i<11;i++){
    weak[i]=record(i,{lands:[0,0,1,1,2,2],candidateTurns:[],
      opening:["Sol Ring","Dark Ritual","Cabal Ritual","Vampiric Tutor","Pestilence","Night's Whisper","Reanimate"]});
    strong[i]=record(i);
  }
  const weakFinding=findings(summarize(weak)),strongFinding=findings(summarize(strong));
  assert.notEqual(weakFinding[0].summary,strongFinding[0].summary);
  assert.notEqual(weakFinding[1].meaning,strongFinding[1].meaning);
  assert.match(weakFinding[1].summary,/0 of 11/);
  assert.match(strongFinding[2].summary,/11 of 11/);
  assert.ok(weakFinding.every(f=>f.caveat.length>15));
  assert.ok(!weakFinding.some(f=>/win rate|games won|victory chance|cast successfully/i.test(f.summary+" "+f.meaning)));
});

test("supports zero candidates, variable archive size and incomplete records",()=>{
  assert.equal(summarize({}),null);
  assert.equal(summarize({"0":{mode:"game",trace:[]}}),null);
  const one=summarize({"9":record(9,{lands:[1,1,2,2,2,3],candidateTurns:[]})});
  assert.equal(one.n,1);
  assert.equal(one.metrics.t3Sources.count,0);
  assert.equal(one.metrics.t4Candidate.pct,0);
  assert.equal(one.candidateGroups[0].value,0);
  assert.deepEqual(one.candidateGroups[3].seeds,[]);
});

test("different per-seed observations map to drilldown groups with exact seed IDs",()=>{
  const data=summarize({
    "4":record(4,{lands:[1,1,1,2,3,4],candidateTurns:[]}),
    "7":record(7,{lands:[1,2,3,4,5,6],candidateTurns:[2,3,4]})
  });
  assert.deepEqual(data.turn3Groups.find(x=>x.label==="1").seeds,["4"]);
  assert.deepEqual(data.turn3Groups.find(x=>x.label==="3").seeds,["7"]);
  assert.deepEqual(data.candidateGroups[3].seeds,["7"]);
  assert.deepEqual(data.candidateGroups[3].absent,["4"]);
  assert.equal(data.metrics.t3Sources.pct,50);
});
