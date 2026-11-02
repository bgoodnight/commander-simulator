'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Outcomes=require('../web/pages/game_outcomes.js');
const Replay=require('../web/pages/replay.js');

const totals=values=>Object.fromEntries(values.map((v,i)=>[String(i),v]));
function history(rounds){
  return rounds.map((values,round)=>({
    round,life_totals:totals(values),
    alive_seats:values.map((v,i)=>v>0?i:null).filter(x=>x!==null),
    life_changes:round===0?[]:[{seat:0,kind:'loss',amount:Math.max(0,rounds[round-1][0]-values[0]),
      delta:values[0]-rounds[round-1][0],before:rounds[round-1][0],after:values[0],
      source_object_id:null}],
    new_eliminations:[]
  }));
}
function run(seed,status,rounds,roles={"1":"aggro","2":"value","3":"control"},extras={}){
  return {seed,opponent_roles:roles,completed_rounds:rounds.length-1,
    outcome:{status,requested_rounds:3,completed_rounds:rounds.length-1,
      complete:status!=='unresolved',winner_seat:status==='win'?0:null},
    life_history:history(rounds),...extras};
}
function batch(runs,scenario='mixed',extras={}){
  return {format:Outcomes.FORMAT,schema_version:1,
    deck_key:'necron_dynasties',deck_sha256:'a'.repeat(64),
    scenario,seed_count:runs.length,requested_rounds:3,
    opponent_fidelity:'abstract_opponent_pressure_not_card_exact',
    outcomes_are_competitive_win_rates:false,runs,...extras};
}
const runWon=()=>run(0,'win',[
  [40,40,40,40],[36,26,28,29],[32,0,0,0]
]);
const runUnresolved=()=>run(1,'unresolved',[
  [40,40,40,40],[35,38,39,40],[20,12,23,30],[18,9,20,26]
]);
const runLost=()=>run(2,'loss',[
  [40,40,40,40],[30,36,35,40],[0,29,34,40]
]);
test('strict long-game schema prevents goldfish or mislabelled rates from masquerading as matches',()=>{
  assert.equal(Outcomes.validate(batch([runWon()])),true);
  assert.equal(Outcomes.validate({...batch([runWon()]),outcomes_are_competitive_win_rates:true}),false);
  assert.equal(Outcomes.validate({...batch([runWon()]),opponent_fidelity:'goldfish_no_opponents'}),false);
  assert.equal(Outcomes.validate({...batch([runWon()]),format:'commander-bounded-archive-v1'}),false);
  assert.equal(Outcomes.validate(batch([runWon(),runWon()])),false); // duplicate seed
  const wrong=runWon();wrong.life_history[1].life_totals={"0":36,"1":40};
  assert.equal(Outcomes.validate(batch([wrong])),false);
  assert.equal(Outcomes.model([batch([runWon()])],'necron_dynasties','b'.repeat(64)).totalGames,0);
});
test('life trends retain denominators after early finishes and interquartile bands',()=>{
  const t=Outcomes.lifeTrend([runWon(),runUnresolved()],3);
  assert.deepEqual(t.map(x=>x.observed),[2,2,2,1]);
  assert.equal(t[1].seats[0].median,35.5);
  assert.equal(t[1].seats[0].p25,35.25);
  assert.equal(t[1].seats[0].p75,35.75);
  assert.equal(t[2].seats[1].alive,1);
  assert.equal(t[3].seats[0].median,18);
  assert.equal(t[3].seats[0].alive,1);
});
test('unresolved rounds are never added to modeled losses; duplicates do not inflate counts',()=>{
  const x=batch([runWon(),runUnresolved()]);
  const r=Outcomes.model([x,x],'necron_dynasties','a'.repeat(64));
  assert.equal(r.sourceBatches,2);
  assert.equal(r.duplicates,2);
  assert.equal(r.totalGames,2);
  assert.equal(r.groups[0].counts.win,1);
  assert.equal(r.groups[0].counts.loss,0);
  assert.equal(r.groups[0].counts.unresolved,1);
  assert.equal(r.groups[0].terminal,1);
  assert.equal(r.groups[0].life[3].observed,1);
});
test('abstract opponent roles remain scenarios, and named decks use whole-pod associations',()=>{
  const a=batch([runWon(),runUnresolved()],'mixed');
  const b=batch([runLost()],'aggressive');
  const model=Outcomes.model([a,b],'necron_dynasties','a'.repeat(64));
  assert.equal(model.groups.length,2);
  let rows=Outcomes.matchupRows(model.groups);
  assert.equal(rows.length,2);
  assert.ok(rows.every(x=>x.kind==='abstract'));
  assert.ok(rows.every(x=>/abstract policies/.test(x.label)));
  assert.equal(rows[0].counts.win,1);
  const newRoles=runUnresolved();
  newRoles.opponent_roles={"1":"control","2":"aggro","3":"value"};
  const rolled=Outcomes.model(
    [batch([runWon(),newRoles])],'necron_dynasties','a'.repeat(64));
  assert.equal(rolled.groups.length,1);
  assert.match(rolled.groups[0].label,/mixed opponent roles/);
  const tagged=batch([runWon(),runUnresolved()],'mixed',{
    opponent_decks:[
      {seat:1,deck_key:'death_guard',commander_name:'Mortarion'},
      {seat:2,deck_key:'magnus',commander_name:'Magnus'},
      {seat:3,deck_key:'gisa',commander_name:'Gisa'}
    ]
  });
  const enriched=Outcomes.model([tagged],'necron_dynasties','a'.repeat(64));
  assert.equal(enriched.groups[0].deckRoster.length,3);
  rows=Outcomes.matchupRows(enriched.groups);
  assert.equal(rows.length,3);
  assert.ok(rows.every(row=>row.kind==='named'));
  assert.equal(rows[0].games,2);
  assert.ok(rows.some(row=>row.label.includes('Mortarion')));
});
test('modeled panels expose distinct outcome, life and matchup disclosures with clickable seeds',()=>{
  class Node{
    constructor(tag){
      this.tag=tag;this.className='';this.textContent='';this.children=[];
      this.attributes={};this.style={};this.events={};this.dataset={};
    }
    append(...n){this.children.push(...n)}
    appendChild(n){this.children.push(n);return n}
    replaceChildren(...n){this.children=[...n]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,fn){this.events[k]=fn}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:t=>new Node(t),createElementNS:(_,t)=>new Node(t)};
  try{
    const root=new Node('main');
    const report=Outcomes.render(root,[batch([runWon(),runUnresolved()])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64)
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    let nodes=walk(root);
    assert.equal(report.totalGames,2);
    assert.equal(nodes.filter(n=>n.className==='board-report game-outcome-card').length,3);
    assert.ok(nodes.some(n=>n.tag==='svg'&&n.attributes.role==='img'));
    assert.ok(nodes.some(n=>n.textContent==='1 / 2 wins'));
    assert.ok(nodes.some(n=>String(n.textContent).includes('Only one opponent group')));
    const seed=nodes.find(n=>n.tag==='button'&&n.className==='game-outcome-seed');
    assert.ok(seed);seed.onclick();
    nodes=walk(root);
    assert.ok(nodes.some(n=>n.textContent==='Round 2 · 1 of 4 seats alive'));
  }finally{global.document=before}
});
test('results page and exporter wire a future published manifest and local JSON',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  const app=fs.readFileSync('web/pages/app.js','utf8');
  const build=fs.readFileSync('tools/build_pages_deck_lab.py','utf8');
  assert.match(html,/id="long-game-panel"/);
  assert.match(html,/id="game-outcome-files"/);
  assert.match(html,/game_outcomes\.js/);
  assert.match(app,/loadLongGameFiles/);
  assert.match(app,/loadPublishedLongGame/);
  assert.match(app,/renderLongGamePanel/);
  assert.match(build,/outcome_assets/);
  assert.match(build,/outcomes_are_competitive_win_rates/);
  assert.equal(typeof Replay.renderBoundedEvidence,'function');
});
