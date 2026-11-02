'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Replay=require('../web/pages/replay.js');

function fixture(){
  return {
    format:Replay.FORMAT,schema_version:1,deck_key:'mortarion_physical_final',
    deck_sha256:'a'.repeat(64),source:{workflow_run_id:41444353902},
    fidelity:{opponent_life_snapshots:false},
    scenarios:{
      balanced:{summary:{seeds:24,survived_by_horizon:24},
        games:[{id:'balanced:0',seed:0,scenario:'balanced',
          seats:[{seat:0,role:'pilot'},{seat:1,role:'aggro'},{seat:2,role:'control'},{seat:3,role:'value'}],
          rounds:[{round:1,snapshots:{'0':{life:40,lands:1,creatures:0,hand_size:7}},
            actions:[
              {type:'land_play',actor_seat:0,target_seat:null,card_name:'Swamp',fields:{type:'land_play',card:'Swamp'}},
              {type:'opponent_abstract_unblocked_damage',actor_seat:1,target_seat:0,
               card_name:null,fields:{type:'opponent_abstract_unblocked_damage',seat:1,target_seat:0,amount:2}},
              {type:'opponent_life_zero',actor_seat:null,target_seat:null,
               affected_seat:3,fields:{type:'opponent_life_zero',seat:3,target_seat:null}}
            ]}]}]}
    }
  };
}

test('v1 replay requires exact deck hash and supported schema',()=>{
  const data=fixture();
  assert.equal(Replay.validate(data,data.deck_key,data.deck_sha256),data);
  assert.throws(()=>Replay.validate(data,data.deck_key,'b'.repeat(64)),/pinned revision/);
  assert.throws(()=>Replay.validate({...data,schema_version:2},data.deck_key,data.deck_sha256),/Unsupported/);
});

test('four-seat actions retain actor/target and do not infer hidden opponents',()=>{
  const round=fixture().scenarios.balanced.games[0].rounds[0];
  assert.equal(Replay.statsForRound(round,0).life,40);
  assert.equal(Replay.statsForRound(round,1),null);
  assert.equal(Replay.activity(round,0),1);
  assert.equal(Replay.activity(round,1),1);
  assert.equal(Replay.activity(round,3),0);
  assert.match(Replay.summarizeAction(round.actions[1]),/Seat 1.*2 abstract unblocked damage.*Seat 0/);
  assert.match(Replay.summarizeAction(round.actions[2]),/Seat 3 reached zero life/);
  assert.equal(Replay.eventKind(round.actions[0]),'land');
});

test('source UI includes optional replay renderer without removing established simulation panels',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  const app=fs.readFileSync('web/pages/app.js','utf8');
  const builder=fs.readFileSync('tools/build_pages_deck_lab.py','utf8');
  assert.match(html,/<script src="\.\/replay\.js\?v=[^"]+" defer><\/script>/);
  assert.match(html,/id="opponent-replay-panel"/);
  assert.match(html,/id="bounded-results"/);
  assert.match(html,/id="quiet-output"/);
  assert.match(html,/id="archive-observation-details"/);
  assert.match(app,/function renderReplay\(\)/);
  assert.match(app,/CommanderReplay\.render\(root,payload/);
  assert.match(builder,/replay-data/);
});

test('published replay file, when present, exposes only actual sampled games',()=>{
  const path='web/pages/data/replays/mortarion-opponent-pressure.v1.json';
  if(!fs.existsSync(path))return;
  const replay=JSON.parse(fs.readFileSync(path,'utf8'));
  assert.equal(replay.format,Replay.FORMAT);
  assert.equal(replay.source.workflow_run_id,41444353902);
  assert.equal(Object.keys(replay.scenarios).length,5);
  assert.equal(Object.values(replay.scenarios).reduce((n,r)=>n+r.games.length,0),14);
  for(const s of Object.values(replay.scenarios)){
    for(const game of s.games)for(const r of game.rounds){
      assert.deepEqual(Object.keys(r.snapshots),['0']);
      assert.ok(r.actions.every(e=>e.fidelity==='reviewed'||e.fidelity==='abstract'));
    }
  }
});


test('replay DOM renders four seats, measured pilot only, actual event details and optional verified card art',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.attributes={};this.className='';}
    append(...nodes){this.children.push(...nodes)}
    appendChild(node){this.children.push(node);return node}
    replaceChildren(...nodes){this.children=[...nodes]}
    setAttribute(name,value){this.attributes[name]=value}
  }
  const previous=global.document;
  global.document={createElement:tag=>new Node(tag)};
  try{
    const root=new Node('div'),input=fixture();
    const opened=[];
    Replay.render(root,input,{deckKey:input.deck_key,deckHash:input.deck_sha256,
      lookup:name=>name==='Swamp'?{name:'Swamp',oracle_id:'swamp-id',art:'https://example.invalid/swamp.jpg'}:null,
      openCard:id=>opened.push(id)});
    const walk=node=>[node,...(node.children||[]).flatMap(walk)];
    const nodes=walk(root),texts=nodes.map(x=>x.textContent).filter(Boolean);
    assert.ok(texts.some(x=>x.includes('Mortarion · You')));
    assert.ok(texts.some(x=>x.includes('Seat 3 · value')));
    assert.ok(texts.some(x=>x.includes('Life not recorded')));
    assert.ok(texts.some(x=>x.includes('40 life')));
    assert.ok(texts.some(x=>x.includes('Seat 1 applied 2 abstract unblocked damage')));
    assert.ok(texts.some(x=>x.includes('Seat 3 reached zero life')));
    const art=nodes.find(x=>x.tag==='img');
    assert.equal(art.src,'https://example.invalid/swamp.jpg');
    const button=nodes.find(x=>x.className==='replay-card-art');
    button.onclick();
    assert.deepEqual(opened,['swamp-id']);
  }finally{global.document=previous}
});
