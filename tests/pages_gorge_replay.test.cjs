"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const Gorge=require("../web/pages/gorge_replay.js");
const original={
  schema:"gorge-native-trace-v1",engine:"gorge",format:"commander",
  seed:100,chain:"648bb20ccbfc5ad5",
  decks:["mortarion_current","magnus_premium","necron_dynasties","wretched_ranks"],
  policies:["bot","bot","bot","bot"],
  log:{seed:100,intents:[{seq:3,player:0,choices:[0]}],
    events:[
      {seq:0,kind:0,amount:4},
      {seq:1,kind:3,obj:12,secret:true},
      {seq:2,kind:9,amount:1},
      {seq:3,kind:20,text:"priority"},
      {seq:4,kind:21,text:"priority:[0]"},
      {seq:5,kind:23,obj:8},
      {seq:6,kind:11,obj:20},
      {seq:7,kind:13,amount:2},
      {seq:8,kind:9,amount:2,player:1},
      {seq:9,kind:3,player:1,obj:122,secret:true},
      {seq:10,kind:500,text:"future kind"}
    ]}
};
assert.equal(Gorge.validate(original),original);
const turns=Gorge.turns(original);
assert.equal(turns.length,3);
assert.deepEqual(turns.map(x=>x.number),[0,1,2]);
assert.equal(Gorge.stats(original).intents,1);
assert.equal(Gorge.stats(original).events,11);
assert.equal(Gorge.accessibleEvents(turns[2],0,false).length,2);
assert.equal(Gorge.accessibleEvents(turns[2],1,false).length,3);
assert.equal(Gorge.accessibleEvents(turns[2],0,true).length,3);
assert.match(Gorge.eventLine(original.log.events[5],original),/played a land/);
assert.match(Gorge.eventLine(original.log.events[6],original),/stack/);
assert.match(Gorge.eventLine(original.log.events[7],original),/mana/);
assert.equal(Gorge.KINDS[10],"Priority");
assert.equal(Gorge.KINDS[23],"Land played");
assert.equal(Gorge.KINDS[500],undefined);
assert.throws(()=>Gorge.validate({...original,format:"constructed"}),/Expected/);
assert.throws(()=>Gorge.validate({...original,chain:""}),/Missing gorge/);
assert.throws(()=>Gorge.validate({...original,log:{events:[{seq:1,kind:9},{seq:1,kind:3}],intents:[]}}),/order/);
assert.throws(()=>Gorge.validate({...original,log:{events:[],intents:[]}}),/Missing/);
const html=fs.readFileSync(path.join(__dirname,"../web/pages/index.html"),"utf8");
assert.match(html,/id="gorge-replay-panel"/);
assert.match(html,/id="gorge-replay-file"/);
assert.match(html,/gorge_replay\.js/);
const build=fs.readFileSync(path.join(__dirname,"../tools/build_pages_deck_lab.py"),"utf8");
assert.match(build,/gorge_replay\.js/);
console.log("Gorge native replay viewer: schema, actual-format events, privacy filtering, turn grouping and static route wiring PASS");
