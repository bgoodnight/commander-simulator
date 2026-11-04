/* Original Deck Lab's art-backed card insights and nested example-game turns.
 * Data is exclusively verified, sanitized Gorge public replay events.
 * Native turn-entry snapshots are NEVER represented as end-of-turn states.
 * Hidden hand identities, individual draws and game winners are unavailable.
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
const openCard=name=>typeof window!=="undefined"&&window.GorgeDeckLabOpenCard?.(name);
const fmt=n=>Number.isFinite(n)?String(n):"—";
const colors=["W","U","B","R","G","C"];
function valid(g){
  return !!g&&g.schema==="gorge-ui-replay-v1"&&g.engine==="gorge"&&
    g.visibility==="public_events_only"&&Array.isArray(g.decks)&&g.decks.length===4&&
    Array.isArray(g.turns)&&Array.isArray(g.snapshots)&&g.snapshots.length>0&&
    g.snapshots.every(s=>s.boundary==="first_pending_decision_of_turn"&&
      Array.isArray(s.players)&&s.players.length===4);
}
function actor(e){return Number.isInteger(e.player)?e.player:0;}
function ownTurnFor(nativeTurn,starts){
  let n=0;
  for(const start of starts)if(start<=nativeTurn)n++;else break;
  return Math.max(1,n);
}
function analyze(g,seat){
  if(!valid(g)||!Number.isInteger(seat)||seat<0||seat>3)
    throw Error("Expected verified public Gorge Commander game and seat");
  const own=g.turns.filter(t=>t.turn>0&&t.seat===seat);
  const starts=own.map(t=>t.turn);
  const casts=new Map();
  let castCount=0,lands=0,tokens=0,mana=0;
  for(const t of g.turns){
    for(const e of t.events||[]){
      if(actor(e)!==seat)continue;
      if(e.kind==="cast"){
        castCount++;
        if(e.card_name){
          const row=casts.get(e.card_name)||{name:e.card_name,count:0,turns:[],nativeTurns:[]};
          row.count++;row.turns.push(ownTurnFor(t.turn,starts));
          row.nativeTurns.push(t.turn);casts.set(e.card_name,row);
        }
      }else if(e.kind==="land_played")lands++;
      else if(e.kind==="token_created")tokens++;
      else if(e.kind==="mana"&&Number(e.amount)>0)mana+=Number(e.amount);
    }
  }
  const publicNames=new Map();
  for(const snap of g.snapshots)for(const p of snap.players||[])
    for(const cards of Object.values(p.zones||{}))for(const card of cards||[])
      if(Number.isInteger(card.object_id)&&card.name)publicNames.set(card.object_id,card.name);
  for(const t of g.turns)for(const e of t.events||[])
    if(Number.isInteger(e.obj)&&e.card_name)publicNames.set(e.obj,e.card_name);
  const timeline=own.map((t,i)=>{
    const next=own[i+1]||null;
    const range=g.turns.filter(x=>x.turn>=t.turn&&(!next||x.turn<next.turn));
    return {number:i+1,nativeTurn:t.turn,nextTurn:next?.turn||null,
      actions:range.flatMap(x=>(x.events||[]).filter(e=>actor(e)===seat)
        .map(event=>({event,turn:x.turn}))),
      atStart:g.snapshots.find(s=>s.turn===t.turn)||null,
      atNext:next?g.snapshots.find(s=>s.turn===next.turn)||null:null};
  });
  return {seat,key:g.decks[seat],game:g,publicNames,casts:castCount,lands,tokens,mana,
    ranked:[...casts.values()].sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name)),
    timeline};
}
function summary(games){
  const decks=new Map();
  for(const g of games.filter(valid)){
    for(let seat=0;seat<4;seat++){
      const a=analyze(g,seat);
      const d=decks.get(a.key)||{name:a.key,games:0,casts:0,lands:0,tokens:0};
      d.games++;d.casts+=a.casts;d.lands+=a.lands;d.tokens+=a.tokens;decks.set(a.key,d);
    }
  }
  return {decks:[...decks.values()]};
}
function art(name){
  const c=info(name);
  return c?.art||c?.image||null;
}
function artImage(name,cls){
  const src=art(name);
  if(!src)return null;
  const img=el("img",cls);
  img.src=src;img.alt="";img.loading="lazy";img.referrerPolicy="no-referrer";
  return img;
}
function cardButton(name,cls="insight-action-card"){
  const known=info(name);
  const btn=el(known?.oracle_id?"button":"a",cls);
  if(known?.oracle_id){
    btn.type="button";
    btn.addEventListener("click",()=>openCard(name));
  }else{
    btn.href="https://scryfall.com/search?q="+encodeURIComponent('!"'+name+'"');
    btn.target="_blank";btn.rel="noopener noreferrer";
  }
  const image=artImage(name,"insight-action-art");
  if(image)btn.append(image);
  btn.append(el("span","insight-action-name",name));
  return btn;
}
function manaPips(out){
  const holder=el("span","gorge-mana-pips");
  for(const color of colors){
    const count=out[color]||0;
    if(count<=0)continue;
    const pip=el("span","gorge-mana-pip");
    const icon=el("img","mana-symbol");
    icon.src="https://svgs.scryfall.io/card-symbols/"+color+".svg";
    icon.alt="{"+color+"}";icon.title="{"+color+"}";icon.loading="lazy";
    icon.onerror=()=>icon.replaceWith(el("span","mana-symbol-fallback",color));
    pip.append(icon);
    if(count>1)pip.append(el("span","insight-mana-count","×"+count));
    holder.append(pip);
  }
  if(!holder.children.length)holder.append(el("span","gorge-zero-mana","0"));
  return holder;
}
function sourceMana(t){
  const result={};
  for(const {event:e} of t.actions)
    if(e.kind==="mana"&&colors.includes(e.counter)&&Number(e.amount)>0)
      result[e.counter]=(result[e.counter]||0)+Number(e.amount);
  return result;
}
function median(nums){
  const data=nums.filter(Number.isFinite).sort((a,b)=>a-b);
  if(!data.length)return null;
  const i=Math.floor(data.length/2);
  return data.length%2?data[i]:(data[i-1]+data[i])/2;
}
function typeOf(name){
  return String(info(name)?.type_line||"").split("—")[0].toLowerCase();
}
function cardGroups(records){
  const cast=new Map();
  for(const a of records){
    for(const c of a.ranked){
      let row=cast.get(c.name);
      if(!row){row={name:c.name,count:0,turns:[],games:new Set(),examples:[]};cast.set(c.name,row);}
      row.count+=c.count;row.turns.push(...c.turns);row.games.add(a.game.seed);
      for(let i=0;i<c.turns.length;i++)
        row.examples.push({analysis:a,ownTurn:c.turns[i],nativeTurn:c.nativeTurns[i]});
    }
  }
  const all=[...cast.values()].sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
  const matching=pattern=>all.filter(c=>pattern.test(typeOf(c.name)));
  return [
    ["Most played card",all],
    ["Most played creature",matching(/\bcreature\b/)],
    ["Most played artifact",matching(/\bartifact\b/)],
    ["Most played instant or sorcery",matching(/\b(instant|sorcery)\b/)]
  ];
}
function commanderName(a){
  const snap=a.game.snapshots.find(s=>s.players?.[a.seat]?.zones?.command?.length);
  return snap?.players?.[a.seat]?.zones?.command?.[0]?.name||
    a.key.replace(/_/g," ");
}
function hero(parent,records,active){
  const name=commanderName(active);
  const frame=el("div","game-outcome-hero-frame");
  const card=el("section","panel game-outcome-card game-outcome-hero");
  const summary=el("div","game-outcome-hero-summary");
  const picture=artImage(name,"game-outcome-hero-art");
  if(picture)summary.append(picture);
  const copy=el("div","game-outcome-hero-copy");
  copy.append(el("span","eyebrow","Full Commander · Gorge engine"),
    el("strong","game-outcome-title",name));
  const metrics=el("div","game-outcome-hero-stats");
  for(const [number,label] of [
    [records.length,"Recorded games"],
    [records.reduce((n,a)=>n+a.casts,0),"Cast events"],
    [records.reduce((n,a)=>n+a.lands,0),"Land plays"]]){
    const stat=el("div","game-outcome-hero-stat");
    stat.append(el("strong",null,number),el("span",null,label));
    metrics.append(stat);
  }
  copy.append(metrics,
    el("span","game-outcome-hero-meta",
      "Verified 40-life Commander games · wins and matchup percentages pending outcome export"));
  summary.append(copy);card.append(summary);frame.append(card);parent.append(frame);
}
/* A public land-play marker follows the visible hand-to-battlefield move.
 * Only name a land when its exact object ID is identified in a native event
 * or visible-zone snapshot. Never infer a private draw from hand changes. */
function landIdentity(a,e,t){
  const candidate=(t.events||[]).find(x=>x.kind==="zone_change"&&
    x.from===1&&x.to===2&&Number.isInteger(x.obj)&&
    e.seq-x.seq>=0&&e.seq-x.seq<=3);
  return candidate?a.publicNames.get(candidate.obj)||null:null;
}
function turnNarration(t,a){
  const parts=[];
  for(const x of t.actions){
    const e=x.event;
    if(e.kind==="land_played"){
      const row=a.game.turns.find(t=>t.turn===x.turn);
      const name=row?landIdentity(a,e,row):null;
      parts.push("Played "+(name||"a land"));
    }else if(e.kind==="cast"&&e.card_name)parts.push("Played "+e.card_name);
    else if(e.kind==="cast")parts.push("Cast an unnamed spell");
    else if(e.kind==="token_created")parts.push("Created a token");
  }
  if(!parts.length)return "No named plays recorded";
  return parts.join(", ");
}
function pill(value,icon,delta,caption){
  const badge=el("span","insight-turn-metric"+
    (Number.isFinite(delta)&&delta!==0?(delta>0?" is-gain":" is-loss"):""));
  badge.title=caption;
  badge.append(el("span",null,icon+" "+fmt(value)));
  if(Number.isFinite(delta)&&delta!==0)
    badge.append(el("span","gorge-metric-delta",
      " ("+(delta>0?"+":"")+delta+")"));
  return badge;
}
function zoneSummary(parent,title,icon,cards,opts={}){
  const node=el("details","insight-end-zone");
  if(opts.name)node.dataset.zone=opts.name;
  const head=el("summary","insight-end-zone-label");
  head.append(el("span","insight-end-zone-icon",icon),
    el("span",null,title+" · "+cards.length));
  node.append(head);
  const list=el("div","insight-action-cards");
  if(opts.private){
    list.append(el("p","micro","Only the number of cards is published. Individual hand identities require a seat-authorized trace."));
  }else if(!cards.length){
    list.append(el("span","micro","None"));
  }else for(const card of cards){
    const name=typeof card==="string"?card:card.name;
    if(name)list.append(cardButton(name));
  }
  node.append(list);parent.append(node);return node;
}
function zoneCategories(p){
  const all=p.zones?.battlefield||[];
  const match=pattern=>all.filter(card=>pattern.test(typeOf(card.name)));
  const typed=card=>/\b(creature|artifact|enchantment|land|planeswalker|battle)\b/.test(typeOf(card.name));
  return [
    ["Creatures","♟",match(/\bcreature\b/),"creatures"],
    ["Lands","◇",match(/\bland\b/),"lands"],
    ["Artifacts","⚙",match(/\bartifact\b/),"artifacts"],
    ["Enchantments","✦",match(/\benchantment\b/),"enchantments"],
    ["Other permanents","◈",all.filter(card=>!typed(card)),"other"],
    ["Graveyard","◆",p.zones?.graveyard||[],"graveyard"],
    ["Exile","⊘",p.zones?.exile||[],"exile"]
  ];
}
function statePanel(t,a){
  const snap=t.atNext||t.atStart;
  const section=el("section","insight-end-state gorge-boundary-state");
  const label=t.atNext?"Next observed turn entry":"Recorded turn entry";
  section.append(el("strong","insight-end-state-title",
    label+" · not an end-of-turn snapshot"));
  if(!snap){
    section.append(el("p","micro","No verified state snapshot for this turn."));
    return section;
  }
  const focus=snap.players[a.seat];
  section.append(el("p","micro",
    "Life "+focus.life+" · Hand "+focus.hand_count+
    " · Library "+focus.library_count+
    " · Battlefield "+(focus.zones?.battlefield?.length||0)+
    " · Graveyard "+(focus.zones?.graveyard?.length||0)));
  zoneSummary(section,"Hand","▤",Array(focus.hand_count).fill(null),
    {name:"hand",private:true});
  for(const [name,icon,cards,key] of zoneCategories(focus))
    zoneSummary(section,name,icon,cards,{name:key});
  const manaLine=el("div","insight-end-mana");
  manaLine.append(el("strong",null,"Mana produced"),manaPips(sourceMana(t)));
  section.append(manaLine);
  const others=el("details","gorge-opponent-snapshots");
  others.append(el("summary",null,"Table state · all four players"));
  const grid=el("div","gorge-table-state-grid");
  for(const p of snap.players){
    const col=el("div","gorge-table-state-seat");
    col.append(el("strong",null,a.game.decks[p.seat]),
      el("span",null,"♥ "+p.life+" · Hand "+p.hand_count+
        " · Battlefield "+(p.zones?.battlefield?.length||0)+
        (p.lost?" · Eliminated":"")));
    for(const key of ["battlefield","graveyard","exile"]){
      const cards=p.zones?.[key]||[];
      zoneSummary(col,key.charAt(0).toUpperCase()+key.slice(1),"◈",cards);
    }
    grid.append(col);
  }
  others.append(grid);section.append(others);
  return section;
}
function turnRow(parent,t,a,options={}){
  const row=el("details","insight-turn-row gorge-original-turn");
  if(options.open)row.open=true;
  const head=el("summary","insight-turn-row-summary");
  const named=t.actions.filter(x=>x.event.kind==="cast"&&x.event.card_name);
  const spotlight=named
    .map(x=>({name:x.event.card_name,cmc:Number(info(x.event.card_name)?.mana_value)||0}))
    .filter(x=>art(x.name)).sort((x,y)=>y.cmc-x.cmc)[0]?.name||
    commanderName(a);
  const cover=artImage(spotlight,"insight-turn-cover");
  if(cover)head.append(cover);
  head.append(el("strong","insight-turn-label","Turn "+t.number),
    el("span","insight-turn-activity",turnNarration(t,a)));
  const badges=el("span","insight-turn-metrics");
  const current=t.atStart?.players?.[a.seat]||null;
  const next=(t.atNext||t.atStart)?.players?.[a.seat]||null;
  if(next){
    const available=!!t.atNext&&!!current;
    badges.append(pill(next.life,"♥",available?next.life-current.life:null,
      "Life at "+(t.atNext?"next own turn entry":"this turn entry")+", not at end of turn"));
    const hand=el("button","insight-turn-metric insight-hand-shortcut",
      "▤ "+next.hand_count);
    hand.type="button";
    hand.title="Hand count at "+(t.atNext?"next own turn entry":"this turn entry")+
      " · click to inspect available hand information";
    hand.addEventListener("click",event=>{
      event.preventDefault();event.stopPropagation();row.open=true;
      const section=row.querySelector('[data-zone="hand"]');
      if(section)section.open=true;
    });
    badges.append(hand);
  }
  const mana=el("span","insight-turn-metric insight-turn-mana");
  mana.title="Positive mana-production events recorded during this turn cycle; mana spent is excluded";
  mana.append(el("span","gorge-mana-label","Mana "),manaPips(sourceMana(t)));
  badges.append(mana);
  head.append(badges,el("span","insight-turn-expand","Explore"));
  row.append(head);
  const body=el("div","insight-turn-row-body");
  const actions=t.actions.filter(x=>
    ["cast","land_played","token_created","damage","life","mana"].includes(x.event.kind));
  const actionPanel=el("section","insight-action-phase is-player");
  actionPanel.append(el("h4","insight-action-phase-heading",
    "Recorded actions · your turn "+t.number));
  const list=el("div","insight-action-sequence");
  const notable=actions.filter(x=>x.event.kind!=="mana");
  if(!notable.length)list.append(el("p","micro","No named plays recorded."));
  for(const {event:e,turn} of notable){
    const item=el("div","insight-action-entry");
    const verb=e.kind==="cast"?"Cast":e.kind==="land_played"?"Played":
      e.kind==="token_created"?"Created":"Recorded";
    const nativeRow=a.game.turns.find(x=>x.turn===turn);
    const knownLand=e.kind==="land_played"&&nativeRow?landIdentity(a,e,nativeRow):null;
    const message=e.kind==="cast"?(e.card_name||"unidentified spell"):
      e.kind==="land_played"?(knownLand||"a land (identity not exported)"):
      e.kind==="token_created"?"a token":
      e.kind==="damage"?"damage event "+(e.amount??""):
      "life adjustment "+(e.amount??"");
    item.append(el("span","insight-action-description",
      verb+" "+message+(turn!==t.nativeTurn?" · during native turn "+turn:"")));
    if(e.kind==="cast"&&e.card_name)item.append(cardButton(e.card_name));
    if(e.kind==="land_played"&&knownLand)item.append(cardButton(knownLand));
    list.append(item);
  }
  actionPanel.append(list);body.append(actionPanel,statePanel(t,a));
  body.append(el("p","micro",
    "The public export does not contain exact private draws or hand cards. State comparisons use verified turn-entry snapshots, not invented turn-end values."));
  row.append(body);parent.append(row);
  return row;
}
function openingRow(parent,a){
  const first=a.timeline[0];
  const p=first?.atStart?.players?.[a.seat];
  const row=el("details","insight-turn-row gorge-original-turn gorge-opening-turn");
  const summary=el("summary","insight-turn-row-summary");
  const cover=artImage(commanderName(a),"insight-turn-cover");
  if(cover)summary.append(cover);
  summary.append(el("strong","insight-turn-label","Draw"),
    el("span","insight-turn-activity",
      "Opening hand · "+(p?fmt(p.hand_count):"unknown")+" cards"));
  const badges=el("span","insight-turn-metrics");
  if(p){
    badges.append(pill(p.life,"♥",null,"Life at first recorded own-turn entry"));
    const hand=el("span","insight-turn-metric","▤ "+p.hand_count);
    hand.title="Hand count only. Private card identities not published.";
    badges.append(hand);
  }
  summary.append(badges,el("span","insight-turn-expand","Explore"));
  row.append(summary);
  const body=el("div","insight-turn-row-body");
  body.append(el("p","micro",
    "Opening hand identities and mulligans are not present in the public replay. Only the observed hand count is shown."));
  if(first)body.append(statePanel({...first,atNext:null},a));
  row.append(body);parent.append(row);
}
function timeline(parent,a,focus){
  const list=el("div","insight-turn-timeline gorge-example-timeline");
  openingRow(list,a);
  for(const t of a.timeline)turnRow(list,t,a,{open:focus===t.number});
  parent.append(list);
  return list;
}
function renderTurns(a,focus){
  const panel=$("turn-reviewer-panel"),root=$("turn-reviewer-results");
  if(!root||!panel)return;
  root.replaceChildren();
  panel.hidden=false;
  const head=el("div","gorge-full-review-head");
  head.append(el("p","small","Seed "+a.game.seed+" · "+a.key.replace(/_/g," ")+
    " · full evidence viewer"));
  const close=el("button","stone-button","Close reviewer");
  close.type="button";
  close.onclick=()=>{panel.hidden=true;};
  head.append(close);root.append(head);
  timeline(root,a,focus);
  if(typeof panel.scrollIntoView==="function")panel.scrollIntoView({behavior:"smooth",block:"start"});
}
function examplesFor(row){
  const seen=new Set(),out=[];
  for(const e of row.examples.sort((a,b)=>a.ownTurn-b.ownTurn||a.analysis.game.seed-b.analysis.game.seed)){
    const id=e.analysis.game.seed+"|"+e.ownTurn;
    if(seen.has(id))continue;
    seen.add(id);out.push(e);
  }
  return out.slice(0,12);
}
function feature(parent,title,candidates){
  if(!candidates.length){
    const empty=el("section","panel gorge-insight-unavailable");
    empty.append(el("strong","game-outcome-title",title),
      el("p","small","No named, metadata-classified cast events in the available Gorge sample."));
    parent.append(empty);
    return;
  }
  const panel=el("details","panel game-outcome-card insight-featured-panel insight-card-with-evidence");
  const head=el("summary","game-outcome-summary");
  const copy=el("span","game-outcome-summary-copy");
  const titleElement=el("strong","game-outcome-title",title);
  const subtitle=el("span","insight-head-subtitle");
  const nameElement=el("span","insight-head-name");
  const cost=el("span","insight-head-mana");
  subtitle.append(nameElement,cost);
  const number=el("span","game-outcome-number");
  copy.append(titleElement,subtitle,number,el("span","board-open","Explore card evidence"));
  head.append(copy);
  const cover=el("img","insight-featured-cover");
  cover.alt="";cover.loading="lazy";cover.referrerPolicy="no-referrer";
  head.append(cover);panel.append(head);
  const body=el("div","game-outcome-body");
  const compare=el("div","insight-featured-compare");
  const featured=el("div","insight-featured-selected");
  const ranking=el("div","insight-featured-ranking");
  ranking.append(el("strong","insight-featured-chart-title","Top cards"),
    el("p","micro","Select a card to inspect its recorded games"));
  const bars=el("div","insight-featured-bars");
  ranking.append(bars);compare.append(featured,ranking);body.append(compare);
  const metrics=el("div","insight-featured-stats");
  const evidence=el("div","insight-featured-evidence");
  body.append(metrics,evidence);panel.append(body);parent.append(panel);
  const maxCount=Math.max(1,...candidates.slice(0,10).map(x=>x.count));
  const buttons=[];
  function choose(item){
    nameElement.textContent=item.name;
    number.textContent=item.count+" "+(item.count===1?"cast":"casts");
    const value=art(item.name);
    if(value){cover.src=value;cover.hidden=false;}else{cover.hidden=true;cover.removeAttribute("src");}
    cost.replaceChildren();
    const printed=String(info(item.name)?.mana_cost||"");
    for(const token of printed.matchAll(/\{([^{}]+)\}/g)){
      const n=token[1].replace("/","");
      const icon=el("img","mana-symbol");
      icon.src="https://svgs.scryfall.io/card-symbols/"+n+".svg";
      icon.alt=token[0];icon.title=token[0];cost.append(icon);
    }
    for(const btn of buttons)btn.setAttribute("aria-pressed",String(btn.dataset.card===item.name));
    featured.replaceChildren();metrics.replaceChildren();evidence.replaceChildren();
    const btn=cardButton(item.name,"insight-featured-card-art");
    btn.replaceChildren();
    const fullArt=info(item.name)?.image||art(item.name);
    if(fullArt){
      const picture=el("img");
      picture.src=fullArt;picture.alt=item.name+" printed card";
      picture.loading="lazy";picture.referrerPolicy="no-referrer";
      btn.append(picture);
    }else btn.append(el("span","insight-featured-card-name",item.name));
    featured.append(btn,el("strong","insight-featured-card-name",item.name));
    const examples=examplesFor(item);
    let selectedExample=0,tracker=null,detail=null,select=null;
    function populate(){
      if(!detail||!examples.length)return;
      const ex=examples[selectedExample];
      detail.replaceChildren();
      const heading=el("div","game-outcome-evidence-head");
      heading.append(el("strong",null,"Seed "+ex.analysis.game.seed+" · Replay"),
        el("span","micro","observed through round "+ex.analysis.timeline.length));
      detail.append(heading);
      timeline(detail,ex.analysis,ex.ownTurn);
      if(select)select.value=String(selectedExample);
    }
    function openExample(){
      if(!examples.length)return;
      if(!tracker.open)selectedExample=0;
      else selectedExample=(selectedExample+1)%examples.length;
      tracker.open=true;populate();
    }
    const tiles=el("div","game-outcome-insight-grid insight-featured-metrics");
    for(const [label,value] of [
      ["Times played",item.count],
      ["Median event turn",median(item.turns)]
    ]){
      const button=el("button","game-outcome-insight-metric insight-featured-metric-link");
      button.type="button";button.disabled=!examples.length;
      button.append(el("span",null,label),el("strong",null,value===null?"—":value));
      button.setAttribute("aria-label",label+" · open next verified example game");
      button.onclick=openExample;tiles.append(button);
    }
    metrics.append(tiles);
    if(!examples.length)return;
    tracker=el("details","insight-inline-tracker insight-inline-tracker-compact");
    const trigger=el("summary",null,"View example games");
    tracker.append(trigger);
    const full=el("button","game-outcome-review-link insight-example-full-link","Open full reviewer ↗");
    full.type="button";full.onclick=()=>{
      const ex=examples[selectedExample];
      renderTurns(ex.analysis,ex.ownTurn);
    };
    const control=el("div","gorge-insight-game-control");
    select=el("select","gorge-insight-example-select");
    select.setAttribute("aria-label","Choose a recorded Gorge game and focus turn");
    examples.forEach((ex,i)=>{
      const o=el("option",null,"4-player · Seed "+ex.analysis.game.seed+
        " · Turn "+ex.ownTurn);
      o.value=String(i);select.append(o);
    });
    select.onchange=()=>{selectedExample=Number(select.value);populate();};
    control.append(select,full);
    detail=el("div","insight-inline-tracker-review");
    tracker.append(control,detail);
    tracker.addEventListener("toggle",()=>{if(tracker.open)populate();});
    evidence.append(tracker);
  }
  for(const candidate of candidates.slice(0,10)){
    const button=el("button","insight-featured-bar");
    button.type="button";button.dataset.card=candidate.name;
    button.setAttribute("aria-label","Inspect "+candidate.name);
    const caption=el("span","insight-featured-bar-caption");
    caption.append(el("span",null,candidate.name),
      el("strong",null,candidate.count+" casts"));
    const track=el("span","insight-featured-bar-track");
    const fill=el("span","insight-featured-bar-fill");
    fill.style.width=Math.max(2,100*candidate.count/maxCount)+"%";
    track.append(fill);button.append(caption,track);
    button.onclick=()=>choose(candidate);
    bars.append(button);buttons.push(button);
  }
  choose(candidates[0]);
}
function renderInsights(records,active){
  const root=$("key-insights-grid");
  if(!root)return;
  root.replaceChildren();root.classList.add("latest-insight-grid");
  const label=$("key-insights-panel")?.querySelector(".key-insights-heading .micro");
  if(label)label.textContent="Choose a card, compare recorded casts and open its example games.";
  hero(root,records,active);
  for(const [title,cards] of cardGroups(records))feature(root,title,cards);
  const empty=$("key-insights-empty");if(empty)empty.hidden=true;
}
function renderOutcomes(records,active,games,key){
  const root=$("game-outcome-results"),status=$("game-outcome-status");
  if(!root)return;
  root.replaceChildren();
  if(status)status.textContent=records.length+" verified Gorge game(s) for "+key;
  const details=el("details","gorge-game-library");
  details.append(el("summary",null,"Game library · "+records.length+
    " verified Gorge game"+(records.length===1?"":"s")));
  const content=el("div","gorge-game-library-body");
  content.append(el("p","small",
    "Real four-player games; verified winners, matchup rates and private hand identities are not yet in the public export."));
  for(const a of records){
    const button=el("button","game-outcome-seed","Seed "+a.game.seed+" · "+
      a.game.decks.map(x=>x.replace(/_/g," ")).join(" / "));
    button.type="button";
    button.onclick=()=>{
      const panel=$("turn-reviewer-panel");
      if(panel)panel.hidden=true;
      render(games,a.game.seed,key);
      const selected=$("key-insights-panel");
      if(selected?.scrollIntoView)selected.scrollIntoView({behavior:"smooth",block:"start"});
    };
    content.append(button);
  }
  details.append(content);root.append(details);
}
function renderDevelopment(records){
  const root=$("bounded-results");
  if(!root)return;
  root.replaceChildren();
  root.append(el("p","small",
    "Gorge source events only; the retired Python simulations do not contribute to these results."));
  for(const a of records)
    root.append(el("p","small","Seed "+a.game.seed+" · "+a.casts+" casts · "+
      a.lands+" land plays · "+a.tokens+" token events"));
}
function render(games,activeSeed,deckKey){
  if(typeof document==="undefined")return;
  games=(games||[]).filter(valid);
  const key=deckKey||window.__deckLabActiveKey||null;
  const root=$("key-insights-grid");
  if(!root)return;
  const snapshot=$("simulation-snapshot");
  if(snapshot)snapshot.hidden=true;
  const reviewer=$("turn-reviewer-panel");
  if(reviewer)reviewer.hidden=true;
  for(const id of ["archive-observation-details","opponent-replay-panel"]){
    const n=$(id);if(n)n.hidden=true;
  }
  const quiet=$("pane-records")?.querySelector(".diagnostic-panel");
  if(quiet)quiet.hidden=true;
  const refresh=$("game-outcome-refresh");if(refresh)refresh.hidden=true;
  if(!games.length){
    root.replaceChildren(el("p","small","Loading verified Gorge simulation games…"));
    return;
  }
  let chosen=games.find(g=>String(g.seed)===String(activeSeed)&&
    (!key||g.decks.includes(key)));
  if(!chosen)chosen=games.find(g=>!key||g.decks.includes(key));
  if(!chosen){
    root.replaceChildren(el("p","small",
      "No verified Gorge games have been published for this deck yet. Choose another simulated deck to explore its results."));
    const status=$("game-outcome-status");
    if(status)status.textContent="No Gorge results for "+key;
    const results=$("game-outcome-results");
    if(results)results.replaceChildren();
    return;
  }
  const seat=key?chosen.decks.indexOf(key):0;
  const selectedKey=chosen.decks[Math.max(0,seat)];
  const records=games.filter(g=>g.decks.includes(selectedKey))
    .map(g=>analyze(g,g.decks.indexOf(selectedKey)));
  const active=records.find(a=>a.game===chosen)||records[0];
  const title=$("key-insights-title");if(title)title.textContent="Key insights";
  renderInsights(records,active);
  renderOutcomes(records,active,games,selectedKey);
  renderDevelopment(records);
}
return {valid,analyze,summary,render,median};
});
