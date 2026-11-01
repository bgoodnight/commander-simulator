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
