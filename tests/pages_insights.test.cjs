"use strict";
const assert=require("node:assert/strict");
const test=require("node:test");
const insights=require("../web/pages/results_insights.js");
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

test('discovers reusable subtype, rules-text and spell-type signals with cumulative draws',()=>{
  const {themes}=require('../web/pages/results_insights.js');
  const cards={z:{type_line:'Creature — Zombie',oracle_text:'A creature.'},
    a:{type_line:'Enchantment',oracle_text:'Zombie creatures you control get +1/+1.'},
    i:{type_line:'Instant',oracle_text:'Draw a card.'},
    s:{type_line:'Sorcery',oracle_text:'Draw two cards.'}};
  const entries=[{name:'Dead',oracle_id:'z',qty:2},{name:'Banner',oracle_id:'a',qty:1},
    {name:'Spark',oracle_id:'i',qty:2},{name:'Burst',oracle_id:'s',qty:1}];
  const run=(seed,opening,draws)=>({mode:'observation',seed,opening_hand:opening,
    trace:draws.map((drawn,i)=>({turn:i+1,drawn}))});
  const runs={1:run(1,['Dead'],['Spark','Other','Other','Other','Other','Other']),
    2:run(2,['Other'],['Other','Other','Banner','Other','Other','Other']),
    3:run(3,['Other'],['Other','Other','Other','Other','Other','Other'])};
  const result=themes(entries,cards,runs,{type_line:'Creature — Human Wizard',oracle_text:'Create a Zombie creature token.'});
  const zombie=result.find(g=>g.label==='Zombie');
  assert.equal(zombie.copies,3);assert.equal(zombie.sample,3);assert.equal(zombie.commanderMatch,true);
  assert.deepEqual([zombie.opening,zombie.byTurn3,zombie.byTurn6],[1,2,2]);
  assert.deepEqual(zombie.cards.map(c=>c.name),['Dead','Banner']);
  assert.equal(result.find(g=>g.id==='spells').copies,3);
  assert.deepEqual([result.find(g=>g.id==='spells').opening,result.find(g=>g.id==='spells').byTurn3],[0,1]);
  delete runs[3].trace[2].drawn;
  assert.equal(themes(entries,cards,runs,null).find(g=>g.label==='Zombie').sample,2);
  assert.equal(themes(entries,cards,null,null).find(g=>g.label==='Zombie').sample,0);
});

test('source curve points preserve each seed and its turn-specific sources',()=>{
  const {sourceTimeline}=require('../web/pages/results_insights.js');
  const a=record(4,{lands:[1,2,3,4,5,6]});
  const b=record(7,{lands:[0,1,1,2,2,3]});
  b.trace[2].modeled_sources=[{card:'Command Tower',colors:['B','U']}];
  const timeline=sourceTimeline(summarize({4:a,7:b}));
  assert.equal(timeline.length,6);
  assert.equal(timeline[2].turn,3);assert.equal(timeline[2].mean,2);
  assert.deepEqual(timeline[2].runs.map(x=>[x.seed,x.count]),[['4',3],['7',1]]);
  assert.deepEqual(timeline[2].runs[1].cards,['Command Tower']);
  assert.deepEqual(sourceTimeline(null),[]);
});

test('theme story compares cumulative first appearances across distinct themes',()=>{
  const {themeTimelines}=require('../web/pages/results_insights.js');
  const run=(seed,opening,draws)=>({mode:'observation',seed,opening_hand:opening,
    trace:draws.map((drawn,i)=>({turn:i+1,drawn}))});
  const records={1:run(1,['Zombie A'],['Other','Wizard A','Other','Other','Other','Other']),
    2:run(2,['Other'],['Other','Other','Zombie A','Other','Other','Other']),
    3:run(3,['Other'],['Other','Other','Other','Other','Other','Other'])};
  const groups=[{id:'z',label:'Zombie',kind:'Subtype',copies:1,cards:[{name:'Zombie A'}]},
    {id:'w',label:'Wizard',kind:'Subtype',copies:1,cards:[{name:'Wizard A'}]}];
  const lines=themeTimelines(groups,records);
  assert.equal(lines[0].points[0].count,1);assert.equal(lines[0].points[2].count,1);
  assert.equal(lines[0].points[3].count,2);assert.equal(lines[0].points[3].pct,67);
  assert.deepEqual(lines[0].points[3].matches.map(x=>[x.seed,x.turn,x.card]),[['1',0,'Zombie A'],['2',3,'Zombie A']]);
  assert.equal(lines[1].points[1].count,0);assert.equal(lines[1].points[2].count,1);
  delete records[3].trace[5].drawn;assert.equal(themeTimelines(groups,records)[0].sample,2);
  assert.deepEqual(themeTimelines(groups,{}),[]);
});
test('quiet-turn analysis uses consecutive recorded actions and exposes unsupported hands',()=>{
  const {quietTurns}=require('../web/pages/results_insights.js');
  function run(seed,events,unsupported){return {mode:'bounded_authoritative_early_actions',deck_key:'d',deck_sha256:'abc',seed,mulligan:{policy:'one-free'},
    events:events.map((types,i)=>({turn:i+1,events:types.map(type=>({type})),unsupported_cards_in_hand:unsupported[i],land_count:1,hand_size:2})),
    state_snapshots:events.map((_,i)=>({turn:i+1,hand:['Spell','Land'],battlefield:['Land']}))}}
  const runs=[run(1,[['draw'],['draw'],['land_play']], [['Spell'],['Spell'],[]]),
    run(2,[['land_play'],['tutor_resolved'],['draw']], [[],[],[]]),
    run(3,[['draw'],['reviewed_trigger_resolved'],['draw']], [[],[],[]])];
  const points=quietTurns(runs,'d','abc');
  assert.equal(points[0].turn,2);assert.equal(points[0].count,1);assert.equal(points[0].uncertain,1);
  assert.equal(points[0].examples[0].seed,1);assert.deepEqual(points[0].examples[0].hand,['Spell','Land']);
  assert.equal(points[1].count,0);
  assert.throws(()=>quietTurns(runs,'other','abc'),/match/);
  assert.throws(()=>quietTurns([runs[0],runs[0]],'d','abc'),/distinct/);
  assert.throws(()=>quietTurns([{mode:'observation'}],'d','abc'));
});

test('quiet detection counts enchantments, phase effects and sacrifices as recorded actions',()=>{
  const {quietTurns}=require('../web/pages/results_insights.js');
  const run=(seed,type)=>({mode:'bounded_authoritative_early_actions',deck_key:'d',deck_sha256:'h',seed,mulligan:{policy:'one-free'},
    events:[{turn:1,events:[],unsupported_cards_in_hand:[],land_count:0,hand_size:0},
      {turn:2,events:[{type}],unsupported_cards_in_hand:[],land_count:0,hand_size:0}],
    state_snapshots:[1,2].map(turn=>({turn,hand:[],battlefield:[]}))});
  const points=quietTurns(['enchantment_resolved','reviewed_phase_resolved','reviewed_sacrifice_activated','draw'].map((t,i)=>run(i,t)),'d','h');
  assert.equal(points[0].count,1);assert.equal(points[0].examples[0].seed,3);
});

// Battlefield prevalence counts runs, retains overlapping types, and never guesses unknown objects.
{
  const cards={Golem:{type_line:'Artifact Creature — Golem'}, Island:{type_line:'Basic Land — Island'}};
  const mk=(seed,board)=>({seed,state_snapshots:[{turn:1,battlefield:board}]});
  const runs=[mk(1,['Golem','Golem','Mystery']),mk(2,['Island'])];
  const creature=insights.boardDevelopment(runs,n=>cards[n]||null,'Creature',1);
  assert.equal(creature.rows[0].pct,50);
  assert.equal(creature.rows[0].mean,1);
  assert.deepEqual(creature.cards,[['Golem',1]]);
  assert.equal(creature.unknown,1);
  assert.deepEqual(creature.examples.map(r=>r.seed),[1]);
  assert.equal(insights.boardDevelopment(runs,n=>cards[n]||null,'Artifact',1).rows[0].pct,50);
}

test('land development reports interpolated quartiles and exact matching cohorts',()=>{
  const make=(seed,n)=>({seed,events:Array.from({length:6},(_,i)=>({turn:i+1,land_count:n})),state_snapshots:Array.from({length:6},()=>({battlefield:[],hand:[]}))});
  const report=insights.landDevelopment([make(0,1),make(1,2),make(2,4),make(3,5)],6);
  assert.equal(report.total,4);assert.equal(report.timeline[5].median,3);
  assert.equal(report.timeline[5].q1,1.75);assert.equal(report.timeline[5].q3,4.25);
  assert.deepEqual(report.groups.map(g=>[g.count,g.runs.map(r=>r.seed)]),[[1,[0]],[2,[1]],[4,[2]],[5,[3]]]);
  assert.equal(insights.landDevelopment([{}],6).total,0);
});
