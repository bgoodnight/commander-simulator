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
const replayLoader=fs.readFileSync(path.join(__dirname,"../web/pages/gorge_replay.js"),"utf8");
// A growing Gorge manifest must not fetch every megabyte-scale replay merely
// to open the first game. Each selected seed is fetched on demand.
assert.match(replayLoader,/return openPublicSample\(select\.value\);/);
assert.doesNotMatch(replayLoader,/Promise\.allSettled\(\[\.\.\.available\]/);

console.log("Gorge native replay viewer: schema, actual-format events, privacy filtering, turn grouping and static route wiring PASS");


const enriched={
  ...original,
  enrichment_schema:"gorge-physical-state-v1",
  objects:[
    {object_id:8,card_name:"Swamp",effective_name:"Swamp",owner:0},
    {object_id:20,card_name:"Sol Ring",effective_name:"Sol Ring",owner:0},
    {object_id:122,card_name:"Counterspell",effective_name:"Counterspell",owner:1}
  ],
  snapshots:[{
    turn:1,active_seat:0,step:"main1",after_event_seq:5,
    boundary:"first_pending_decision_of_turn",
    players:[
      {seat:0,life:40,lost:false,mana_pool:[0,0,1,0,0,0],
       zones:{hand:[20],library:[8],battlefield:[8],graveyard:[],exile:[],command:[]}},
      {seat:1,life:39,lost:false,mana_pool:[0,1,0,0,0,0],
       zones:{hand:[122],library:[],battlefield:[],graveyard:[],exile:[],command:[]}},
      {seat:2,life:40,lost:false,mana_pool:[0,0,0,0,0,0],
       zones:{hand:[],library:[],battlefield:[],graveyard:[],exile:[],command:[]}},
      {seat:3,life:40,lost:false,mana_pool:[0,0,0,0,0,0],
       zones:{hand:[],library:[],battlefield:[],graveyard:[],exile:[],command:[]}}
    ]
  }]
};
assert.equal(Gorge.validate(enriched),enriched);
assert.equal(Gorge.objectName(enriched,20),"Sol Ring");
assert.equal(Gorge.objectName(enriched,1000),null);
assert.match(Gorge.eventLine(enriched.log.events[6],enriched),/Sol Ring/);
const seat0=Gorge.stateForSeat(enriched,1,0);
assert.equal(seat0.players[0].zones.hand[0].name,"Sol Ring (#20)");
assert.equal(seat0.players[1].zones.hand,null,"Opponent hand identities must stay hidden");
assert.equal(seat0.players[1].hand_size,1);
assert.deepEqual(seat0.players[0].mana_pool,[0,0,1,0,0,0]);
const seat1=Gorge.stateForSeat(enriched,1,1);
assert.equal(seat1.players[1].zones.hand[0].name,"Counterspell (#122)");
assert.equal(seat1.players[0].zones.hand,null);
assert.equal(Gorge.stateForSeat(enriched,1,0,true).players[1].zones.hand[0].name,"Counterspell (#122)");
assert.equal(Gorge.stateForSeat(enriched,2,0),null);
assert.throws(()=>Gorge.validate({...enriched,objects:[enriched.objects[0],enriched.objects[0]]}),/crosswalk/);
console.log("Gorge source-backed card identity and turn-start state privacy PASS");
