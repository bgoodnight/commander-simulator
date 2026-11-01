'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync('web/pages/app.js','utf8').replace(/boot\(\);\s*$/, '');
test('deck facts follow actual quantities and exclude lands from the mana average',()=>{
  const ctx={location:{pathname:'/index.html'},window:{},localStorage:{getItem:()=>null},document:{}};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext(`
    data={cards:{c:{category:'Creature',mana_value:6},l:{category:'Land',mana_value:0},s:{category:'Sorcery',mana_value:2}},
      decks:[{key:'test',cards:[{zone:'Commander',oracle_id:'c',name:'Commander',qty:1}]}]};
    selected='test';activeCounts={Land:3,Spell:2};
    cachedByName.set('land',{oracle_id:'l'});cachedByName.set('spell',{oracle_id:'s'});
  `,ctx);
  const facts=vm.runInContext('deckFacts()',ctx);
  assert.equal(facts.total,6);assert.equal(facts.lands,3);assert.equal(facts.averageMana,'3.3');
  vm.runInContext("activeCounts.Spell=1",ctx);
  assert.equal(vm.runInContext('deckFacts().total',ctx),5);
});
test('theme art and matching card names open the correct card details',()=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.handlers={};this.classList={add(){}}}
    append(...nodes){this.children.push(...nodes)}
    appendChild(node){this.children.push(node);return node}
    replaceChildren(){this.children=[]}
    setAttribute(k,v){this.attrs[k]=v}
    addEventListener(k,v){this.handlers[k]=v}
  }
  const root=new Node('root'),opened=[];
  const record={name:'Graveborn Muse',oracle_id:'z',art:'https://example.test/art.jpg'};
  const group={id:'subtype:zombie',label:'Zombie',copies:1,kind:'Creature subtype',sample:1,opening:1,byTurn3:1,byTurn6:1,cards:[{name:record.name,qty:1}]};
  const ctx={location:{pathname:'/index.html'},window:{DeckInsights:{themes:()=>[group]}},
    localStorage:{getItem:()=>null},document:{getElementById:()=>root,createElement:t=>new Node(t)},opened,record};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext("data={cards:{z:record},decks:[]}; cachedByName.set(record.name.toLowerCase(),record); showCard=id=>opened.push(id); renderThemes([],null)",ctx);
  const article=root.children[0],preview=article.children[0];
  assert.equal(preview.attrs['aria-label'],'View Graveborn Muse card details');
  preview.handlers.click();
  const details=article.children.find(x=>x.tag==='details');
  const link=details.children[1].children[0].children[0];
  assert.equal(link.tag,'button');link.handlers.click();
  assert.deepEqual(opened,['z','z']);
});
test('mana icons preserve hybrid symbols, missing costs, and offline fallback',()=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.classList={add(){}}}
    appendChild(node){this.children.push(node);return node}
    setAttribute(k,v){this.attrs[k]=v}
    replaceWith(node){this.replacement=node}
  }
  const ctx={location:{pathname:'/index.html'},window:{},localStorage:{getItem:()=>null},document:{createElement:t=>new Node(t)}};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  const row=vm.runInContext("manaSymbols('{2}{U}{W/P}{X}')",ctx);
  assert.deepEqual(row.children.map(x=>x.alt),['{2}','{U}','{W/P}','{X}']);
  assert.equal(row.children[2].src,'https://svgs.scryfall.io/card-symbols/WP.svg');
  row.children[2].onerror();assert.equal(row.children[2].replacement.textContent,'{W/P}');
  assert.equal(vm.runInContext("manaSymbols('')",ctx).children[0].textContent,'—');
  const identity=vm.runInContext("commanderIdentity({color_identity:['R','U']})",ctx);
  assert.equal(identity.children[1].attrs['aria-label'],'blue, red color identity');
  assert.equal(vm.runInContext('commanderIdentity({color_identity:[]})',ctx).children[1].textContent,'Colorless');
});
test('curve point reveals its runs and linked source cards',()=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.handlers={};this.dataset={};this.classList={add(){}}}
    append(...nodes){this.children.push(...nodes)}
    appendChild(node){this.children.push(node);return node}
    replaceChildren(){this.children=[]}
    setAttribute(k,v){this.attrs[k]=v}
    addEventListener(k,v){this.handlers[k]=v}
    querySelectorAll(selector){return this.children.filter(c=>selector==='.curve-point'&&c.attrs.class==='curve-point')}
  }
  const root=new Node('root'),detail=new Node('detail'),opened=[];
  const record={name:'Swamp',oracle_id:'s'};
  const points=[{turn:1,mean:1,runs:[{seed:'7',count:1,cards:['Swamp']}]}];
  const ctx={location:{pathname:'/results.html'},window:{DeckInsights:{sourceTimeline:()=>points}},
    localStorage:{getItem:()=>null},document:{getElementById:id=>id==='source-curve'?root:detail,
      createElement:t=>new Node(t),createElementNS:(_,t)=>new Node(t)},record,opened};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext("cachedByName.set('swamp',record); showCard=id=>opened.push(id); renderSourceCurve({})",ctx);
  const point=root.children[0].children.find(x=>x.attrs.class==='curve-point');
  point.handlers.click();assert.equal(point.attrs['aria-pressed'],'true');
  const row=detail.children[2].children[0],card=row.children[2].children[0];
  card.handlers.click();assert.deepEqual(opened,['s']);
});
test('rules text renders embedded mana symbols without losing surrounding text or line breaks',()=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.classList={add(){}}}
    appendChild(node){this.children.push(node);return node}
  }
  const ctx={location:{pathname:'/index.html'},window:{},localStorage:{getItem:()=>null},document:{createElement:t=>new Node(t)}};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  const rendered=vm.runInContext("manaSymbols('Convoke pays for {1} or one mana.\\nDraw two cards.')",ctx);
  assert.equal(rendered.children[0].textContent,'Convoke pays for ');
  assert.equal(rendered.children[1].alt,'{1}');
  assert.equal(rendered.children[1].src,'https://svgs.scryfall.io/card-symbols/1.svg');
  assert.equal(rendered.children[2].textContent,' or one mana.\nDraw two cards.');
});
test('theme story selects a turn and opens the matching card',()=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.handlers={};this.dataset={};this.style={};this.classList={add(){}}}
    append(...nodes){this.children.push(...nodes)}
    appendChild(node){this.children.push(node);return node}
    replaceChildren(){this.children=[]}
    setAttribute(k,v){this.attrs[k]=v}
    addEventListener(k,v){this.handlers[k]=v}
    querySelectorAll(selector){return this.children.filter(c=>selector==='.theme-series'&&c.attrs.class==='theme-series')}
  }
  const nodes={};for(const id of ['theme-story-chart','theme-story-detail','story-title-themes','story-summary-themes'])nodes[id]=new Node('div');
  const card={name:'Zombie A',oracle_id:'z'};
  const points=Array.from({length:7},(_,turn)=>({turn,count:1,pct:100,matches:[{seed:'7',turn:0,card:'Zombie A'}]}));
  const group={id:'zombie',label:'Zombie',copies:5,sample:1,points};
  const ctx={location:{pathname:'/results.html'},window:{DeckInsights:{themes:()=>[group],themeTimelines:()=>[group]}},
    localStorage:{getItem:()=>null},document:{getElementById:id=>nodes[id],createElement:t=>new Node(t),createElementNS:(_,t)=>new Node(t)},card,opened:[]};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext("data={cards:{z:card}}; archives={test:{}};selected='test';displayDeckCards=()=>[];selectedDeck=()=>({commander_id:'z'});cardInfo=()=>card;showCard=id=>opened.push(id);renderThemeStory()",ctx);
  assert.match(nodes['story-title-themes'].textContent,/Zombie appears by turn 3 in 1 \/ 1 runs/);
  const chart=nodes['theme-story-chart'].children[1];
  const point=chart.children.find(x=>x.attrs.role==='button');point.handlers.click();
  const detail=nodes['theme-story-detail'],cardButton=detail.children[2].children[0].children[2];
  cardButton.handlers.click();assert.deepEqual(ctx.opened,['z']);
});
test('quiet diagnostic cycles through examples and opens their card details',()=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.handlers={};this.dataset={};this.style={};this.classList={add(){}}}
    append(...nodes){this.children.push(...nodes)}
    appendChild(node){this.children.push(node);return node}
    replaceChildren(){this.children=[]}
    setAttribute(k,v){this.attrs[k]=v}
    addEventListener(k,v){this.handlers[k]=v}
  }
  const nodes={};for(const id of ['quiet-output','quiet-status','quiet-command'])nodes[id]=new Node('div');
  const sample=seed=>({seed,turn:2,landCount:1,hand:['Spell'],battlefield:[],unsupported:['Spell'],events:[]});
  const points=[{turn:2,total:2,count:2,pct:100,uncertain:2,examples:[sample(1),sample(2)],nonquiet:[]}];
  const ctx={location:{pathname:'/results.html'},window:{DeckInsights:{quietTurns:()=>points}},
    localStorage:{getItem:()=>null},document:{getElementById:id=>nodes[id],createElement:t=>new Node(t)},opened:[]};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext("selectedDeck=()=>({key:'d',deck_sha256:'hash'});isUnsimulatedVersion=()=>false;cardInfo=()=>({oracle_id:'s',category:'Sorcery'});showCard=id=>opened.push(id);quietRuns=[{},{}];renderQuietDiagnostic()",ctx);
  const out=nodes['quiet-output'];let example=out.children[out.children.length-1];
  assert.match(example.children[0].textContent,/seed 1/);
  example.children[2].children[1].handlers.click();
  example=out.children[out.children.length-1];assert.match(example.children[0].textContent,/seed 2/);
  example.children[4].children[0].handlers.click();assert.deepEqual(ctx.opened,['s']);
});

test('batch examples match the deck, the turn and the recorded card role',()=>{
  const ctx={location:{pathname:'/results.html'},window:{},localStorage:{getItem:()=>null},document:{}};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext(`
    data={cards:{l:{oracle_id:'l',name:'Island'},r:{oracle_id:'r',name:'Sol Ring'},a:{oracle_id:'a',name:'Other Artifact'},s:{oracle_id:'s',name:'Spell'},x:{oracle_id:'x',name:'Outside'}}};
    for(const item of Object.values(data.cards))cachedByName.set(item.name.toLowerCase(),item);
    deck={cards:[{oracle_id:'l'},{oracle_id:'r'},{oracle_id:'a'},{oracle_id:'s'}],modeled_rocks:['r']};
    batch={runs:[
      {events:[{events:[{type:'land_play',card:'Island'},{type:'artifact_resolved',card:'Other Artifact'}],unsupported_cards_in_hand:[]},
       {events:[{type:'artifact_resolved',card:'Sol Ring'},{type:'land_play',card:'Outside'}],unsupported_cards_in_hand:['Spell','Spell']}]},
      {events:[{events:[{type:'land_play',card:'Island'}],unsupported_cards_in_hand:[]},
       {events:[],unsupported_cards_in_hand:['Spell']}]}
    ]};
  `,ctx);
  assert.equal(vm.runInContext("batchExample(batch,deck,'land',1).count",ctx),2);
  assert.equal(vm.runInContext("batchExample(batch,deck,'rock',2).card.name",ctx),'Sol Ring');
  assert.equal(vm.runInContext("batchExample(batch,deck,'unsupported',2).count",ctx),2);
  assert.equal(vm.runInContext("batchExample(batch,deck,'rock',1)",ctx),null);
});

test('compact batch card example opens card details without a caption',()=>{
  class Node {constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.handlers={};this.classList={add(){}}}
    append(...nodes){this.children.push(...nodes)} appendChild(node){this.children.push(node);return node}
    setAttribute(k,v){this.attrs[k]=v} addEventListener(k,v){this.handlers[k]=v}}
  const opened=[],ctx={location:{pathname:'/results.html'},window:{},localStorage:{getItem:()=>null},opened,
    document:{createElement:t=>new Node(t)}};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext('showCard=id=>opened.push(id)',ctx);
  const node=vm.runInContext("batchExampleNode({card:{name:'Sol Ring',oracle_id:'r',image:'https://example.test/card.jpg'},count:27},'rock',3,100)",ctx);
  assert.equal(node.attrs['aria-label'],'View Sol Ring card details');
  assert.equal(node.children.length,1);
  assert.equal(node.children[0].src,'https://example.test/card.jpg');
  node.handlers.click();assert.deepEqual(opened,['r']);
});

test('board report connects the aggregate to matching run evidence and card details',()=>{
  class Node {constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.handlers={};this.style={};this.classList={add(){}}}
    append(...nodes){this.children.push(...nodes)} appendChild(node){this.children.push(node);return node}
    setAttribute(k,v){this.attrs[k]=v} addEventListener(k,v){this.handlers[k]=v}}
  const card={name:'Golem',oracle_id:'g',type_line:'Artifact Creature — Golem',art:'https://example.test/art.jpg'};
  const snapshots=Array.from({length:6},(_,i)=>({turn:i+1,battlefield:['Golem'],hand:[]}));
  const run={seed:3,state_snapshots:snapshots,events:snapshots.map(x=>({turn:x.turn,events:[]}))};
  const ctx={location:{pathname:'/results.html'},window:{DeckInsights:require('../web/pages/results_insights.js')},localStorage:{getItem:()=>null},document:{createElement:t=>new Node(t)},card,run,opened:[]};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext('cardInfo=n=>n===card.name?card:null;showCard=id=>opened.push(id)',ctx);
  const report=vm.runInContext("boardReport({runs:[run]},'Creature')",ctx);
  assert.match(report.children[0].children[0].children[1].textContent,/100%/);
  const body=report.children[1];
  body.children[5].children[0].handlers.click();assert.deepEqual(ctx.opened,['g']);
  const evidence=body.children[6];assert.match(evidence.children[0].textContent,/1/);
  assert.match(evidence.children[1].children[0].textContent,/seed 3/);
});
