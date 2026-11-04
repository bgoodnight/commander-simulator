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

/* Keep the original Deck Lab's parchment/teal/gold card vocabulary.
   Only gorge data changes; the presentation uses the long-standing CSS
   classes board-report, board-summary, game-outcome-turn-strip, etc. */
function displayDeckName(name){
  const labels={
    mortarion_current:"Mortarion · Current",
    magnus_premium:"Magnus · Premium",
    necron_dynasties:"Necron Dynasties",
    wretched_ranks:"Wretched Ranks",
    "avengers-assemble":"Avengers Assemble",
    "cavalry-charge":"Cavalry Charge",
    "deadly-disguise":"Deadly Disguise",
    "science-pip":"Science!"
  };
  return labels[name]||String(name||"").replaceAll(/[_-]/g," ").replace(/\\b\\w/g,c=>c.toUpperCase());
}
function cardArt(name){
  if(!name||typeof name!=="string")return null;
  return "https://api.scryfall.com/cards/named?exact="+encodeURIComponent(name)+"&format=image&version=art_crop";
}
function cardLink(name){
  return "https://scryfall.com/search?q="+encodeURIComponent('!"'+name+'"');
}
function cardImage(name,klass){
  if(!name)return null;
  const im=el("img",klass||"board-cover");
  im.src=cardArt(name); im.alt="";
  im.loading="lazy"; im.decoding="async";
  im.addEventListener("error",()=>im.remove(),{once:true});
  return im;
}
function artBoard(item){
  const report=el("details","board-report");
  const cover=el("summary","board-summary");
  const copy=el("span","board-summary-copy");
  copy.append(el("span","board-kicker",item.kicker));
  copy.append(el("strong",null,item.value));
  copy.append(el("span","board-description",item.description));
  copy.append(el("span","board-open","Explore recorded evidence"));
  cover.append(copy);
  const art=cardImage(item.art);
  if(art)cover.append(art);
  report.append(cover);
  const body=el("div","board-body");
  body.append(el("h3",null,item.title),el("p","small",item.evidence));
  if(item.list?.length){
    const list=el("div","board-card-list");
    for(const entry of item.list.slice(0,18)){
      const a=el("a","board-card-row",entry.name+" · "+entry.count);
      a.href=cardLink(entry.name);a.target="_blank";a.rel="noopener noreferrer";
      list.append(a);
    }
    body.append(list);
  }
  report.append(body);
  return report;
}
function sectionHeading(eyebrow,title,subtitle){
  const row=el("div","key-insights-heading");
  const label=el("div");
  label.append(el("span","eyebrow",eyebrow),el("h2",null,title));
  row.append(label,el("span","micro",subtitle));
  return row;
}
function playerZone(label,items){
  const details=el("details","game-outcome-observed-zone");
  details.append(el("summary",null,label+" · "+items.length));
  const list=el("div","game-outcome-observed-cards");
  if(!items.length)list.append(el("span","micro","Empty"));
  for(const item of items){
    const link=el("a","game-outcome-recorded-card",item.name);
    link.href=cardLink(item.name);link.target="_blank";link.rel="noopener noreferrer";
    list.append(link);
  }
  details.append(list);return details;
}
function turnSummary(turn,game){
  const events=(game.turns.find(x=>x.turn===turn.turn)?.events||[]);
  const actions=events.filter(e=>["cast","land_played","token_created"].includes(e.kind))
    .map(e=>e.kind==="cast"?"Cast "+(e.card_name||"a spell"):
      e.kind==="land_played"?"Played a land":"Created a token");
  return actions.length?actions.slice(0,5).join(" · "):"No named card plays recorded";
}
function render(games,activeSeed){
  const root=$("gorge-dashboard");if(!root)return;
  root.replaceChildren();
  const verified=games.filter(valid);
  if(!verified.length){
    root.append(el("p","small","Choose a verified gorge game to inspect recorded play."));
    return;
  }
  const all=summary(verified);
  const game=verified.find(x=>String(x.seed)===String(activeSeed))||verified[0];
  const model=analyze(game);
  const header=el("div","gorge-original-header");
  const headline=el("div");
  headline.append(el("span","eyebrow","Commander · recorded four-player games"),
    el("h1",null,"Simulation Results"),
    el("p","small","Real gorge gameplay, presented in the original Deck Lab."));
  header.append(headline);
  if(verified.length>1){
    const picker=el("label","gorge-original-picker");
    picker.append(el("span","micro","View recorded game"));
    const select=el("select",null);
    for(const recorded of verified){
      const option=el("option",null,"Game "+recorded.seed+" · "+displayDeckName(recorded.decks[0]));
      option.value=String(recorded.seed);
      select.append(option);
    }
    select.value=String(game.seed);
    select.addEventListener("change",()=>{
      const source=$("gorge-replay-sample-select"),load=$("gorge-replay-load");
      if(source&&load){
        source.value="gorge-seed-"+select.value+".ui.json";
        load.click();
      }else render(verified,select.value);
    });
    picker.append(select);header.append(picker);
  }
  root.append(header);

  const insights=el("section","panel key-insights-panel");
  insights.append(sectionHeading("Simulation takeaways","Key insights",
    "Select a card to inspect evidence from the recorded game"));
  const grid=el("div","board-grid");
  const counts=[...model.casts].sort((a,b)=>b.played-a.played);
  const top=counts[0];
  const first=model.timeline.flatMap(t=>game.turns.find(x=>x.turn===t.turn)?.events||[])
    .find(e=>e.kind==="cast"&&e.card_name);
  const leadSeat=model.bySeat.map((d,seat)=>({seat,casts:d.casts}))
    .sort((a,b)=>b.casts-a.casts||a.seat-b.seat)[0];
  const data=[
    {kicker:"Most frequently cast",value:top?top.name:"Unrecorded",
      description:top?top.played+" observed casts":"No identified spells",
      title:"Most commonly played card",art:top?.name,
      evidence:"Actual spell casts recorded by gorge in this game, including spells on opponents' turns.",
      list:counts.map(c=>({name:c.name,count:c.played+" casts"}))},
    {kicker:"First spell",value:first?.card_name||"Unrecorded",
      description:first?"First named cast in recorded play":"No named cast available",
      title:"How the game developed",art:first?.card_name,
      evidence:"The first public spell-cast event in source order. Opening hands are intentionally not inferred.",
      list:counts.slice(0,10).map(c=>({name:c.name,count:c.played+" casts"}))},
    {kicker:"Most active caster",value:displayDeckName(game.decks[leadSeat.seat]),
      description:leadSeat.casts+" spells cast in this game",
      title:"Casting activity by deck",
      art:(game.snapshots[0]?.players[leadSeat.seat]?.zones?.command||[])[0]?.name,
      evidence:game.decks.map((name,seat)=>displayDeckName(name)+" — "+model.bySeat[seat].casts+" public spell casts").join(" · ")}
  ];
  for(const item of data)grid.append(artBoard(item));
  insights.append(grid);root.append(insights);

  const outcomes=el("section","game-outcome-panel panel");
  const title=el("div","game-outcome-heading");
  const intro=el("div");
  intro.append(el("span","eyebrow","Four-player Commander"),
    el("h2",null,"Latest simulated results"),
    el("p","micro","Choose a deck or a turn below to explore this genuine game."));
  title.append(intro);outcomes.append(title);
  const entries=el("div","gorge-original-decks");
  game.decks.forEach((name,seat)=>{
    const block=el("article","game-outcome-life-stat");
    const commander=game.snapshots[0]?.players[seat]?.zones?.command?.[0]?.name;
    const image=cardImage(commander,"gorge-original-commander-art");
    if(image)block.append(image);
    const copy=el("div","gorge-original-deck-copy");
    copy.append(el("span","micro","Seat "+(seat+1)),
      el("strong",null,displayDeckName(name)),
      el("small",null,model.bySeat[seat].casts+" observed casts"));
    block.append(copy);entries.append(block);
  });
  outcomes.append(entries);
  outcomes.append(el("p","micro",
    "This small preview shows verified gameplay. Win rates and final outcomes remain unavailable until exported explicitly by gorge."));
  root.append(outcomes);

  const reviewer=el("section","latest-turn-reviewer");
  reviewer.append(el("h2",null,"Turn reviewer"));
  const explanation=el("p","micro",
    "Select a turn to inspect recorded actions and the authoritative state at turn entry.");
  reviewer.append(explanation);
  const strip=el("div","game-outcome-turn-strip");
  const detail=el("div","game-outcome-round-detail gorge-original-turn-detail");
  let activeTurn=null;
  function showTurn(t){
    activeTurn=t.turn;
    for(const button of strip.children)
      button.setAttribute("aria-pressed",String(button.dataset.turn===String(activeTurn)));
    detail.replaceChildren();
    const head=el("div","game-outcome-evidence-head");
    head.append(el("strong",null,"Turn "+t.turn+" · "+displayDeckName(game.decks[t.seat])));
    detail.append(head);
    const events=game.turns.find(x=>x.turn===t.turn)?.events||[];
    const important=events.filter(e=>["cast","land_played","token_created","damage","player_lost"].includes(e.kind));
    const play=el("p","small");
    play.textContent=important.length?important.map(e=>
      e.kind==="cast"?"Cast "+(e.card_name||"spell"):
      e.kind==="land_played"?"Played land":
      e.kind==="token_created"?"Created token":
      e.kind==="damage"?"Damage "+(e.amount??""):
      "Player eliminated").slice(0,25).join(" · "):"No public plays in this segment";
    detail.append(play);
    if(t.state){
      const states=el("div","game-outcome-life-stats");
      for(const p of t.state.players){
        const state=el("div","game-outcome-life-stat");
        state.append(el("span",null,displayDeckName(game.decks[p.seat])),
          el("strong",null,String(p.life)),
          el("small",null,p.hand_count+" in hand · "+p.library_count+" in library"));
        states.append(state);
      }
      detail.append(states);
      const observed=el("div","game-outcome-observed-zones");
      for(const p of t.state.players){
        const player=el("details","game-outcome-observed-zone");
        player.append(el("summary",null,game.decks[p.seat]+" · battlefield and zones"));
        const areas=el("div","gorge-original-zone-list");
        for(const zone of ["battlefield","graveyard","exile","command"])
          areas.append(playerZone(zone,p.zones?.[zone]||[]));
        player.append(areas);observed.append(player);
      }
      detail.append(observed);
      detail.append(el("p","micro","Gorge state captured at the first pending decision of this turn, not the end of the previous turn."));
    }
  }
  for(const t of model.timeline){
    const btn=el("button","game-outcome-turn-tile");
    btn.type="button";
    btn.dataset.turn=String(t.turn);
    btn.setAttribute("aria-pressed","false");
    const artName=game.turns.find(x=>x.turn===t.turn)?.events
      ?.find(e=>e.kind==="cast"&&e.card_name)?.card_name;
    const image=cardImage(artName,"game-outcome-turn-art");
    if(image)btn.append(image);
    btn.append(el("span","game-outcome-turn-number",
      "Turn "+t.turn+" · "+game.decks[t.seat]),
      el("span","game-outcome-turn-highlight",turnSummary(t,game)));
    const life=t.state?.players?.[t.seat]?.life;
    btn.append(el("span","game-outcome-turn-life",
      life===undefined?"Recorded actions":"Life "+life+" at turn entry"));
    btn.addEventListener("click",()=>showTurn(t));
    strip.append(btn);
  }
  reviewer.append(strip,detail);root.append(reviewer);
  if(model.timeline.length)showTurn(model.timeline[0]);

  const development=el("details","panel result-takeaway result-takeaway-development");
  const dh=el("summary","result-takeaway-summary");
  dh.append(el("span","eyebrow","Further analysis"),
    el("h2","result-takeaway-heading","Development & consistency"),
    el("span","result-takeaway-description","Recorded spell casts and land plays"));
  development.append(dh);
  const body=el("div","gorge-original-development");
  const comparison=el("div","board-card-list");
  for(const d of all.decks){
    comparison.append(el("div","board-card-row",
      displayDeckName(d.name)+" · "+d.games+" games · "+d.casts+" casts · "+d.lands+" land plays"));
  }
  body.append(comparison,el("p","micro",
    "Turn-end state, draw identities, win rates, and cards held cannot yet be calculated reliably from public snapshots."));
  development.append(body);root.append(development);
}
return {valid,analyze,summary,render};
});
