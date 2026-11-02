'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Catalog=require('../web/pages/insight_catalog.js');
const Explorer=require('../web/pages/insight_explorer.js');
const Replay=require('../web/pages/replay.js');

const types={'Sol Ring':'Artifact','Arcane Signet':'Artifact','Ponder':'Sorcery',
 'Faithless Looting':'Sorcery','Opt':'Instant','Counterspell':'Instant',
 'Bastion of Remembrance':'Enchantment','Phyrexian Arena':'Enchantment',
 'Mana Geyser':'Sorcery','Bad Spell':'Sorcery','No-Cast Spell':'Sorcery',
 'Swamp':'Basic Land','Bile Blight':'Instant','Feed the Swarm':'Sorcery'};
const lookup=name=>types[name]?{name,oracle_id:name,type_line:types[name],
 mana_cost:'{2}{B}',art:'https://example.invalid/art',image:'https://example.invalid/card'}:null;
const event=(type,card)=>({type,card});
function run(seed,turns,opening=[]){
 return {seed,deck_key:'test',deck_sha256:'a'.repeat(64),
  mulligan:{opening_hand:opening},
  events:turns.map((t,i)=>({turn:i+1,events:t.events||[],
   unsupported_cards_in_hand:t.unsupported||[]})),
  state_snapshots:turns.map((t,i)=>({turn:i+1,hand:t.hand||[],
   battlefield:t.battlefield||[]}))};
}
test('common types show only proven casts/plays with relevant distinct contenders',()=>{
 const runs=Array.from({length:6},(_,i)=>run(i,[{events:[
  ...(i<4?[event('artifact_resolved','Sol Ring'),event('reviewed_draw_spell_cast','Ponder'),
     event('reviewed_draw_spell_cast','Opt')]:[]),
  ...(i>=2?[event('artifact_resolved','Arcane Signet'),
    event('tutor_cast','Faithless Looting'),event('reviewed_instant_response','Counterspell')]:[]),
  event('reviewed_enter_resolved','Bad Spell')
 ],hand:['Mana Geyser']}]));
 for(const [type,winner] of [['Artifact','Sol Ring'],['Sorcery','Ponder'],['Instant','Opt']]){
  const m=Catalog.commonPlayedByType(runs,lookup,type);
  assert.ok(m,type+' should qualify');
  assert.equal(m.contenders[0].name,winner);
  assert.equal(m.contenders[0].score,4);
  assert.equal(m.contenders.length,2);
  assert.equal(m.contenders[0].metrics.find(x=>x.id==='total').value,'4');
 }
 assert.equal(Catalog.commonPlayedByType(runs,lookup,'Creature'),null);
 assert.equal(Catalog.commonPlayedByType(runs,lookup,'Enchantment'),null);
 assert.equal(Catalog.commonPlayedByType(runs,lookup,'Planeswalker'),null);
});
function hands(){
 return [
  run(0,[{hand:['Mana Geyser','Bad Spell']},
   {hand:['Mana Geyser','Bad Spell'],events:[event('source_paid_candidate','Mana Geyser')]},
   {hand:['Mana Geyser','Bad Spell'],events:[event('source_paid_candidate','Mana Geyser')]}]),
  run(1,[{hand:['Mana Geyser','Bad Spell']},
   {hand:['Mana Geyser','Bad Spell'],events:[event('source_paid_candidate','Mana Geyser')]},
   {hand:['Mana Geyser'],events:[event('source_paid_candidate','Bad Spell')]}]),
  run(2,[{hand:['Bad Spell']},{hand:['Bad Spell']},{hand:[]}]),
  run(3,[{hand:['Bad Spell']},{hand:[]},{hand:[]}])
 ];
}
test('held hand residence is separate from source-paid cost preview and discarded cards',()=>{
 const m=Catalog.heldInHand(hands(),lookup);
 assert.equal(m.id,'held-in-hand');
 assert.deepEqual(m.views.map(x=>x.id),['held','payable']);
 const a=m.contenders.find(x=>x.name==='Mana Geyser');
 const b=m.contenders.find(x=>x.name==='Bad Spell');
 assert.equal(a.score,5);
 assert.equal(a.viewScores.payable,3);
 assert.equal(b.viewScores.payable,0);
 assert.equal(a.metrics.find(x=>x.id==='payable').examples[0].focusTopic,'hand');
 assert.match(a.metrics.find(x=>x.id==='payable').explanation,/not evidence of legal timing/i);
 const without=hands().map(r=>({...r,events:r.events.map(t=>({
  ...t,events:t.events.filter(e=>e.type!=='source_paid_candidate')}))}));
 assert.equal(Catalog.heldInHand(without,lookup).views.length,1);
});
test('unused only means no observed play within bounded horizon',()=>{
 const runs=Array.from({length:4},(_,i)=>run(i,[
  {events:[event('draw','Bad Spell')],hand:['Bad Spell','No-Cast Spell'],
   unsupported:['Bad Spell','No-Cast Spell']},
  {events:[i===0?event('tutor_cast','Mana Geyser'):event('draw','Mana Geyser')],
   hand:['Bad Spell','No-Cast Spell','Mana Geyser']},
  {hand:['Bad Spell','No-Cast Spell','Mana Geyser']}
 ]));
 const m=Catalog.leftUnplayed(runs,lookup);
 assert.ok(m);
 assert.equal(m.contenders[0].score,4);
 assert.equal(m.contenders.find(x=>x.name==='Bad Spell').metrics
  .find(x=>x.id==='coverage').value,'4 runs');
 assert.equal(m.contenders.find(x=>x.name==='Mana Geyser').score,3);
});
function replay(){
 return {format:Replay.FORMAT,schema_version:1,deck_key:'test',
  deck_sha256:'a'.repeat(64),source:{workflow_run_id:12},seeds_per_scenario:24,
  scenarios:{balanced:{summary:{seeds:24},games:[{
   id:'balanced:0',seed:0,scenario:'balanced',
   seats:[{seat:0,label:'Pilot',role:'pilot'}],
   rounds:[{round:1,snapshots:{'0':{life:40,lands:1,creatures:1,hand_size:2}},
    actions:[
     {actor_seat:0,card_name:'Bile Blight',type:'reviewed_removal_resolved',
      fidelity:'reviewed',fields:{destroyed_count:2}},
     {actor_seat:0,card_name:'Feed the Swarm',type:'reviewed_removal_resolved',
      fidelity:'reviewed',fields:{destroyed_count:1}},
     {actor_seat:0,card_name:null,type:'player_abstract_unblocked_damage',
      fidelity:'abstract',target_seat:1,fields:{amount:8}}
    ]}]
  }]}}};
}
test('source impacts hide unproven damage and kills, distinguish narrated samples',()=>{
 const p=replay(),insights=Catalog.verifiedImpact(p,lookup);
 assert.deepEqual(insights.map(x=>x.id),['permanents-destroyed']);
 assert.equal(insights[0].total,1);
 assert.equal(insights[0].contenders[0].score,2);
 const ex=insights[0].contenders[0].metrics[0].examples[0];
 assert.deepEqual([ex.source,ex.scenario,ex.seed,ex.turn,ex.eventIndex],
  ['opponent_replay','balanced',0,1,0]);
 const actions=p.scenarios.balanced.games[0].rounds[0].actions;
 actions.push(
  {actor_seat:0,card_name:'Bile Blight',type:'reviewed_player_damage',
   fidelity:'reviewed',target_seat:1,fields:{amount:4}},
  {actor_seat:0,card_name:'Feed the Swarm',type:'reviewed_player_damage',
   fidelity:'reviewed',target_seat:2,fields:{amount:3}});
 assert.deepEqual(Catalog.verifiedImpact(p,lookup).map(x=>x.id),
  ['direct-player-damage','permanents-destroyed']);
 actions.push(
  {actor_seat:0,card_name:'Bile Blight',type:'reviewed_removal_resolved',
   fidelity:'reviewed',fields:{creatures_killed:2,destroyed_count:2}},
  {actor_seat:0,card_name:'Feed the Swarm',type:'reviewed_creature_kill',
   fidelity:'reviewed',fields:{creatures_killed:1}});
 assert.ok(Catalog.verifiedImpact(p,lookup).some(x=>x.id==='creature-kills'));
});
test('rank-mode graph toggles payable only when measurements exist',()=>{
 class Node{
  constructor(tag){this.tag=tag;this.className='';this.children=[];
   this.attributes={};this.textContent='';this.style={};}
  append(...n){this.children.push(...n)}
  appendChild(n){this.children.push(n);return n}
  replaceChildren(...n){this.children=[...n]}
  setAttribute(k,v){this.attributes[k]=v}
 }
 const old=global.document;global.document={createElement:t=>new Node(t)};
 try{
  const model=Catalog.heldInHand(hands(),lookup),opened=[];
  const ui=Explorer.render(model,{onRenderEvidence:(root,ex)=>{
   opened.push([ex.seed,ex.turn]);root.appendChild(new Node('span'));
  }});
  const walk=n=>[n,...n.children.flatMap(walk)];
  let items=walk(ui);
  const modes=items.filter(n=>n.tag==='button'&&n.className.startsWith('insight-ranking-view'));
  assert.equal(modes.length,2);modes[1].onclick();
  items=walk(ui);
  assert.ok(items.some(n=>n.className==='insight-card-name'&&n.textContent==='Mana Geyser'));
  const metric=items.find(n=>n.tag==='button'&&n.className.startsWith('insight-metric')&&
   n.children[1]?.textContent==='Cost-payable turns');
  metric.onclick();
  assert.deepEqual(opened,[[0,2]]);
 }finally{global.document=old}
});
test('shell loads conditional catalog and inline narration hooks',()=>{
 const html=fs.readFileSync('web/pages/index.html','utf8');
 const app=fs.readFileSync('web/pages/app.js','utf8');
 const build=fs.readFileSync('tools/build_pages_deck_lab.py','utf8');
 assert.match(html,/insight_catalog\.js/);
 assert.match(app,/catalog\.heldInHand/);
 assert.match(app,/DeckInsightCatalog\.verifiedImpact/);
 assert.match(app,/renderNarratedEvidence/);
 assert.match(build,/insight_catalog\.js/);
 assert.equal(typeof Replay.renderNarratedEvidence,'function');
});
