'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

const code=fs.readFileSync('web/pages/app.js','utf8').replace(/boot\(\);\s*$/,'');
function context(missingIds=[]){
  const nodes=new Map();
  const missing=new Set(missingIds);
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
      if(missing.has(id))return null;
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
  assert.deepEqual(Array.from(choices,c=>c.id),['saved:v-new','saved:v-one','preset:beta','preset:alpha']);
  assert.equal(vm.runInContext('latestDeckChoice().title',ctx),'The Latest Build');
  assert.match(vm.runInContext('deckChoiceLabel(latestDeckChoice())',ctx),
               /The Latest Build.*Beta Commander.*2026-11-01.*Saved in this browser/);
});

test('single full-width editor deck selector filters to selected commander',()=>{
  const {ctx,nodes}=context();
  vm.runInContext('renderGlobalDeckSelector();renderDeckVersionSelector()',ctx);
  const values=node=>node.children.map(x=>x.value);
  assert.deepEqual(values(nodes.get('global-deck-select')),['saved:v-one','preset:alpha']);
  vm.runInContext("selected='beta';renderGlobalDeckSelector()",ctx);
  assert.deepEqual(values(nodes.get('global-deck-select')),['saved:v-new','preset:beta']);
  assert.equal(nodes.get('global-deck-select').value,'preset:beta');
});

test('cross-commander built-in and saved variants load without filtering',()=>{
  const {ctx}=context();
  vm.runInContext(`
    var loaded=[];
    validateCounts=()=>{};
    note=()=>{};
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

test('deck selection appears after commander header, above editor content',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  assert.match(html,/<\/section>\s*<section class="deck-selection-row"[\s\S]*?id="global-deck-select"[\s\S]*?<\/section>\s*<section id="app-content"/);
  assert.match(html,/id="saved-versions"/);
  assert.match(html,/class="deck-selection-row"/);
  assert.doesNotMatch(html,/id="deck-version-select"/);
  assert.match(html,/Manage Decks/);
});

test('removed legacy deck selector does not interrupt deck rendering',()=>{
  const {ctx,nodes}=context(['deck-version-select','change-deck-link']);
  assert.doesNotThrow(()=>vm.runInContext('renderDeckVersionSelector();renderGlobalDeckSelector()',ctx));
  assert.ok(nodes.get('global-deck-select').children.length>0);
});

test('physical Mortarion UI uses the verified 100-run archive rather than legacy observations',()=>{
  const {ctx}=context();
  vm.runInContext(`
    data.decks.push({key:'mortarion_physical_final',commander:'Mortarion, Daemon Primarch',
      commander_id:'mortarion-id',deck_sha256:'pinned-hash',cards:[]});
    selected='mortarion_physical_final';selectedVersionId=null;activeCounts=null;
    const turn=(i,lands)=>({turn:i,land_count:lands,mana_rock_count:i===6?1:0,
      creature_count:i===6?1:0,hand_size:7,
      unsupported_cards_in_hand:['Blood Artist'],
      events:[{type:'draw',card:'Swamp'}]});
    var run=(seed,third)=>({seed,deck_key:'mortarion_physical_final',deck_sha256:'pinned-hash',
      mode:'bounded_authoritative_early_actions',mulligan:{policy:'one-free'},
      events:[turn(1,1),turn(2,2),turn(3,third),turn(4,4),turn(5,4),turn(6,4)],
      state_snapshots:Array.from({length:6},(_,i)=>({turn:i+1,hand:[],battlefield:[]}))});
    var physicalRuns=[run(0,3),run(1,2)];
    detailedArchives={mortarion_physical_final:{
      runs:physicalRuns,deck_sha256:'pinned-hash',release:'simulated-commit'}};
  `,ctx);
  assert.equal(vm.runInContext('physicalArchive()?.runs.length',ctx),2);
  assert.equal(vm.runInContext('physicalArchiveMetrics(physicalArchive().runs).third',ctx),50);
  assert.equal(vm.runInContext('physicalArchiveMetrics(physicalArchive().runs).fourth',ctx),100);
  assert.equal(vm.runInContext('physicalArchiveBreakdown(physicalArchive().runs).timeline[5].unsupported',ctx),'1.00');
  assert.equal(vm.runInContext("detailedArchives.mortarion_physical_final.deck_sha256='stale';physicalArchive()",ctx),null);
  const html=fs.readFileSync('web/pages/index.html','utf8');
  assert.match(html,/id="archive-observation-details"/);
  assert.match(code,/const seedChoices=physical\?physical.runs.map\(run=>run.seed\):data.seeds/);
  assert.match(code,/const physical=detailedArchives\?\.\[deck.key\]/);
});
