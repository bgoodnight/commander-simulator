"use strict";
const {test}=require("node:test"),assert=require("node:assert/strict");
const {extract}=require("../tools/gorge_cast_activity.cjs");
test("counts only hero casts, including commander and repeated casts",()=>{
  const game={seed:7,object_identity:{"9":"Commander"},turns:[{events:[
    {kind:"cast",obj:9}, {kind:"cast",obj:9},
    {kind:"cast",player:1,card_name:"Other"},
    {kind:"cast",card_name:"Ritual"},{kind:"damage",amount:3}
  ]}]};
  const cards=new Map([["Commander",{type_line:"Legendary Creature — Primarch"}],
    ["Ritual",{type_line:"Instant"}]]);
  const out=extract(game,0,cards);
  assert.equal(out.spells,3);assert.equal(out.creatures,2);
  assert.equal(out.cards.find(x=>x.name==="Commander").casts,2);
  assert.equal(out.named_casts_complete,true);
});
test("missing identity or type does not invent creature counts",()=>{
  const out=extract({seed:8,turns:[{events:[{kind:"cast"}]}]},0,new Map());
  assert.equal(out.spells,1);assert.equal(out.creatures,null);
  assert.equal(out.named_casts_complete,false);
});
