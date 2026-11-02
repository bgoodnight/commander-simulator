'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Explorer=require('../web/pages/insight_explorer.js');
const Replay=require('../web/pages/replay.js');

const card=name=>['Gisa','Yahenni'].includes(name)?
  {name,oracle_id:name.toLowerCase(),type_line:'Legendary Creature — Human',
   image:'https://example.invalid/'+name+'.jpg',art:'https://example.invalid/'+name+'-art.jpg'}:null;
const row=(turn,events,hand,battlefield=[])=>({turn,events,
  snapshot:{turn,hand,battlefield},land_count:1,hand_size:hand.length});
function makeRun(seed,opening,turns){
  return {seed,deck_key:'fixture',deck_sha256:'a'.repeat(64),
    mulligan:{opening_hand:opening},
    events:turns.map(t=>({turn:t.turn,events:t.events,hand_size:t.snapshot.hand.length,land_count:1})),
    state_snapshots:turns.map(t=>t.snapshot)};
}
const played=(name)=>[{type:'creature_cast',card:name},{type:'creature_resolved',card:name}];
function fixture(){
  return [
    makeRun(0,['Gisa'],[
      row(1,[{type:'draw',card:'Yahenni'}],['Gisa','Yahenni']),
      row(2,played('Yahenni'),['Gisa'],['Yahenni']),
      row(3,played('Gisa'),[],['Yahenni','Gisa'])
    ]),
    makeRun(1,['Yahenni'],[
      row(1,[{type:'draw',card:'Swamp'}],['Yahenni']),
      row(2,[],['Yahenni']),
      row(3,[],['Yahenni']),
      row(4,played('Yahenni'),[],['Yahenni'])
    ]),
    makeRun(2,['Yahenni'],[
      row(1,played('Gisa'),['Yahenni'],['Gisa']),
      row(2,[{type:'reviewed_enter_resolved',card:'Yahenni'}],['Yahenni'],['Gisa']),
      row(3,[],['Yahenni'],['Gisa'])
    ])
  ];
}

test('creature MVP derives distinct seed denominators and median first cast turn',()=>{
  const model=Explorer.creaturePlays(fixture(),card);
  assert.equal(model.total,3);
  assert.equal(model.contenders.length,2);
  assert.equal(model.contenders[0].name,'Gisa');
  assert.equal(model.contenders[0].score,2);
  assert.equal(model.contenders[1].name,'Yahenni');
  assert.equal(model.contenders[1].score,2);
  const yahenni=model.contenders[1];
  assert.equal(yahenni.metrics.find(m=>m.id==='access').value,'67%');
  assert.equal(yahenni.metrics.find(m=>m.id==='turn').value,'3');
  const games=yahenni.metrics.find(m=>m.id==='played').examples;
  assert.deepEqual(games.map(g=>[g.seed,g.turn,g.eventIndex]),[[0,2,1],[1,4,1]]);
  assert.equal(games[0].run.seed,0);
});

test('no resolved creature and missing input produce no insight; ETB is not a play',()=>{
  assert.equal(Explorer.creaturePlays([],card),null);
  const sample=makeRun(0,['Gisa'],[row(1,[{type:'reviewed_enter_resolved',card:'Gisa'}],['Gisa'])]);
  assert.equal(Explorer.creaturePlays([sample],card),null);
  assert.equal(Explorer.median([4,2,5,1]),3);
});

test('insight renderer has art-backed header, selectable bars, cycleable metric evidence',()=>{
  class Node{
    constructor(tag){
      this.tag=tag;this.children=[];this.className='';this.attributes={};
      this.textContent='';this.style={};this.open=false;
    }
    append(...children){this.children.push(...children)}
    appendChild(child){this.children.push(child);return child}
    replaceChildren(...children){this.children=[...children]}
    setAttribute(name,value){this.attributes[name]=value}
  }
  const previous=global.document;
  global.document={createElement:tag=>new Node(tag)};
  try{
    const opened=[];
    const model=Explorer.creaturePlays(fixture(),card);
    const panel=Explorer.render(model,{onOpenEvidence:(e,c,m)=>opened.push([e.seed,e.turn,e.eventIndex,c.name,m.id])});
    const walk=node=>[node,...node.children.flatMap(walk)];
    let nodes=walk(panel);
    assert.equal(panel.tag,'details');
    assert.match(panel.className,/board-report insight-report/);
    assert.ok(nodes.some(n=>n.className.includes('board-summary')));
    assert.equal(nodes.filter(n=>n.tag==='img').length,2); // banner and selected physical card
    const bar=nodes.find(n=>n.className.startsWith('insight-bar')&&n.attributes['aria-pressed']==='false');
    assert.ok(bar);bar.onclick();
    nodes=walk(panel);
    assert.ok(nodes.some(n=>n.className==='insight-card-name'&&n.textContent==='Yahenni'));
    assert.equal(nodes.filter(n=>n.tag==='img').length,2); // contender bars contain no art
    const metric=nodes.find(n=>n.className.startsWith('insight-metric'));
    metric.onclick();
    nodes=walk(panel);
    assert.ok(nodes.some(n=>n.textContent==='Seed 0 · Turn 2'));
    // The node is rebuilt after a click, so locate the current control again.
    nodes.find(n=>n.className.startsWith('insight-metric')).onclick();
    nodes=walk(panel);
    assert.ok(nodes.some(n=>n.textContent==='Seed 1 · Turn 4'));
    nodes.find(n=>n.textContent==='View full turn ↗').onclick();
    assert.deepEqual(opened,[[1,4,1,'Yahenni','played']]);
  }finally{global.document=previous}
});

test('simulation shell retains native card art overlay and bottom seed turn viewer',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const app=fs.readFileSync('web/pages/app.js','utf8');
  assert.match(html,/insight_explorer\.js/);
  assert.match(html,/id="insight-turn-viewer"/);
  assert.ok(html.indexOf('id="insight-turn-viewer"')>html.indexOf('id="archive-observation-details"'));
  assert.ok(html.indexOf('id="opponent-replay-panel"')>html.indexOf('id="insight-turn-viewer"'));
  assert.match(css,/\.insight-report \.board-summary-copy/);
  assert.match(app,/creatureInsightReport\(batch\.runs\)/);
  assert.match(app,/CommanderReplay\.renderBoundedEvidence/);
  assert.equal(typeof Replay.renderBoundedEvidence,'function');
});

test('bounded replay adapter retains exact action order, card identity and snapshots',()=>{
  const run=fixture()[0];
  const rounds=Replay.boundedRounds(run,card);
  assert.equal(rounds[1].round,2);
  assert.deepEqual(rounds[1].actions.map(a=>a.type),['creature_cast','creature_resolved']);
  assert.deepEqual(rounds[1].snapshots['0'].zones.hand,[{name:'Gisa',token:false}]);
  assert.equal(rounds[1].snapshots['0'].creatures,1);
  assert.equal(rounds[1].snapshots['0'].life,null);
  assert.equal(rounds[1].actions[1].card_name,'Yahenni');
});
