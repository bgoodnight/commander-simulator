'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

const code=fs.readFileSync('web/pages/app.js','utf8').replace(/boot\(\);\s*$/,'');
function context(){
  const nodes=new Map();
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.value='';this.disabled=false;this.classList={add(){}};}
    appendChild(child){this.children.push(child);return child;}
    append(...children){this.children.push(...children);}
    replaceChildren(){this.children=[];}
  }
  const ctx={
    location:{pathname:'/index.html',search:''},
    window:{confirm:()=>true}, localStorage:{getItem:()=>null,setItem(){}},
    document:{getElementById:id=>{
      if(!nodes.has(id))nodes.set(id,new Node('root'));
      return nodes.get(id);
    },createElement:t=>new Node(t)}
  };
  vm.createContext(ctx);vm.runInContext(code,ctx);
  vm.runInContext(`
    data={cards:{},decks:[
      {key:'alpha',commander:'Alpha Commander',commander_id:'alpha-id',updated_at:'2026-09-01T00:00:00Z',cards:[]},
      {key:'beta',commander:'Beta Commander',commander_id:'beta-id',updated_at:'2026-10-20T00:00:00Z',cards:[]}
    ]};
    selected='alpha';selectedVersionId=null;activeCounts=null;
    localVersions=[
      {id:'v-one',title:'My First Deck',baseKey:'alpha',updated:'2026-10-21T00:00:00Z',counts:{}},
      {id:'v-new',title:'The Latest Build',baseKey:'beta',updated:'2026-11-01T18:00:00Z',counts:{}}
    ];
  `,ctx);
  return {ctx,nodes};
}

test('newest deck is default candidate across every commander and both sources',()=>{
  const {ctx}=context();
  const choices=vm.runInContext('allDeckChoices()',ctx);
  assert.deepEqual(choices.map(c=>c.id),['saved:v-new','saved:v-one','preset:beta','preset:alpha']);
  assert.equal(vm.runInContext('latestDeckChoice().title',ctx),'The Latest Build');
  assert.match(vm.runInContext('deckChoiceLabel(latestDeckChoice())',ctx),
               /The Latest Build.*Beta Commander.*2026-11-01.*Saved in this browser/);
});

test('the global selector and editor selector expose all named decks',()=>{
  const {ctx,nodes}=context();
  vm.runInContext('renderGlobalDeckSelector();renderDeckVersionSelector()',ctx);
  const values=node=>node.children.map(x=>x.value);
  const expected=['saved:v-new','saved:v-one','preset:beta','preset:alpha'];
  assert.deepEqual(values(nodes.get('global-deck-select')),expected);
  assert.deepEqual(values(nodes.get('deck-version-select')),expected);
  assert.equal(nodes.get('global-deck-select').value,'preset:alpha');
});

test('cross-commander built-in and saved variants load without filtering',()=>{
  const {ctx}=context();
  vm.runInContext(`
    var loaded=[];
    summon=(key,{versionId=null}={})=>loaded.push({key,versionId});
    loadDeckSelection('preset:beta');
    loadDeckSelection('saved:v-new');
  `,ctx);
  const records=vm.runInContext('loaded',ctx);
  assert.equal(records.length,2);
  assert.equal(records[0].key,'beta');
  assert.equal(records[0].versionId,null);
  assert.equal(records[1].key,'beta');
  assert.equal(records[1].versionId,'v-new');
});

test('unsaved edits require confirmation before deck switch',()=>{
  const {ctx}=context();
  ctx.window.confirm=()=>false;
  vm.runInContext(`
    var switched=false;
    hasUnsavedChanges=()=>true;
    renderDeckVersionSelector=()=>{};
    summon=()=>{switched=true};
    loadDeckSelection('preset:beta');
  `,ctx);
  assert.equal(vm.runInContext('switched',ctx),false);
});

test('header and manager UI elements exist in shared page shell',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  assert.match(html,/id="global-deck-select"/);
  assert.match(html,/id="saved-versions"/);
  assert.match(html,/id="deck-version-select"/);
  assert.match(html,/Manage Decks/);
});
