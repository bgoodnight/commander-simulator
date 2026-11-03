/* Gorge native replay viewer: independent of legacy Python replay renderer.
 * Parses the ORIGINAL gorge-native-trace-v1 log locally. No uploads or
 * invented object->card mappings, hand sizes, mana colors, or life totals.
 * Full records contain hidden libraries and hands. Restrict by seat unless
 * the owner explicitly enables omniscient inspection.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.GorgeReplay=api;
})(typeof window!=="undefined"?window:globalThis,function(){
"use strict";
const SCHEMA="gorge-native-trace-v1";
const KINDS={
  0:"Game start",1:"Shuffle",2:"Zone change",3:"Draw",4:"Life change",
  5:"Damage",6:"Tap",7:"Untap",8:"Step change",9:"Turn change",
  10:"Priority",11:"Spell/ability on stack",12:"Resolve",13:"Mana produced",
  14:"Mana cleared",15:"Counter changed",16:"Attackers",17:"Blockers",
  18:"Player lost",19:"Game over",20:"Decision asked",21:"Decision made",
  22:"Note",23:"Land played",24:"Targets chosen",25:"Face changed",
  26:"Clock tick",27:"Trigger on stack",28:"Combat reset",
  29:"Casting information",30:"Choice",31:"Token created",32:"Stack copied"
};
const NOTELESS=new Set([8,10,14,20,21,26,28]);
const $=(id)=>document.getElementById(id);
const node=(tag,cls,txt)=>{
  const el=document.createElement(tag);
  if(cls)el.className=cls;
  if(txt!==undefined&&txt!==null)el.textContent=String(txt);
  return el;
};
function validate(data){
  if(!data||data.schema!==SCHEMA||data.engine!=="gorge"||data.format!=="commander")
    throw Error("Expected an unmodified gorge-native-trace-v1 Commander recording");
  if(!Number.isSafeInteger(data.seed)||!Array.isArray(data.decks)||data.decks.length!==4||
     data.decks.some(x=>typeof x!=="string"||!x.trim())||
     !Array.isArray(data.policies)||data.policies.length!==4||
     typeof data.chain!=="string"||!data.chain.trim())
    throw Error("Missing gorge seed, four seats, policies, or replay chain");
  const log=data.log;
  if(!log||!Array.isArray(log.events)||!Array.isArray(log.intents)||!log.events.length||
     log.events.length>1500000)
    throw Error("Missing or oversized native gorge event/decision log");
  let previous=-1;
  for(const e of log.events){
    if(!e||!Number.isSafeInteger(e.seq)||e.seq<=previous||
       !Number.isInteger(e.kind)||e.kind<0||
       (e.player!==undefined&&(!Number.isInteger(e.player)||e.player<0||e.player>3)))
      throw Error("Malformed or out-of-order gorge event");
    previous=e.seq;
  }
  return data;
}
function turns(data){
  validate(data);
  const result=[];
  let current=null;
  function push(){
    if(current&&current.events.length)result.push(current);
  }
  for(const event of data.log.events){
    if(event.kind===9){
      push();
      current={number:Number.isInteger(event.amount)?event.amount:null,
        seat:Number.isInteger(event.player)?event.player:0,events:[]};
    }else if(!current){
      current={number:0,seat:null,events:[]};
    }
    current.events.push(event);
  }
  push();
  return result;
}
function allowed(e,seat,reveal){
  return reveal||!e.secret||e.player===seat;
}
function accessibleEvents(game,seat,reveal){
  return game.events.filter(e=>allowed(e,seat,reveal));
}
function kind(e){return KINDS[e.kind]||"Native event #"+e.kind}
function actor(e,data){
  const seat=Number.isInteger(e.player)?e.player:0;
  return data.decks[seat]+" (seat "+(seat+1)+")";
}
function eventLine(e,data){
  const seat=actor(e,data);
  const obj=Number.isInteger(e.obj)?" · object #"+e.obj:"";
  const amount=Number.isFinite(e.amount)?" · "+e.amount:"";
  const text=typeof e.text==="string"&&e.text.trim()?" · "+e.text.slice(0,160):"";
  if(e.kind===3)return seat+" drew a card"+obj;
  if(e.kind===9)return "Turn "+(e.amount??"?")+" · "+seat;
  if(e.kind===23)return seat+" played a land"+obj;
  if(e.kind===11)return seat+" put a spell/ability on the stack"+obj;
  if(e.kind===12)return "Stack object resolved"+obj;
  if(e.kind===13)return seat+" produced mana"+amount+obj;
  if(e.kind===5)return "Damage recorded"+amount+obj;
  if(e.kind===4)return "Life changed for "+seat+amount;
  if(e.kind===16)return seat+" declared attackers"+(e.ids?" · "+e.ids.length+" referenced object(s)":"");
  if(e.kind===17)return seat+" declared blockers";
  if(e.kind===18)return seat+" lost the game";
  if(e.kind===19)return "Game ended";
  return kind(e)+obj+amount+text;
}
function stats(data){
  const all=turns(data);
  const count=all.reduce((n,t)=>n+t.events.filter(e=>!NOTELESS.has(e.kind)).length,0);
  return {turns:all.filter(t=>t.number!==0).length,events:data.log.events.length,
    intents:data.log.intents.length,meaningful:count,players:data.decks};
}
function paint(rootElement,data,options={}){
  if(!rootElement||typeof document==="undefined")return;
  validate(data);
  rootElement.replaceChildren();
  const state={seat:Number.isInteger(options.seat)?options.seat:0,
               reveal:false,expanded:null,all:false};
  const turnData=turns(data), summary=stats(data);
  const header=node("div","gorge-replay-header");
  header.append(node("h3",null,"Native gorge Commander replay"));
  header.append(node("p","small","Seed "+data.seed+" · "+summary.turns+
    " turns · "+summary.events+" native events · "+summary.intents+
    " decisions · chain "+data.chain));
  rootElement.append(header);
  const caution=node("p","gorge-replay-caution",
    "This is the original engine event stream, not a reconstructed Python replay. "+
    "Card IDs are shown when card names cannot be proven; hand contents and "+
    "full life/mana snapshots are not inferred. Loaded locally in your browser.");
  rootElement.append(caution);
  const controls=node("div","gorge-replay-controls");
  const seatLabel=node("label",null,"View as player");
  const seatSelect=node("select","gorge-replay-seat");
  data.decks.forEach((name,index)=>{
    const option=node("option",null,"Seat "+(index+1)+" · "+name);
    option.value=String(index);seatSelect.append(option);
  });
  seatSelect.value=String(state.seat);seatLabel.append(seatSelect);
  controls.append(seatLabel);
  const disclosure=node("label","gorge-replay-disclosure");
  const reveal=node("input");reveal.type="checkbox";reveal.checked=false;
  disclosure.append(reveal,node("span",null,"Show all hidden events (omniscient)"));
  controls.append(disclosure);
  const showAll=node("button",null,"Show all event types");
  showAll.type="button";controls.append(showAll);
  rootElement.append(controls);
  const roster=node("div","gorge-replay-roster");
  data.decks.forEach((name,i)=>{
    const box=node("div","gorge-replay-player");
    box.append(node("strong",null,"Seat "+(i+1)),node("span",null,name),
      node("small",null,"AI: "+data.policies[i]));
    roster.append(box);
  });
  rootElement.append(roster);
  const list=node("div","gorge-replay-turns");
  rootElement.append(list);
  function draw(){
    list.replaceChildren();
    turnData.forEach((game,index)=>{
      const visible=accessibleEvents(game,state.seat,state.reveal);
      const substantive=visible.filter(e=>state.all||!NOTELESS.has(e.kind));
      const heading=game.number===0?"Game setup":
        "Turn "+game.number+" · "+(game.seat===null?"Unknown":data.decks[game.seat]);
      const section=node("details","gorge-replay-turn");
      if(index===0||index===state.expanded)section.open=true;
      const summaryRow=node("summary",null,heading);
      summaryRow.append(node("span","gorge-replay-event-count",
        substantive.length+" visible events"));
      section.append(summaryRow);
      const highlights=substantive.filter(e=>[3,4,5,11,12,13,16,17,18,19,23,31].includes(e.kind)).slice(0,5);
      if(highlights.length){
        const brief=node("p","gorge-replay-highlights",
          highlights.map(e=>kind(e)).join(" · "));section.append(brief);
      }
      const body=node("div","gorge-replay-event-list");
      section.append(body);
      const populate=()=>{
        body.replaceChildren();
        if(!substantive.length){body.append(node("p","small","No events available in this visibility mode."));return;}
        // Render the actual recorded order, never synthesize a gameplay action.
        for(const event of substantive){
          const details=node("details","gorge-replay-event");
          const row=node("summary",null,"#"+event.seq+" · "+eventLine(event,data));
          details.append(row);
          const raw=node("pre","gorge-replay-raw",JSON.stringify(event,null,2));
          details.append(raw);
          body.append(details);
        }
      };
      section.addEventListener("toggle",()=>{
        if(section.open){state.expanded=index;populate();}
        else body.replaceChildren();
      });
      if(section.open)populate();
      list.append(section);
    });
  }
  seatSelect.addEventListener("change",()=>{
    state.seat=Number(seatSelect.value);draw();
  });
  reveal.addEventListener("change",()=>{
    state.reveal=reveal.checked;draw();
  });
  showAll.addEventListener("click",()=>{
    state.all=!state.all;
    showAll.textContent=state.all?"Hide bookkeeping events":"Show all event types";
    draw();
  });
  draw();
}
function init(){
  const input=$("gorge-replay-file"),rootElement=$("gorge-replay-root");
  if(!input||!rootElement)return;
  input.addEventListener("change",async()=>{
    const file=input.files&&input.files[0];
    if(!file)return;
    rootElement.replaceChildren(node("p","small","Reading local gorge replay…"));
    try{
      if(file.size>60*1024*1024)throw Error("Replay exceeds the 60 MB local viewer limit");
      const data=JSON.parse(await file.text());
      paint(rootElement,data);
    }catch(err){
      rootElement.replaceChildren(node("p","gorge-replay-error",
        "Unable to display replay: "+String(err.message||err)));
    }
  });
}
if(typeof document!=="undefined"){
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);
  else init();
}
return {SCHEMA,KINDS,validate,turns,accessibleEvents,eventLine,stats,paint};
});
