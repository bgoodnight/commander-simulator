'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('web/pages/app.js','utf8').replace(/boot\(\);\s*$/, '');
function setup(initial){
  const stored=new Map(initial?[['commander-deck-lab-sound-v1',initial]]:[]);
  const button={setAttribute(k,v){this[k]=v}};
  let contexts=0;
  const ctx={location:{pathname:'/index.html'},window:{AudioContext:class{constructor(){contexts++}}},
    localStorage:{getItem:k=>stored.get(k)??null,setItem:(k,v)=>stored.set(k,v)},
    document:{getElementById:()=>button},console};
  vm.createContext(ctx);vm.runInContext(source,ctx);
  return {ctx,stored,button,contexts:()=>contexts};
}
test('sound defaults on, but no audio starts before a user gesture',()=>{
  const s=setup();vm.runInContext('syncSoundControl(); originalSound()',s.ctx);
  assert.equal(s.button['aria-pressed'],'true');assert.equal(s.contexts(),0);
});
test('mute persists and is restored across pages',()=>{
  const s=setup();vm.runInContext('enableSound()',s.ctx);
  assert.equal(s.stored.get('commander-deck-lab-sound-v1'),'off');
  assert.equal(s.button['aria-pressed'],'false');
  const next=setup('off');vm.runInContext('syncSoundControl()',next.ctx);
  assert.equal(next.button.textContent,'♫ Sound off');
});
