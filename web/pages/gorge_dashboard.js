/* Gorge data projected into the ORIGINAL November 3 Deck Lab Results DOM.
 * Keep its art-backed CSS, navigation, metric tiles, insight cards and
 * expandable timeline. Never replace the user's UI with a second dashboard.
 * Source: sanitized gorge-ui-replay-v1 public games, not retired Python runs.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.GorgeDashboard=api;
})(typeof window!=="undefined"?window:globalThis,function(){
"use strict";
const $=id=>document.getElementById(id);
const el=(tag,cls,text)=>{
  const n=document.createElement(tag);
  if(cls)n.className=cls;
  if(text!==undefined&&text!==null)n.textContent=String(text);
  return n;
};
const info=name=>typeof window!=="undefined"&&window.GorgeDeckLabCardInfo?
  window.GorgeDeckLabCardInfo(name):null;
function valid(g){
  return !!g&&g.schema==="gorge-ui-replay-v1"&&g.engine==="gorge"&&
    g.visibility==="public_events_only"&&g.decks?.length===4&&
    Array.isArray(g.turns)&&Array.isArray(g.snapshots)&&
    g.snapshots.every(s=>s.boundary==="first_pending_decision_of_turn"&&
      Array.isArray(s.players)&&s.players.length===4);
}
function actor(e){
  // The native source omits zero-valued player IDs for seat 0.
  return Number.isInteger(e.player)?e.player:0;
}
function occurrences(g,seat){
  const events=g.turns.flatMap(t=>(t.events||[]).map(e=>({event:e,turn:t.turn})));
  return events.filter(x=>actor(x.event)===seat);
}
function analyze(g,seat){
  if(!valid(g)||!Number.isInteger(seat)||seat<0||seat>3)
    throw Error("Expected verified Gorge public game and seat");
  const all=occurrences(g,seat),counts=new Map(),castTurns=new Map();
  let casts=0,lands=0,tokens=0,mana=0;
  for(const {event:e,turn} of all){
    if(e.kind==="cast"){
      casts++;
      if(e.card_name){
        counts.set(e.card_name,(counts.get(e.card_name)||0)+1);
        const a=castTurns.get(e.card_name)||[];
        a.push(turn);castTurns.set(e.card_name,a);
      }
    }else if(e.kind==="land_played")lands++;
    else if(e.kind==="token_created")tokens++;
    else if(e.kind==="mana"&&Number.isFinite(e.amount))mana+=Math.max(0,e.amount);
  }
  const ranked=[...counts].map(([name,count])=>({name,count,turns:castTurns.get(name)}))
    .sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
  const own=g.turns.filter(t=>t.turn>0&&t.seat===seat);
  const timeline=own.map((t,i)=>{
    const next=own[i+1];
    const range=g.turns.filter(x=>x.turn>=t.turn&&(!next||x.turn<next.turn));
    const actions=range.flatMap(x=>(x.events||[]).filter(e=>actor(e)===seat)
      .map(e=>({event:e,turn:x.turn})));
    const atStart=g.snapshots.find(s=>s.turn===t.turn)||null;
    const atNext=next?g.snapshots.find(s=>s.turn===next.turn)||null:null;
    return {number:i+1,nativeTurn:t.turn,nextTurn:next?.turn||null,
      actions,atStart,atNext};
  });
  return {seat,key:g.decks[seat],game:g,casts,lands,tokens,mana,ranked,timeline};
}
function summary(games){
  const decks=new Map();
  for(const g of games.filter(valid))
    for(let seat=0;seat<4;seat++){
      const a=analyze(g,seat);
      const d=decks.get(a.key)||{name:a.key,games:0,casts:0,lands:0,tokens:0};
      d.games++;d.casts+=a.casts;d.lands+=a.lands;d.tokens+=a.tokens;
      decks.set(a.key,d);
    }
  return {decks:[...decks.values()]};
}
function art(name){
  const c=info(name);
  return c?.art||c?.image||null;
}
function artImage(name,css){
  const src=art(name);
  if(!src)return null;
  const img=el("img",css);
  img.src=src;img.alt="";img.loading="lazy";img.referrerPolicy="no-referrer";
  return img;
}
function cardLink(name){
  const card=info(name);
  const n=el(card?.oracle_id?"button":"a","insight-action-card");
  if(card?.oracle_id){
    n.type="button";
    n.addEventListener("click",()=>window.GorgeDeckLabOpenCard?.(name));
  }else{
    n.href="https://scryfall.com/search?q="+encodeURIComponent('!"'+name+'"');
    n.target="_blank";n.rel="noopener noreferrer";
  }
  const img=artImage(name,"insight-action-art");
  if(img)n.append(img);
  n.append(el("span","insight-action-name",name));
  return n;
}
function manaPips(mana){
  const wrap=el("span","gorge-mana-pips");
  for(const [color,count] of Object.entries(mana)){
    if(!/^[WUBRGC]$/.test(color)||count<=0)continue;
    const holder=el("span","gorge-mana-pip");
    const img=el("img","mana-symbol");
    img.src="https://svgs.scryfall.io/card-symbols/"+color+".svg";
    img.alt="{"+color+"}";img.title="{"+color+"}";img.loading="lazy";
    img.onerror=()=>img.replaceWith(el("span","mana-symbol-fallback",color));
    holder.append(img,el("span","insight-mana-count",count>1?"×"+count:""));
    wrap.append(holder);
  }
  return wrap;
}
function metric(label,value,detail){
  const n=el("div","simulation-snapshot-metric");
  n.append(el("span","eyebrow",label),el("strong",null,value));
  if(detail)n.append(el("span","micro",detail));
  return n;
}
function hero(parent,name,records,primary){
  const frame=el("div","game-outcome-hero-frame");
  const outer=el("section","panel game-outcome-card game-outcome-hero");
  const head=el("div","game-outcome-hero-summary");
  const portrait=artImage(name,"game-outcome-hero-art");
  if(portrait)head.append(portrait);
  const copy=el("div","game-outcome-hero-copy");
  copy.append(el("span","eyebrow","Gorge · verified Commander"),
    el("strong","game-outcome-title",name.replace(/_/g," ")));
  const stats=el("div","game-outcome-hero-stats");
  const totals=[
    [records.length,"Recorded games"],
    [records.reduce((n,a)=>n+a.casts,0),"Cast events"],
    [records.reduce((n,a)=>n+a.lands,0),"Land plays"]
  ];
  for(const [value,label] of totals){
    const n=el("div","game-outcome-hero-stat");
    n.append(el("strong",null,value),el("span",null,label));stats.append(n);
  }
  copy.append(stats,el("p","micro","Real four-player Gorge games · 40 starting life · verified winners not exported"));
  head.append(copy);outer.append(head);frame.append(outer);parent.append(frame);
}
function feature(parent,title,name,value,caption,examples){
  const details=el("details","panel game-outcome-card insight-featured-panel");
  const head=el("summary","game-outcome-summary");
  const copy=el("span","game-outcome-summary-copy");
  copy.append(el("strong","game-outcome-title",title),
    el("span","insight-head-name",name),
    el("strong","game-outcome-number",value),
    el("span","board-open","Explore evidence"));
  head.append(copy);
  const img=artImage(name,"insight-featured-cover");
  if(img)head.append(img);
  details.append(head);
  const body=el("div","game-outcome-body");
  body.append(el("p","micro",caption));
  for(const line of examples.slice(0,8)){
    const n=el("div","insight-action-entry");
    n.append(el("span","insight-action-description",line));
    body.append(n);
  }
  details.append(body);parent.append(details);
}
function renderMetrics(games,records){
  const section=$("simulation-snapshot");
  if(!section)return;
  section.hidden=false;
  const scope=$("simulation-snapshot-scope");
  if(scope)scope.textContent="Gorge · public 40-life games";
  const root=$("simulation-snapshot-metrics");
  if(!root)return;
  root.replaceChildren(
    metric("Games",records.length,"Verified public exports"),
    metric("Cast events",records.reduce((n,a)=>n+a.casts,0),"Selected deck"),
    metric("Lands played",records.reduce((n,a)=>n+a.lands,0),"Selected deck"),
    metric("Source games",games.length,"All loaded decks")
  );
}
function renderInsights(records,active){
  const grid=$("key-insights-grid"),empty=$("key-insights-empty");
  if(!grid)return;
  grid.replaceChildren();grid.classList.add("latest-insight-grid");
  if(empty)empty.hidden=true;
  const header=$("key-insights-panel")?.querySelector(".key-insights-heading .micro");
  if(header)header.textContent="Explore recorded cards and genuine turn evidence.";
  const aggregate=new Map();
  for(const a of records)for(const c of a.ranked){
    const row=aggregate.get(c.name)||{name:c.name,count:0,examples:[]};
    row.count+=c.count;
    row.examples.push("Seed "+a.game.seed+" · cast at native turn(s) "+c.turns.join(", "));
    aggregate.set(c.name,row);
  }
  const ranked=[...aggregate.values()].sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
  const lead=ranked[0];
  const commanderName=(active.game.snapshots[0]?.players[active.seat]?.zones?.command||[])[0]?.name||
    active.key.replace(/_/g," ");
  hero(grid,commanderName,records,active);
  feature(grid,"Most cast card",lead?.name||"No identified cast",
    lead?.count??"—","Named public cast events across the selected deck's games.",
    lead?.examples||["The public export contains no named cast."]);
  feature(grid,"Token production","Verified token events",
    records.reduce((n,a)=>n+a.tokens,0),
    "Only source-recorded token-creation events are counted.",
    records.map(a=>"Seed "+a.game.seed+" · "+a.tokens+" token events"));
  const last=active.game.snapshots.filter(s=>s.players[active.seat])
    .slice(-1)[0]?.players[active.seat];
  feature(grid,"Life at turn entry","Life total",
    last?.life??"—",
    "Last available verified turn-entry snapshot, not a final game result.",
    records.map(a=>"Seed "+a.game.seed+" · last published turn-entry snapshot"));
  feature(grid,"Cards in hand","Private identities withheld",
    last?.hand_count??"—",
    "This is a hand COUNT at a turn-entry snapshot. Card identities and turns held are unavailable in the public export.",
    ["For exact hand contents, use a seat-authorized Gorge replay, not the public Pages export."]);
}
function renderOutcomes(records,active,games,deckKey){
  const status=$("game-outcome-status"),out=$("game-outcome-results");
  if(!out)return;
  if(status)status.textContent=records.length+" Gorge game(s) for "+active.key+" · verified 40-life source";
  out.replaceChildren();
  const tool=el("div","game-outcome-toolbar");
  tool.append(el("span","micro","Choose a real recorded game; no modeled opponent personalities."));
  const select=el("select","game-outcome-scenario-select");
  select.setAttribute("aria-label","Select Gorge game");
  for(const a of records){
    const option=el("option",null,"Seed "+a.game.seed+" · "+a.game.decks.join(" / "));
    option.value=String(a.game.seed);select.append(option);
  }
  select.value=String(active.game.seed);
  select.addEventListener("change",()=>render(games,select.value,deckKey));
  tool.append(select);out.append(tool);
  const list=el("div","game-outcome-seeds");
  for(const a of records){
    const button=el("button","game-outcome-seed",
      "Seed "+a.game.seed+" · "+a.game.decks.filter((_,i)=>i!==a.seat).join(" / "));
    button.type="button";
    if(a.game.seed===active.game.seed)button.classList.add("is-selected");
    button.addEventListener("click",()=>render(games,a.game.seed,deckKey));
    list.append(button);
  }
  out.append(list);
  out.append(el("p","micro",
    "Win rates and matchups are pending a verified winner/outcome export. The opponents and card events shown here are real Gorge records."));
}
function eventDescription(e){
  if(e.kind==="cast")return e.card_name?"Cast "+e.card_name:"Cast an unidentified spell";
  if(e.kind==="land_played")return "Played a land (name not exported)";
  if(e.kind==="token_created")return "Created a token";
  if(e.kind==="damage")return "Damage event"+(Number.isFinite(e.amount)?" · "+e.amount:"");
  if(e.kind==="life")return "Life changed"+(Number.isFinite(e.amount)?" · "+e.amount:"");
  if(e.kind==="mana")return (Number(e.amount)<0?"Mana used: ":"Mana produced: ")+
    (e.counter||"unspecified")+(Number.isFinite(e.amount)?" ×"+Math.abs(e.amount):"");
  return e.kind.replace(/_/g," ");
}
function turnSummary(t){
  const notable=t.actions.filter(x=>["cast","land_played","token_created"].includes(x.event.kind));
  if(!notable.length)return "No named plays in the public event log";
  const text=notable.map(x=>x.event.kind==="cast"&&x.event.card_name?
    "Played "+x.event.card_name:eventDescription(x.event)).join(", ");
  return text.length>300?text.slice(0,297)+"…":text;
}
function manaGenerated(t){
  const out={};
  for(const {event:e} of t.actions){
    if(e.kind!=="mana"||!/^[WUBRGC]$/.test(e.counter||""))continue;
    out[e.counter]=(out[e.counter]||0)+Math.max(0,Number(e.amount)||0);
  }
  return out;
}
function zoneDetail(parent,title,cards,extra){
  const block=el("details","insight-turn-zones gorge-public-zone");
  block.append(el("summary",null,title+" · "+cards.length+(extra||"")));
  const body=el("div","insight-action-cards");
  if(!cards.length)body.append(el("span","micro","None recorded"));
  for(const card of cards){
    if(card.name)body.append(cardLink(card.name));
    else body.append(el("span","micro","Unnamed public object"));
  }
  block.append(body);parent.append(block);
}
function stateDetails(parent,t,seat,decks){
  const snap=t.atNext||t.atStart;
  const note=t.atNext?
    "First decision of your NEXT turn (not end of this turn)":
    "First decision of THIS turn (not turn end)";
  if(!snap){parent.append(el("p","micro","No authoritative turn-boundary state in this public replay."));return;}
  const heading=el("div","insight-action-phase is-life");
  heading.append(el("strong","insight-action-phase-heading","Recorded state · "+note));
  for(const player of snap.players){
    const block=el("details","gorge-player-state");
    if(player.seat===seat)block.open=true;
    block.append(el("summary",null,
      (player.seat===seat?"Your deck · ":"Opponent · ")+decks[player.seat]+
      " · ♥ "+player.life+" · Hand "+player.hand_count+
      " · Library "+player.library_count+(player.lost?" · Eliminated":"")));
    const zones=el("div","gorge-player-zones");
    const x=player.zones||{};
    for(const key of ["battlefield","graveyard","exile","command"]){
      const cards=Array.isArray(x[key])?x[key]:[];
      zoneDetail(zones,key.charAt(0).toUpperCase()+key.slice(1),cards);
    }
    zones.append(el("p","micro","Hand: "+player.hand_count+
      " cards. Opponent hand identities are private; individual hand cards cannot be shown from this export."));
    block.append(zones);heading.append(block);
  }
  parent.append(heading);
}
function renderTurnRow(parent,t,a){
  const details=el("details","insight-turn-row gorge-original-turn");
  const head=el("summary","insight-turn-row-summary");
  const first=t.actions.find(x=>x.event.kind==="cast"&&x.event.card_name);
  const cover=first?artImage(first.event.card_name,"insight-turn-cover"):null;
  if(cover)head.append(cover);
  head.append(el("span","insight-turn-label","Turn "+t.number),
    el("span","insight-turn-activity",turnSummary(t)));
  const metrics=el("span","insight-turn-metrics");
  const seatState=(t.atNext||t.atStart)?.players?.[a.seat];
  if(seatState){
    const life=el("span","insight-turn-metric","♥ "+seatState.life);
    const hand=el("span","insight-turn-metric","▤ "+seatState.hand_count);
    life.title="Life at "+(t.atNext?"next":"current")+" turn entry";
    hand.title="Hand COUNT at "+(t.atNext?"next":"current")+" turn entry";
    metrics.append(life,hand);
  }
  const mana=manaGenerated(t);
  if(Object.keys(mana).length){
    const pill=el("span","insight-turn-metric gorge-turn-mana");
    pill.title="Recorded mana produced during this turn cycle (not unspent mana)";
    pill.append(manaPips(mana));metrics.append(pill);
  }
  head.append(metrics,el("span","insight-turn-expand","Explore ▾"));
  details.append(head);
  const body=el("div","insight-turn-row-body");
  const phase=el("div","insight-action-phase is-player");
  phase.append(el("strong","insight-action-phase-heading",
    "Recorded actions · native turn "+t.nativeTurn+
    (t.nextTurn?" through turn "+(t.nextTurn-1):" through last recorded event")));
  const actions=el("div","insight-action-sequence");
  const meaningful=t.actions.filter(x=>["cast","land_played","token_created","mana","damage","life"].includes(x.event.kind));
  for(const {event:e,turn} of meaningful){
    const line=el("div","insight-action-entry");
    line.append(el("span","insight-action-description","T"+turn+" · "+eventDescription(e)));
    if(e.kind==="cast"&&e.card_name)line.append(cardLink(e.card_name));
    actions.append(line);
  }
  if(!meaningful.length)actions.append(el("p","small","No public actions recorded for this deck in this turn cycle."));
  phase.append(actions);body.append(phase);
  stateDetails(body,t,a.seat,a.game.decks);
  body.append(el("p","micro",
    "The public log omits hidden draws and hand identities. State snapshots are turn-entry observations, not claimed end-of-turn counts."));
  details.append(body);parent.append(details);
}
function renderTurns(active){
  const root=$("turn-reviewer-results"),panel=$("turn-reviewer-panel");
  if(!root)return;
  if(panel)panel.hidden=false;
  root.replaceChildren();
  root.append(el("p","micro",
    active.key+" · Seed "+active.game.seed+" · "+active.timeline.length+
    " own turns · real card actions, four-player snapshots and colored mana events"));
  const list=el("div","insight-turn-timeline");
  for(const t of active.timeline)renderTurnRow(list,t,active);
  root.append(list);
}
function renderDevelopment(records){
  const root=$("bounded-results");
  if(!root)return;
  root.replaceChildren();
  root.append(el("p","small",
    "Verified native events across the available public Gorge samples. Larger matchup batches and verified outcomes are not published yet."));
  for(const a of records){
    const x=el("p","small","Seed "+a.game.seed+" · "+
      a.casts+" casts · "+a.lands+" land plays · "+a.tokens+
      " token events · "+a.mana+" generated mana");
    root.append(x);
  }
}
function render(games,activeSeed,deckKey){
  if(typeof document==="undefined")return;
  games=(games||[]).filter(valid);
  const activeKey=deckKey||window.__deckLabActiveKey||null;
  const grid=$("key-insights-grid");
  if(!grid)return;
  const snapshot=$("simulation-snapshot"),out=$("game-outcome-results");
  if(!games.length){
    if(snapshot)snapshot.hidden=true;
    grid.replaceChildren(el("p","small","Loading verified Gorge games…"));
    if(out)out.replaceChildren();
    return;
  }
  let chosen=games.find(g=>String(g.seed)===String(activeSeed)&&
    (!activeKey||g.decks.includes(activeKey)));
  if(!chosen)chosen=games.find(g=>!activeKey||g.decks.includes(activeKey));
  const preview=!chosen;
  if(!chosen)chosen=games[0];
  const seat=activeKey?chosen.decks.indexOf(activeKey):-1;
  const focusSeat=seat>=0?seat:0;
  const records=games.filter(g=>g.decks.includes(chosen.decks[focusSeat]))
    .map(g=>analyze(g,g.decks.indexOf(chosen.decks[focusSeat])));
  const active=records.find(a=>a.game===chosen)||analyze(chosen,focusSeat);
  const title=$("key-insights-title");
  if(title)title.textContent="Key insights";
  renderMetrics(games,records);
  renderInsights(records,active);
  renderOutcomes(records,active,games,activeKey);
  renderTurns(active);
  renderDevelopment(records);
  if(preview){
    const status=$("game-outcome-status");
    if(status)status.textContent="Preview: no verified Gorge sample for selected "+
      activeKey+" · showing "+active.key+" instead";
  }
  // Retired Python diagnostics remain in the archived branch; don't show
  // incompatible outcome rates or example runs on a Gorge-only report.
  for(const id of ["archive-observation-details","opponent-replay-panel"]){
    const n=$(id);if(n)n.hidden=true;
  }
  const quiet=$("pane-records")?.querySelector(".diagnostic-panel");
  if(quiet)quiet.hidden=true;
  const refresh=$("game-outcome-refresh");
  if(refresh)refresh.hidden=true;
}
return {valid,analyze,summary,render};
});
