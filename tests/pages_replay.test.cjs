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
          seats:[{seat:0,label:'Mortarion',role:'pilot'},{seat:1,label:'Seat 1',role:'aggro'},{seat:2,label:'Seat 2',role:'control'},{seat:3,label:'Seat 3',role:'value'}],
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
  assert.ok(Number.isInteger(replay.source.workflow_run_id)&&
    replay.source.workflow_run_id>0);
  assert.match(replay.source.engine_commit,/^[a-f0-9]{40}$/);
  assert.match(replay.deck_sha256,/^[a-f0-9]{64}$/);
  if(replay.source.workflow_run_id!==41444353902){
    const rounds=Object.values(replay.scenarios).flatMap(x=>x.games.flatMap(g=>g.rounds));
    assert.ok(rounds.every(r=>r.snapshots['0'].zones));
    assert.ok(rounds.every(r=>Array.isArray(r.mana_activations)));
    assert.ok(rounds.some(r=>r.actions.some(a=>a.type==='draw')));
  }
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


test('round summaries calculate net changes without inventing mana, tokens or causes',()=>{
  const past={round:3,snapshots:{"0":{life:39,lands:3,creatures:4,hand_size:5}},actions:[]};
  const now={round:4,snapshots:{"0":{life:33,lands:4,creatures:2,hand_size:3}},actions:[
    {type:'land_play',card_name:'Swamp',actor_seat:0,target_seat:null,fields:{card:'Swamp'}},
    {type:'reviewed_removal_resolved',card_name:'Infernal Grasp',actor_seat:0,target_seat:1,
      fields:{type:'reviewed_removal_resolved',destroyed_count:1}},
    {type:'opponent_abstract_unblocked_damage',card_name:null,actor_seat:2,target_seat:0,
      fields:{type:'opponent_abstract_unblocked_damage',amount:3}},
    {type:'opponent_abstract_destroy',card_name:null,actor_seat:1,target_seat:0,
      fields:{type:'opponent_abstract_destroy',amount:0}}
  ]};
  assert.equal(Replay.changeIn(now,past,'life'),-6);
  assert.equal(Replay.changeIn(now,past,'creatures'),-2);
  assert.equal(Replay.changeIn(now,past,'lands'),1);
  assert.equal(Replay.changeIn(now,past,'hand_size'),-2);
  assert.equal(Replay.changeIn(now,null,'life'),null);
  assert.deepEqual(Replay.recordedCombat(now),{dealt:0,taken:3,blocks:0,defended:0});
  assert.deepEqual(Replay.relatedActions(now,'creatures').map(x=>x.type),
    ['reviewed_removal_resolved','opponent_abstract_destroy']);
  const spot=Replay.cardSpotlight(now,name=>
    name==='Infernal Grasp'?{name,oracle_id:'id',art:'https://example.invalid/art.jpg'}:null);
  assert.equal(spot.card.name,'Infernal Grasp');
  assert.equal(Replay.cardSpotlight({actions:[now.actions[2]]},()=>null).card,null);
  assert.equal(Replay.statsForRound(now,2),null);
});

test('simulation layout preserves prior reports and adds accessible takeaway and turn drilldown structure',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const app=fs.readFileSync('web/pages/app.js','utf8');
  const replay=fs.readFileSync('web/pages/replay.js','utf8');
  assert.match(html,/id="development-panel"/);
  assert.match(html,/id="opponent-replay-panel"/);
  assert.match(html,/id="bounded-results"/);
  assert.match(html,/id="quiet-output"/);
  assert.match(html,/id="archive-observation-details"/);
  assert.match(replay,/replay-takeaway-summary/);
  assert.match(replay,/replay-turn-summary/);
  assert.match(replay,/replay-focus-choices/);
  assert.match(replay,/replay-playbyplay/);
  assert.match(replay,/replay-table-context/);
  assert.match(css,/#pane-records\[hidden\]\{display:none!important\}/);
  assert.doesNotMatch(app,/development\.open=true/);
  assert.match(html,/id="key-insights-panel"/);
});


test('chronological turn summary includes recorded draws, plays and responses but not duplicate resolves',()=>{
  const round={round:3,actions:[
    {type:'draw',actor_seat:0,card_name:'Sol Ring'},
    {type:'land_play',actor_seat:0,card_name:'Swamp'},
    {type:'artifact_cast',actor_seat:0,card_name:'Sol Ring'},
    {type:'artifact_resolved',actor_seat:0,card_name:'Sol Ring'},
    {type:'reviewed_instant_response',actor_seat:0,card_name:'Undying Malice'},
    {type:'opponent_abstract_destroy',actor_seat:1,target_seat:0},
    {type:'cleanup_discard',actor_seat:0,card_name:'Pestilence'}
  ]};
  assert.deepEqual(Replay.pilotTurnActivity(round),[
    'drew Sol Ring','played Swamp','cast Sol Ring',
    'responded with Undying Malice','discarded Pestilence'
  ]);
  assert.deepEqual(Replay.pilotTurnActivity({actions:[
    {type:'opponent_abstract_creature',actor_seat:2}] }),[]);
});

test('exact pilot hand, creatures and committed mana sources render only where recorded',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.className='';this.textContent='';this.attributes={};}
    append(...nodes){this.children.push(...nodes)}
    appendChild(node){this.children.push(node);return node}
    setAttribute(name,value){this.attributes[name]=value}
  }
  const old=global.document;global.document={createElement:tag=>new Node(tag)};
  const opened=[];
  const lookup=name=>{
    const types={'Swamp':'Basic Land — Swamp','Sol Ring':'Artifact',
      'Mortarion, Daemon Primarch':'Legendary Creature — Daemon Primarch',
      'Blood Artist':'Creature — Vampire','Treasure':'Token Artifact'};
    return types[name]?{name,oracle_id:name+'-id',type_line:types[name],
      art:'https://example.invalid/'+encodeURIComponent(name)+'.jpg'}:null;
  };
  const round={round:4,
    snapshots:{'0':{hand_size:2,life:34,lands:1,creatures:1,zones:{
      hand:[{name:'Blood Artist',object_id:4},{name:'Sol Ring',object_id:9}],
      battlefield:[{name:'Swamp',object_id:1},
        {name:'Mortarion, Daemon Primarch',object_id:3},
        {name:'Treasure',object_id:23,token:true}],
      graveyard:[],exile:[],untracked_tokens:[]}}},
    mana_activations:[
      {source_name:'Swamp',mana_output:['B']},
      {source_name:'Sol Ring',mana_output:['C','C']}],
    actions:[]};
  const flatten=x=>[x,...(x.children||[]).flatMap(flatten)];
  try{
    const hand=Replay.zoneInspector(round,'hand',lookup,id=>opened.push(id));
    const all=flatten(hand);
    assert.ok(all.some(x=>x.textContent==='Blood Artist'));
    assert.ok(all.some(x=>x.textContent==='Sol Ring'));
    const button=all.find(x=>x.className==='replay-zone-card');
    assert.equal(typeof button.onclick,'function');
    button.onclick();assert.equal(opened.length,1);
    const creatures=Replay.zoneInspector(round,'creatures',lookup,()=>{});
    const c=flatten(creatures);
    assert.ok(c.some(x=>x.textContent==='Mortarion, Daemon Primarch'));
    assert.ok(c.some(x=>x.textContent==='Treasure'));
    const lands=Replay.zoneInspector(round,'lands',lookup,()=>{});
    const l=flatten(lands);
    assert.ok(l.some(x=>x.textContent==='Swamp'));
    assert.ok(l.some(x=>x.textContent==='Sol Ring'));
    assert.ok(l.some(x=>String(x.textContent).includes('output')));
    const creditIcons=l.filter(x=>x.tag==='img'&&x.src?.includes('/card-symbols/'));
    assert.equal(creditIcons.filter(x=>x.src.endsWith('/C.svg')).length,2);
    assert.deepEqual(creditIcons.filter(x=>x.src.endsWith('/C.svg')).map(x=>x.alt),['{C}','{C}']);
    assert.equal(Replay.zoneInspector(fixture().scenarios.balanced.games[0].rounds[0],'hand',lookup,()=>{}),null);
  }finally{global.document=old}
});

test('replay mana glyphs use existing Scryfall symbol artwork and safe readable fallbacks',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.className='';this.textContent='';}
    appendChild(value){this.children.push(value);return value}
  }
  const original=global.document;global.document={createElement:tag=>new Node(tag)};
  try{
    const glyphs=Replay.manaOutputSymbols(['B','C','C','W/U','?']);
    assert.equal(glyphs.className,'mana-symbols replay-mana-output');
    assert.deepEqual(glyphs.children.slice(0,4).map(x=>x.src),[
      'https://svgs.scryfall.io/card-symbols/B.svg',
      'https://svgs.scryfall.io/card-symbols/C.svg',
      'https://svgs.scryfall.io/card-symbols/C.svg',
      'https://svgs.scryfall.io/card-symbols/WU.svg']);
    assert.equal(glyphs.children[4].textContent,'?');
    assert.deepEqual(glyphs.children.slice(0,4).map(x=>x.alt),
      ['{B}','{C}','{C}','{W/U}']);
    assert.equal(Replay.manaOutputSymbols([]).children[0].textContent,'Unreported');
  }finally{global.document=original}
});
