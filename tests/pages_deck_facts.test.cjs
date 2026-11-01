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
