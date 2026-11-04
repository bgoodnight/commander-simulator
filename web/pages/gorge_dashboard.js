/* Gorge-native data adapter for the ORIGINAL Deck Lab results presentation.
 * No fabricated wins, turn-end state, secret draws or held-card durations.
 * All statistics are derived from actual public gorge events/snapshots.
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
  if(text!==undefined)n.textContent=String(text);
  return n;
};
function valid(g){
  return !!g&&g.schema==="gorge-ui-replay-v1"&&g.engine==="gorge"&&
    g.visibility==="public_events_only"&&Array.isArray(g.turns)&&
    Array.isArray(g.snapshots)&&g.decks?.length===4;
}
function analyze(g){
  if(!valid(g))throw Error("Expected sanitized gorge Commander replay");
  const turns=g.turns.filter(t=>t.turn>0);
  const casts=new Map(),bySeat=Array.from({length:4},()=>({
    casts:0,lands:0,damageEvents:0,tokens:0,turns:0
  }));
  const timeline=[];
  for(const turn of turns){
    const seat=turn.seat,seatData=bySeat[seat];
    if(!seatData)continue;
    seatData.turns++;
    const actions=[];
    for(const event of turn.events||[]){
      // Casts may occur on another player's turn. Native player is the
      // authoritative actor when present (gorge omits seat 0's zero value).
      const actor=Number.isInteger(event.player)?event.player:seat;
      const actorData=bySeat[actor]||seatData;
      if(event.kind==="cast"){
        actorData.casts++;
        if(event.card_name){
          const key=actor+"|"+event.card_name;
          const card=casts.get(key)||{name:event.card_name,seat:actor,played:0,turns:[]};
          card.played++;card.turns.push(turn.turn);casts.set(key,card);
          actions.push("Cast "+event.card_name);
        }else actions.push("Cast spell (unidentified)");
      }else if(event.kind==="land_played"){
        actorData.lands++;actions.push("Played land");
      }else if(event.kind==="token_created"){
        actorData.tokens++;actions.push("Created token");
      }else if(event.kind==="damage")actorData.damageEvents++;
    }
    timeline.push({turn:turn.turn,seat,actions,
      state:g.snapshots.find(s=>s.turn===turn.turn)||null});
  }
  return {seed:g.seed,decks:g.decks,turns:turns.length,
    snapshots:g.snapshots.length,bySeat,
    casts:[...casts.values()].sort((a,b)=>b.played-a.played||a.name.localeCompare(b.name)),
    timeline,
    winner:null, // Public snapshots are not a verified winner record.
    sourceEvents:g.source?.total_native_events||0};
}
function summary(games){
  const analyses=games.map(analyze);
  const deckStats=new Map();
  for(const a of analyses){
    a.decks.forEach((name,seat)=>{
      const x=deckStats.get(name)||{name,games:0,casts:0,lands:0,tokens:0,turns:0};
      x.games++;x.casts+=a.bySeat[seat].casts;
      x.lands+=a.bySeat[seat].lands;x.tokens+=a.bySeat[seat].tokens;
      x.turns+=a.bySeat[seat].turns;deckStats.set(name,x);
    });
  }
  return {analyses,decks:[...deckStats.values()]};
}
function metric(label,value,detail){
  const card=el("div","simulation-snapshot-metric");
  card.append(el("span","eyebrow",label),el("strong",null,value));
  if(detail)card.append(el("span","micro",detail));
  return card;
}
function panel(parent,title,subtitle,klass){
  const p=el("section","panel "+(klass||""));
  const h=el("div","key-insights-heading");
  const intro=el("div");
  intro.append(el("span","eyebrow","Gorge · recorded evidence"),el("h2",null,title));
  h.append(intro,el("span","micro",subtitle));p.append(h);parent.append(p);return p;
}
function render(games,activeSeed){
  const root=$("gorge-dashboard");
  if(!root)return;
  root.replaceChildren();
  if(!games.length){root.append(el("p","small","No verified gorge games loaded."));return;}
  const all=summary(games);
  const game=games.find(g=>String(g.seed)===String(activeSeed))||games[0];
  const a=analyze(game);
  const header=el("section","simulation-snapshot");
  const heading=el("div","simulation-snapshot-heading");
  heading.append(el("span","eyebrow","Simulation at a glance"),
    el("span","micro","Gorge · "+games.length+" verified four-player games"));
  header.append(heading);
  const metrics=el("div","simulation-snapshot-metrics");
  metrics.append(metric("Recorded games",games.length,"40-life Commander"),
    metric("Turn segments",a.turns,"Selected seed "+a.seed),
    metric("State snapshots",a.snapshots,"Turn-entry, not turn-end"),
    metric("Native events",a.sourceEvents.toLocaleString(),"Selected game"));
  header.append(metrics);root.append(header);
  const insight=panel(root,"Key insights",
    "Measured directly from gorge events · no inferred card-held times","key-insights-panel");
  const board=el("div","board-grid");
  const leader=a.casts[0];
  const tiles=[
    ["Most cast card",leader?leader.name:"Not recorded",
      leader?leader.played+" cast events in selected game":"No named casts"],
    ["Land plays",a.bySeat.reduce((n,x)=>n+x.lands,0),
      "All four players · selected game"],
    ["Tokens created",a.bySeat.reduce((n,x)=>n+x.tokens,0),
      "Public token events · selected game"],
    ["Card time in hand","Unavailable",
      "Requires private seat-authorized hand history"]
  ];
  for(const [label,value,desc] of tiles){
    const tile=el("article","panel insight-card");
    tile.append(el("span","eyebrow",label),el("h3",null,value),el("p","micro",desc));
    board.append(tile);
  }
  insight.append(board);
  const outcomes=panel(root,"Latest simulated results",
    "Actual gorge opponents, not abstract Python pressure","game-outcome-panel");
  const status=el("p","small",games.length+" verified gorge games · "+all.decks.length+
    " unique decks. Win rates are withheld until the export includes a verified winner.");
  outcomes.append(status);
  const results=el("div","gorge-deck-grid");
  for(const d of all.decks){
    const card=el("div","panel gorge-deck-result");
    card.append(el("strong",null,d.name),el("span","micro",d.games+" game(s) · "+
      d.casts+" named/unnamed casts · "+d.lands+" land plays · "+d.tokens+" tokens"));
    results.append(card);
  }
  outcomes.append(results);
  const review=panel(root,"Turn reviewer",
    "Chronological public actions from the selected gorge game","latest-turn-reviewer");
  const select=el("select","gorge-turn-select");
  select.setAttribute("aria-label","Select gorge turn");
  for(const t of a.timeline){
    const o=el("option",null,"Turn "+t.turn+" · "+a.decks[t.seat]);
    o.value=String(t.turn);select.append(o);
  }
  review.append(select);
  const turnDetail=el("div","gorge-turn-detail");
  review.append(turnDetail);
  function showTurn(){
    const t=a.timeline.find(x=>String(x.turn)===select.value)||a.timeline[0];
    turnDetail.replaceChildren();
    if(!t)return;
    turnDetail.append(el("h3",null,"Turn "+t.turn+" · "+a.decks[t.seat]));
    turnDetail.append(el("p","small",t.actions.length?
      t.actions.join(" · "):"No public cast, land-play or token events recorded."));
    if(t.state){
      const row=el("div","gorge-deck-grid");
      for(const p of t.state.players){
        const card=el("div","panel gorge-deck-result");
        card.append(el("strong",null,a.decks[p.seat]),
          el("span","micro","Life "+p.life+" · Hand "+p.hand_count+
            " · Library "+p.library_count),
          el("span","micro","Battlefield "+(p.zones?.battlefield?.length||0)+
            " · Graveyard "+(p.zones?.graveyard?.length||0)+
            " · Exile "+(p.zones?.exile?.length||0)));
        row.append(card);
      }
      turnDetail.append(row);
      turnDetail.append(el("p","micro","Authoritative state at first pending decision of turn; not turn-end."));
    }
  }
  select.addEventListener("change",showTurn);showTurn();
  const development=el("details","panel result-takeaway");
  const dh=el("summary","result-takeaway-summary");
  dh.append(el("span","eyebrow","Further analysis"),
    el("h2","result-takeaway-heading","Development & consistency"),
    el("span","result-takeaway-description","Observed casts and land plays by deck"));
  development.append(dh);
  const inner=el("div","gorge-development");
  for(const d of all.decks){
    const p=el("p","small",d.name+" · "+d.games+" games · "+
      d.casts+" casts · "+d.lands+" land plays");
    inner.append(p);
  }
  inner.append(el("p","micro","Opening-hand composition, turns held, end-turn mana, win rates and matchup analysis are not inferred from incomplete exports."));
  development.append(inner);root.append(development);
}
return {valid,analyze,summary,render};
});
