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
  if(data.enrichment_schema!==undefined){
    if(data.enrichment_schema!=="gorge-physical-state-v1"||
       !Array.isArray(data.objects)||!Array.isArray(data.snapshots))
      throw Error("Unrecognized gorge physical-state enrichment");
    const ids=new Set();
    for(const o of data.objects){
      if(!o||!Number.isInteger(o.object_id)||o.object_id<1||ids.has(o.object_id)||
         typeof o.card_name!=="string")throw Error("Invalid per-game card identity crosswalk");
      ids.add(o.object_id);
    }
    for(const snap of data.snapshots){
      if(!Number.isInteger(snap.turn)||!Array.isArray(snap.players)||snap.players.length!==4||
         snap.boundary!=="first_pending_decision_of_turn")
        throw Error("Invalid authoritative gorge turn-boundary snapshot");
    }
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
function objectName(data,id){
  if(!Number.isInteger(id)||id<=0)return null;
  const card=(data.objects||[]).find(o=>o.object_id===id);
  if(!card)return null;
  return card.card_name||card.effective_name||null;
}
function labelledObject(data,id){
  if(!Number.isInteger(id)||id<=0)return "";
  const name=objectName(data,id);
  return name?name+" (#"+id+")":"object #"+id;
}
function snapshotAtTurn(data,turn){
  return (data.snapshots||[]).find(s=>s.turn===turn)||null;
}
function stateForSeat(data,turn,seat,reveal=false){
  const snap=snapshotAtTurn(data,turn);
  if(!snap)return null;
  const rows=snap.players.map((p,i)=>{
    const zones=p.zones||{};
    const seatIsVisible=seat===i||reveal;
    const publicZones=["battlefield","graveyard","exile","command"];
    const result={seat:i,life:p.life,lost:p.lost,zones:{},
      hand_size:Array.isArray(zones.hand)?zones.hand.length:null,
      library_size:Array.isArray(zones.library)?zones.library.length:null,
      mana_pool:Array.isArray(p.mana_pool)?[...p.mana_pool]:null};
    for(const zone of publicZones){
      result.zones[zone]=(zones[zone]||[]).map(id=>({
        id,name:labelledObject(data,id)}));
    }
    // The owner can see their own hand; an opponent's hand identities must
    // never reach the DOM, even as a hidden JSON detail.
    result.zones.hand=seatIsVisible?(zones.hand||[]).map(id=>({
      id,name:labelledObject(data,id)})):null;
    return result;
  });
  return {turn:snap.turn,step:snap.step,after_event_seq:snap.after_event_seq,
    boundary:snap.boundary,players:rows};
}
function eventLine(e,data){
  const seat=actor(e,data);
  const obj=Number.isInteger(e.obj)?" · "+labelledObject(data,e.obj):"";
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
  const enriched=data.enrichment_schema==="gorge-physical-state-v1";
  const caution=node("p","gorge-replay-caution",
    enriched?
      "Live gorge rules and object identities. State panels are taken at the first decision of each turn, NOT at turn end. Mana pools may be empty at this boundary. Hidden hands are masked by seat.":
      "This older gorge recording contains events only. Card names and exact turn states were not recorded; object IDs cannot be safely inferred. Open a newer enriched trace to inspect zones and hands.");
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
      if(enriched&&game.number>0){
        const stateView=stateForSeat(data,game.number,state.seat,state.reveal);
        if(stateView){
          const statePanel=node("details","gorge-replay-state");
          statePanel.append(node("summary",null,
            "Verified turn-start state · "+stateView.step+" · after event #"+stateView.after_event_seq));
          const stateBody=node("div","gorge-replay-state-grid");
          for(const p of stateView.players){
            const playerBox=node("div","gorge-replay-state-player");
            playerBox.append(node("strong",null,data.decks[p.seat]),
              node("span",null,"Life: "+p.life+" · Hand: "+p.hand_size+
                " · Library: "+p.library_size+(p.lost?" · Eliminated":"")));
            if(Array.isArray(p.mana_pool)){
              const letters=["{W}","{U}","{B}","{R}","{G}","{C}"];
              const mana=p.mana_pool.map((x,i)=>x>0?letters[i]+"×"+x:null).filter(Boolean);
              playerBox.append(node("small",null,
                "Unspent mana at observation: "+(mana.join(" ")||"none")));
            }
            for(const zone of ["hand","battlefield","graveyard","exile","command"]){
              const cards=p.zones[zone];
              const details=node("details","gorge-replay-zone");
              details.append(node("summary",null,
                zone==="hand"&&cards===null?
                  "Hand · "+p.hand_size+" hidden cards":
                  zone[0].toUpperCase()+zone.slice(1)+" · "+(cards||[]).length));
              if(cards!==null){
                details.append(node("p","gorge-replay-card-list",
                  cards.length?cards.map(x=>x.name).join(" · "):"Empty"));
              }
              playerBox.append(details);
            }
            stateBody.append(playerBox);
          }
          statePanel.append(stateBody);
          section.append(statePanel);
        }
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
/* Compact, source-evidenced gorge-ui-replay-v1 for the permanent UI.
 * Full game-state panels remain explicitly unavailable until gorge exports
 * authoritative snapshots. No reconstructed life totals or card identity.
 */
function paintPublicSnapshot(section,snapshot,decks,omniscient=false){
  if(!snapshot||snapshot.boundary!=="first_pending_decision_of_turn")return;
  const details=node("details","gorge-replay-state");
  details.append(node("summary",null,"Verified turn-entry state · "+snapshot.step+
    " · after event #"+snapshot.after_event_seq));
  const grid=node("div","gorge-replay-state-grid");
  const manaSymbols=["{W}","{U}","{B}","{R}","{G}","{C}"];
  for(const player of snapshot.players||[]){
    const card=node("div","gorge-replay-state-player");
    card.append(node("strong",null,decks[player.seat]),
      node("span",null,"Life "+player.life+" · Hand "+player.hand_count+
        " · Library "+player.library_count+(player.lost?" · Eliminated":"")));
    const mana=(player.mana_pool||[]).map((n,i)=>n>0?manaSymbols[i]+" ×"+n:null).filter(Boolean);
    card.append(node("small",null,"Unspent mana: "+(mana.join("  ")||"none")));
    const shown=omniscient?
      ["hand","library","battlefield","graveyard","exile","command"]:
      ["battlefield","graveyard","exile","command"];
    for(const zoneName of shown){
      const cards=player.zones&&player.zones[zoneName]||[];
      const zone=node("details","gorge-replay-zone");
      zone.append(node("summary",null,zoneName+" · "+cards.length));
      const content=node("div","gorge-replay-zone-cards");
      for(const c of cards){
        const link=node("a",null,c.name+" (#"+c.object_id+")");
        link.href="https://scryfall.com/search?q="+encodeURIComponent('!"'+c.name+'"');
        link.rel="noopener noreferrer";link.target="_blank";
        content.append(link);
      }
      if(!cards.length)content.append(node("small",null,"Empty"));
      zone.append(content);card.append(zone);
    }
    grid.append(card);
  }
  details.append(grid);section.append(details);
}
function paintView(rootElement,data){
  if(!data||data.schema!=="gorge-ui-replay-v1"||data.engine!=="gorge"||
     !Array.isArray(data.turns)||!Array.isArray(data.decks)||
     data.decks.length!==4||
     !["public_events_only","omniscient"].includes(data.visibility)||
     (data.visibility==="omniscient"&&data.synthetic_simulation_only!==true))
    throw Error("Expected an explicitly validated synthetic or public gorge-ui-replay-v1 export");
  rootElement.replaceChildren();
  if(typeof window!=="undefined"&&window.GorgeDashboard){
    window.__gorgeActiveGame=data;
    const loaded=window.__gorgeLoadedGames||[data];
    window.GorgeDashboard.render(loaded,data.seed);
  }
  const header=node("div","gorge-replay-header");
  header.append(node("h3",null,"Gorge Commander · Game "+data.seed));
  header.append(node("p","small",data.decks.join(" · ")));
  header.append(node("p","small",data.source.total_native_events+
    " source events · "+data.source.total_native_decisions+
    " decisions · "+data.source.exported_events+
    (data.visibility==="omniscient"?" omniscient display events":" public display events")));
  rootElement.append(header);
  rootElement.append(node("p","gorge-replay-caution",
    data.snapshots?.length?
    data.visibility==="omniscient"?
      "Synthetic omniscient AI game: all four players' opening hands, draws and libraries are visible. Snapshots are at the FIRST pending decision of each turn, NOT turn end.":
      "Authoritative state recorded at the FIRST pending decision of each turn, not turn end. Opponent hand and library identities remain private.":
    "Event-only recording: no authoritative physical state available."));
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
  data.turns.forEach((turn,index)=>{
    const section=node("details","gorge-replay-turn");
    if(index===1)section.open=true;
    const heading=turn.turn===0?"Game setup":
      "Turn "+turn.turn+" · "+(data.decks[turn.seat]||"Seat unknown");
    const summary=node("summary",null,heading);
    summary.append(node("span","gorge-replay-event-count",
      turn.event_count+" recorded events"));
    section.append(summary);
    if(Array.isArray(data.snapshots)){
      const snap=data.snapshots.find(x=>x.turn===turn.turn);
      if(snap)paintPublicSnapshot(section,snap,data.decks,
        data.visibility==="omniscient");
    }
    const highlight=turn.highlights.map(e=>
      e.kind.replace(/_/g," ")+(e.card_name?" · "+e.card_name:
      e.text?" · "+e.text:"")).slice(0,10);
    if(highlight.length)section.append(node("p","gorge-replay-highlights",
      highlight.join(" · ")));
    const body=node("div","gorge-replay-event-list");
    section.append(body);
    let filled=false;
    const fill=()=>{
      if(filled)return;
      filled=true;
      for(const event of turn.events){
        const item=node("details","gorge-replay-event");
        const label="#"+event.seq+" · "+event.kind.replace(/_/g," ")+
          (event.card_name?" · "+event.card_name:"")+
          (event.text&&event.text!==event.card_name?" · "+event.text:"")+
          (event.counter?" · "+event.counter:"")+
          (event.amount!==undefined?" · "+event.amount:"");
        item.append(node("summary",null,label));
        item.append(node("pre","gorge-replay-raw",JSON.stringify(event,null,2)));
        body.append(item);
      }
    };
    section.addEventListener("toggle",()=>{if(section.open)fill();});
    if(section.open)fill();
    list.append(section);
  });
}
function init(){
  const input=$("gorge-replay-file"),rootElement=$("gorge-replay-root");
  if(!input||!rootElement)return;
  // Keep the Gorge source inspector within the original Results layout.
  // The existing page and card selection control all visible report panels.
  // Only load versions explicitly named by the validated public manifest.
  // No hidden gorge native log is fetched or published by this control.
  const samples=$("gorge-replay-samples");
  const select=$("gorge-replay-sample-select");
  const loadButton=$("gorge-replay-load");
  const available=new Set();
  const loadedGames=new Map();
  let manifestVisibility=null,catalogReady=false,requestId=0;
  const catalog=[];
  // Full-cohort outcomes can be much larger than retained detailed replays.
  // Never represent a sample-only card/turn panel as a 500-game measurement.
  const analyticsPromise=fetch("./gorge-data/analytics.json",{cache:"no-store"})
    .then(response=>{
      if(!response.ok)throw Error("Verified outcome catalog unavailable");
      return response.json();
    }).then(value=>{
      if(value.schema!=="gorge-batch-analytics-v1"||
         !Array.isArray(value.games))
        throw Error("Invalid Gorge outcome catalog");
      return value.games;
    }).catch(error=>{
      console.warn("Gorge full-cohort outcomes unavailable",error);
      return null;
    });
  async function presentOutcomeSummary(key,sampledCount,ticket){
    const rows=await analyticsPromise;
    if(ticket!==requestId||!available.size)return;
    const outcomes=$("game-outcome-results");
    if(!outcomes)return;
    const prior=outcomes.querySelector(".gorge-full-cohort-summary");
    if(prior)prior.remove();
    const status=$("game-outcome-status");
    if(!rows){
      if(status)status.textContent=sampledCount+
        " sampled Gorge replays · full-cohort analytics unavailable";
      return;
    }
    const valid=rows.filter(r=>
      r&&r.finished===true&&r.replay_verified===true&&
      Number.isInteger(r.player_seat)&&r.player_seat>=0&&r.player_seat<4&&
      Array.isArray(r.decks)&&r.decks[r.player_seat]===key&&
      (r.player_deck===undefined||r.player_deck===key)&&
      (r.draw===true||Number.isInteger(r.winner_seat)));
    if(!valid.length)return;
    const wins=valid.filter(r=>!r.draw&&r.winner_seat===r.player_seat).length;
    const draws=valid.filter(r=>r.draw).length;
    const losses=valid.length-wins-draws;
    const pct=(100*wins/valid.length).toFixed(1);
    const summary=node("p","gorge-full-cohort-summary",
      "Full verified cohort: "+valid.length+" games · "+wins+" wins ("+pct+
      "%) · "+losses+" losses · "+draws+" draws. Detailed turn and card insights "+
      "below use "+sampledCount+" retained source-backed replay"+
      (sampledCount===1?"":"s")+", not the entire cohort.");
    outcomes.prepend(summary);
    if(status)status.textContent=valid.length+" verified Gorge games · "+
      sampledCount+" detailed sampled replays · source-attributed player seats";
  }
  // The catalog records the designated player seat. A small number of
  // verified Gorge recordings predate embedding that attribution in replay
  // JSON; their original source bytes remain unchanged and are matched by
  // seed, chain, complete deck order and archived workflow provenance.
  function playerEntry(row,key){
    return row&&Number.isInteger(row.player_seat)&&row.player_seat>=0&&
      row.player_seat<4&&Array.isArray(row.decks)&&
      row.player_deck===key&&row.decks[row.player_seat]===key&&
      typeof row.file==="string"&&
      /^gorge-seed-[0-9]+\.ui\.json$/.test(row.file);
  }
  function recentFirst(a,b){
    return String(b.simulated_at||"").localeCompare(String(a.simulated_at||""))||
      Number(b.seed||0)-Number(a.seed||0);
  }
  async function loadVerifiedReplay(name){
    let data=loadedGames.get(name);
    if(data)return data;
    const response=await fetch("./gorge-data/"+encodeURIComponent(name),
      {cache:"no-store"});
    if(!response.ok)throw Error("Public Gorge replay unavailable: "+name);
    data=await response.json();
    const entry=catalog.find(row=>row.file===name);
    if(data.schema!=="gorge-ui-replay-v1"||
       data.visibility!==manifestVisibility||
       (manifestVisibility==="omniscient"&&data.synthetic_simulation_only!==true)||
       !Array.isArray(data.snapshots)||!data.snapshots.length||
       !entry||data.seed!==entry.seed||data.chain!==entry.chain||
       !Array.isArray(data.decks)||data.decks.length!==4||
       data.decks.some((deck,i)=>deck!==entry.decks[i])||
       !playerEntry(entry,entry.player_deck))
      throw Error("Unverified player-seat Gorge replay or visibility");
    const embedded=data.player_seat===entry.player_seat&&
      data.player_deck===entry.player_deck;
    const legacy=data.player_seat===undefined&&data.player_deck===undefined&&
      entry.source_player_role_evidence?.kind==="verified-workflow-player-role-v1"&&
      Number.isInteger(entry.source_player_role_evidence.workflow_run_id);
    if(!embedded&&!legacy)
      throw Error("Replay player role differs from the verified catalog");
    // Source bytes are unchanged. Verified historical player-seat metadata is
    // projected for display, but never guessed from a deck's appearance.
    if(legacy)data={...data,player_seat:entry.player_seat,
      player_deck:entry.player_deck,player_role_provenance:"verified archived workflow"};
    loadedGames.set(name,data);
    return data;
  }
  async function openPublicSample(name){
    if(!available.has(name))throw Error("Replay is not a player-seat game for this deck");
    const ticket=++requestId;
    rootElement.replaceChildren(node("p","small","Loading verified Gorge game…"));
    const data=await loadVerifiedReplay(name);
    if(ticket!==requestId||!available.has(name))return;
    if(typeof window!=="undefined")window.__gorgeLoadedGames=[data];
    paintView(rootElement,data);
    // The selected replay is the evidence drilldown, not the entire cohort.
    // Aggregate only exact, independently verified player-seat replays, with
    // bounded concurrent downloads so the mobile UI remains responsive.
    const other=[...catalog].filter(row=>
      playerEntry(row,data.player_deck)&&available.has(row.file)&&row.file!==name)
      .sort(recentFirst);
    if(!other.length){
      await presentOutcomeSummary(data.player_deck,1,ticket);
      return;
    }
    const cohort=[data];
    let cursor=0;
    async function worker(){
      while(cursor<other.length&&ticket===requestId){
        const row=other[cursor++];
        try{
          const game=await loadVerifiedReplay(row.file);
          if(ticket===requestId)cohort.push(game);
        }catch(error){
          console.warn("Source-verified Gorge game excluded from aggregation",row.seed,error);
        }
      }
    }
    await Promise.all(Array.from({length:Math.min(3,other.length)},()=>worker()));
    if(ticket!==requestId||!available.has(name))return;
    if(typeof window!=="undefined")window.__gorgeLoadedGames=cohort;
    window.GorgeDashboard?.render(cohort,data.seed,data.player_deck);
    await presentOutcomeSummary(data.player_deck,cohort.length,ticket);
    if(cohort.length<other.length+1){
      const status=$("game-outcome-status");
      if(status)status.textContent+=" · "+(other.length+1-cohort.length)+
        " replays unavailable or excluded";
    }
  }
  function refreshForPlayer(){
    if(!catalogReady)return;
    ++requestId;
    const key=window.__deckLabActiveKey;
    const previous=select.value;
    available.clear();
    select.replaceChildren();
    for(const game of [...catalog].sort(recentFirst)){
      if(!playerEntry(game,key))continue;
      available.add(game.file);
      const option=node("option",null,"Seed "+game.seed+" · "+
        game.decks.filter((_,i)=>i!==game.player_seat).join(" / "));
      option.value=game.file;select.append(option);
    }
    samples.hidden=!available.size;
    if(typeof window!=="undefined")window.__gorgeLoadedGames=[];
    if(!available.size){
      rootElement.replaceChildren(node("p","small",
        "No simulations have been run with this selected deck in the player seat."));
      window.GorgeDashboard?.render([],null,key);
      return;
    }
    select.value=available.has(previous)?previous:select.options[0].value;
    openPublicSample(select.value).catch(err=>
      rootElement.replaceChildren(node("p","gorge-replay-error",
        "Unable to display Gorge replay: "+String(err.message||err))));
  }
  if(typeof window!=="undefined")
    window.GorgeDeckLabRefreshSamples=refreshForPlayer;
  if(samples&&select&&loadButton){
    loadButton.addEventListener("click",()=>{
      openPublicSample(select.value).catch(err=>
        rootElement.replaceChildren(node("p","gorge-replay-error",
          "Unable to display Gorge replay: "+String(err.message||err))));
    });
    fetch("./gorge-data/manifest.json",{cache:"no-store"}).then(response=>{
      if(!response.ok)throw Error("No published Gorge catalog");
      return response.json();
    }).then(manifest=>{
      const omniscient=manifest.schema==="gorge-omniscient-replay-manifest-v1"&&
        manifest.visibility==="omniscient"&&manifest.synthetic_simulation_only===true;
      if(!omniscient&&manifest.schema!=="gorge-public-replay-manifest-v1")
        throw Error("Unsupported Gorge catalog");
      if(!Array.isArray(manifest.games))throw Error("Unsupported manifest games");
      manifestVisibility=omniscient?"omniscient":"public_events_only";
      catalog.push(...manifest.games);
      catalogReady=true;
      refreshForPlayer();
    }).catch(error=>{
      rootElement.replaceChildren(node("p","gorge-replay-error",
        "Gorge results catalog unavailable: "+String(error.message||error)));
    });
  }
  input.addEventListener("change",async()=>{
    const file=input.files&&input.files[0];
    if(!file)return;
    rootElement.replaceChildren(node("p","small","Reading local gorge replay…"));
    try{
      if(file.size>60*1024*1024)throw Error("Replay exceeds the 60 MB local viewer limit");
      const data=JSON.parse(await file.text());
      if(data.schema==="gorge-ui-replay-v1")paintView(rootElement,data);
      else paint(rootElement,data);
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
return {SCHEMA,KINDS,validate,turns,accessibleEvents,eventLine,stats,paint,objectName,stateForSeat};
});
