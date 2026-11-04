/* Gorge Deck Lab dashboard adapter
 *
 * Uses the SAME original Results markup and CSS classes, not a replacement
 * design. Reads only sanitized gorge-ui-replay-v1 records. Never conflates
 * pre-gorge Python simulations with full 40-life Commander games.
 *
 * Source fidelity: cast events are attributed to the original owner using
 * gorge's pinned 100-card-per-seat object ID partition. This is card
 * ownership, not a claim of who controlled/cast a stolen spell. Hand *names*
 * and full end-of-turn states cannot be inferred from these public samples.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.GorgeDashboard=api;
})(typeof window!=="undefined"?window:globalThis,function(){
"use strict";
const SCHEMA="gorge-ui-replay-v1";
const BASIC=new Set(["plains","island","swamp","mountain","forest","wastes",
  "snow-covered plains","snow-covered island","snow-covered swamp",
  "snow-covered mountain","snow-covered forest"]);
const COLORS=["#d5b879","#75bdb4","#ba9acf","#d98679"];
const ALLOWED_ZONES=["battlefield","graveyard","exile","command"];
const $=id=>document.getElementById(id);
const el=(tag,cls,text)=>{
  const x=document.createElement(tag);
  if(cls)x.className=cls;
  if(text!==undefined&&text!==null)x.textContent=String(text);
  return x;
};
const text= (n)=>Number.isFinite(n)?String(Math.round(n*10)/10):"—";
function validate(g){
  if(!g||g.schema!==SCHEMA||g.engine!=="gorge"||
     g.visibility!=="public_events_only"||
     !Number.isInteger(g.seed)||!Array.isArray(g.decks)||
     g.decks.length!==4||!Array.isArray(g.turns)||
     !Array.isArray(g.snapshots)||g.snapshots.length<1||
     g.snapshot_definition!=="first_pending_decision_of_turn")
    throw Error("Not an authoritative public gorge replay");
  const end=g.turns.at(-1)?.events?.filter(e=>e.kind==="game_over").at(-1);
  if(!end||!Number.isInteger(end.player)||end.player<0||end.player>3||
     end.text!==g.decks[end.player])
    throw Error("Gorge replay has no unambiguous winner");
  if(g.snapshots.some(s=>s.boundary!=="first_pending_decision_of_turn"||
       !Array.isArray(s.players)||s.players.length!==4||
       s.players.some((p,i)=>p.seat!==i||
         !Number.isFinite(p.life)||!Number.isInteger(p.hand_count)||
         !Number.isInteger(p.library_count)||
         !Array.isArray(p.mana_pool)||p.mana_pool.length!==6||
         !p.zones||Object.keys(p.zones).sort().join("|")!==
           [...ALLOWED_ZONES].sort().join("|"))))
    throw Error("Invalid or private gorge physical-state snapshot");
  if(g.snapshots[0].players.some(p=>p.life!==40))
    throw Error("Not a 40-life Commander game");
  return g;
}
function winner(g){
  validate(g);
  return g.turns.at(-1).events.filter(e=>e.kind==="game_over").at(-1).player;
}
function seatForObject(obj){
  return Number.isInteger(obj)&&obj>=1&&obj<=400?
    Math.floor((obj-1)/100):null;
}
function catalog(cards){
  const lookup=new Map();
  for(const c of Object.values(cards||{})){
    if(typeof c?.name==="string"){
      lookup.set(c.name.toLowerCase(),c);
      for(const face of c.face_names||[])
        lookup.set(face.toLowerCase(),c);
    }
  }
  return name=>lookup.get(String(name||"").toLowerCase())||null;
}
function seenGames(games,key){
  return games.filter(g=>g.decks.includes(key));
}
function getPlayer(g,key){
  const seat=g.decks.indexOf(key);
  return seat>=0?{seat,player:g.snapshots.at(-1).players[seat]}:null;
}
function analyze(games,key){
  const selected=seenGames(games,key).map(g=>validate(g));
  const n=selected.length;
  const finished=selected.filter(g=>winner(g)===g.decks.indexOf(key));
  const wins=finished.length;
  const castMap=new Map(),matchups=new Map();
  let allCasts=0;
  for(const game of selected){
    const seat=game.decks.indexOf(key),win=winner(game)===seat;
    for(const other of game.decks.filter((_,i)=>i!==seat)){
      if(!matchups.has(other))matchups.set(other,{key:other,games:0,wins:0,seeds:[]});
      const rec=matchups.get(other);
      rec.games++;rec.wins+=Number(win);rec.seeds.push(game.seed);
    }
    for(const turn of game.turns){
      for(const e of turn.events||[]){
        // Card ownership is recorded independently of who played the spell.
        if(e.kind!=="cast"||!e.card_name||
           seatForObject(e.obj)!==seat)continue;
        if(e.from!==1&&e.from!==6)continue;
        const name=e.card_name;
        if(!castMap.has(name))castMap.set(name,{
          name,casts:0,games:new Set(),turns:[],examples:[]});
        const rec=castMap.get(name);
        rec.casts++;allCasts++;rec.games.add(game.seed);
        rec.turns.push(turn.turn);
        rec.examples.push({seed:game.seed,turn:turn.turn,eventIndex:e.seq,
          cardName:name,description:"Native gorge cast event #"+e.seq+
            (e.from===6?" · from command zone":" · from hand")});
      }
    }
  }
  const cast=[...castMap.values()].map(r=>({
    ...r,gamesPlayed:r.games.size,firstTurnMedian:median(r.turns),
    examples:[...r.examples].sort((a,b)=>a.seed-b.seed||a.turn-b.turn)
  })).sort((a,b)=>b.gamesPlayed-a.gamesPlayed||b.casts-a.casts||
    a.name.localeCompare(b.name));
  const lastLife=selected.map(g=>getPlayer(g,key).player.life);
  const lastAlive=selected.filter(g=>!getPlayer(g,key).player.lost).length;
  return {key,n,wins,losses:n-wins,winPct:n?100*wins/n:null,
    lastAlive,lastLifeMedian:median(lastLife),cast,allCasts,
    matchups:[...matchups.values()].sort((a,b)=>b.games-a.games||
      a.key.localeCompare(b.key)),games:selected,
    turnsMedian:median(selected.map(g=>g.turns.filter(t=>t.turn>0).length)),
    snapshotNote:"Every state is at the first pending decision of a turn, NOT end-of-turn."};
}
function median(vals){
  if(!vals.length)return null;
  const a=[...vals].filter(Number.isFinite).sort((x,y)=>x-y);
  if(!a.length)return null;
  return a.length%2?a[(a.length-1)/2]:(a[a.length/2-1]+a[a.length/2])/2;
}
function castModel(stats,kind,lookup){
  const filter=r=>{
    const c=lookup(r.name);
    if(BASIC.has(r.name.toLowerCase()))return false;
    if(kind==="all")return true;
    if(kind==="creature")return /\bCreature\b/i.test(c?.type_line||"");
    return c?.category===kind;
  };
  const rows=stats.cast.filter(filter);
  if(!rows.length)return null;
  const labels={all:"Most cast card",creature:"Most cast creature",
    Artifact:"Most cast artifact",Enchantment:"Most cast enchantment",
    Instant:"Most cast instant",Sorcery:"Most cast sorcery"};
  const contenders=rows.map(r=>({
    name:r.name,card:lookup(r.name),score:r.gamesPlayed,
    scoreLabel:r.gamesPlayed+" / "+stats.n+" games",
    viewScores:{games:r.gamesPlayed,casts:r.casts},
    viewLabels:{games:r.gamesPlayed+" games",casts:r.casts+" casts"},
    metrics:[
      {id:"games",label:"Games cast",value:r.gamesPlayed+" / "+stats.n,
        explanation:"Distinct gorge games with a cast of this owned card. "+
          "This does not infer hidden draws or uncast copies.",
        examples:r.examples},
      {id:"casts",label:"Total casts",value:String(r.casts),
        explanation:"Recorded native cast events of this owned card; "+
          "a copied spell is not automatically counted as a new cast.",
        examples:r.examples},
      {id:"turn",label:"Median turn cast",
        value:r.firstTurnMedian===null?"—":text(r.firstTurnMedian),
        explanation:"Median GLOBAL turn index for the observed casts, "+
          "not rounds held in hand.",examples:r.examples}
    ]
  })).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
  return {
    id:"gorge-"+kind,kind:"cast",title:labels[kind]||"Most cast card",
    value:contenders[0].score+" / "+stats.n+" games",
    chartLabel:"Games with an owned-card cast",
    explanation:"Real four-player gorge Commander games ("+stats.n+
      " observations). Only source-verified card casts are counted. "+
      "No hidden hand appearances or implied land plays are included.",
    headlineDetail:"Source-backed casts · "+stats.n+" gorge game"+(stats.n===1?"":"s"),
    total:stats.n,contenders,
    views:[
      {id:"games",label:"Games cast",chartLabel:"Games with card cast"},
      {id:"casts",label:"Times cast",chartLabel:"Recorded casts"}
    ]
  };
}
function lifeRows(game){
  validate(game);
  return game.snapshots.map(s=>({
    turn:s.turn,seat:s.active_seat,
    life:s.players.map(p=>p.life),lost:s.players.map(p=>p.lost),
    hands:s.players.map(p=>p.hand_count),
    library:s.players.map(p=>p.library_count),
    battlefield:s.players.map(p=>p.zones.battlefield.length)
  }));
}
function lifeChart(game,lookup){
  const rows=lifeRows(game);
  const W=680,H=230,L=36,R=12,T=18,B=32,maxX=rows.at(-1).turn;
  const maxLife=Math.max(40,...rows.flatMap(r=>r.life),1);
  const ceiling=Math.ceil(maxLife/10)*10,plotW=W-L-R,plotH=H-T-B;
  const x=t=>L+(t-1)/Math.max(1,maxX-1)*plotW;
  const y=l=>T+plotH-Math.max(0,l)/ceiling*plotH;
  const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("viewBox","0 0 680 230");svg.setAttribute("role","img");
  svg.setAttribute("aria-label","Four-player life at authoritative gorge turn-entry checkpoints");
  const append=(tag,attrs,body)=>{
    const a=document.createElementNS("http://www.w3.org/2000/svg",tag);
    Object.entries(attrs||{}).forEach(([k,v])=>a.setAttribute(k,String(v)));
    if(body!==undefined)a.textContent=String(body);
    svg.append(a);return a;
  };
  for(const f of [0,.25,.5,.75,1]){
    const val=Math.round(f*ceiling);
    append("line",{x1:L,y1:y(val),x2:W-R,y2:y(val),stroke:"#5f6d68",
      "stroke-opacity":.35});
    append("text",{x:5,y:y(val)+4,fill:"#c4cbbd","font-size":11},val);
  }
  for(let seat=0;seat<4;seat++){
    append("polyline",{
      points:rows.map(r=>x(r.turn)+","+y(r.life[seat])).join(" "),
      fill:"none",stroke:COLORS[seat],"stroke-width":2.4,
      "stroke-linejoin":"round","stroke-linecap":"round"
    });
  }
  for(const turn of [1,Math.ceil(maxX/2),maxX])
    append("text",{x:x(turn),y:H-8,"text-anchor":"middle",
      fill:"#c4cbbd","font-size":11},"T"+turn);
  return svg;
}
function outcomeCard(title,kicker,number,detail,bodyFn){
  const panel=el("details","board-report game-outcome-card");
  const summary=el("summary","game-outcome-summary");
  const copy=el("div","game-outcome-summary-copy");
  copy.append(el("span","board-kicker",kicker),
    el("strong","game-outcome-title",title),
    el("span","game-outcome-number",number),
    el("span","game-outcome-caption",detail),
    el("span","board-open","Explore →"));
  summary.append(copy);panel.append(summary);
  const body=el("div","game-outcome-body");
  bodyFn(body);panel.append(body);
  return panel;
}
function metric(name,value,description){
  const node=el("div","game-outcome-insight-metric");
  node.append(el("span",null,name),el("strong",null,value),
    el("small",null,description));
  return node;
}
function storyCard(title,kicker,value,caption,onOpen){
  const button=el("button","game-outcome-hero-highlight");
  button.type="button";
  button.append(el("span",null,title),el("strong",null,value),
    el("small",null,caption),el("span","game-outcome-hero-highlight-cue","Explore ↗"));
  button.onclick=onOpen;
  return button;
}
function unavailable(title,message){
  const panel=el("details","board-report insight-report");
  const summary=el("summary","board-summary insight-summary");
  const copy=el("span","board-summary-copy");
  copy.append(el("span","board-kicker","Gorge data coverage"),
    el("strong","insight-head-title",title),
    el("span","insight-head-stat","Not yet recorded"),
    el("span","board-open","Why? →"));
  summary.append(copy);panel.append(summary);
  const body=el("div","board-body insight-body");
  body.append(el("p","small",message));panel.append(body);
  return panel;
}
let state={games:[],catalog:null,deck:null,requestedDeck:null,selectedSeed:null,loading:null};
function currentDeck(games){
  if(state.deck&&games.some(g=>g.decks.includes(state.deck)))return state.deck;
  const key=typeof window!=="undefined"&&typeof window.GORGE_SELECTED_DECK==="string"?
    window.GORGE_SELECTED_DECK:null;
  if(key&&games.some(g=>g.decks.includes(key)))return key;
  return games[0]?.decks[0]||null;
}
function paint(){
  if(typeof document==="undefined"||!state.games.length)return;
  const deck=currentDeck(state.games);
  if(!deck)return;
  state.deck=deck;
  const sample=$("simulation-snapshot");
  const heading=sample?.querySelector(".simulation-snapshot-heading");
  if(heading){
    let wrapper=$("gorge-recorded-deck-picker");
    if(!wrapper){
      wrapper=el("label","gorge-recorded-deck-picker");
      wrapper.id="gorge-recorded-deck-picker";
      wrapper.append(el("span","micro","Recorded deck"));
      const picker=el("select","game-outcome-scenario-select gorge-recorded-deck-select");
      picker.id="gorge-recorded-deck-select";
      picker.setAttribute("aria-label","Choose a deck from verified gorge games");
      wrapper.append(picker);
      heading.append(wrapper);
    }
    const picker=$("gorge-recorded-deck-select");
    const decks=[...new Set(state.games.flatMap(game=>game.decks))];
    if(picker.options.length!==decks.length||
       decks.some((id,i)=>picker.options[i]?.value!==id)){
      picker.replaceChildren();
      for(const id of decks){
        const game=state.games.find(g=>g.decks.includes(id));
        const seat=game.decks.indexOf(id);
        const name=game.snapshots[0].players[seat].zones.command[0]?.name||id;
        const option=el("option",null,name+" · "+id.replaceAll("_"," "));
        option.value=id;picker.append(option);
      }
      picker.onchange=()=>{state.deck=picker.value;paint()};
    }
    picker.value=deck;
  }
  const stats=analyze(state.games,deck);
  const lookup=catalog(state.catalog?.cards||{});
  const sample=$("simulation-snapshot"),metrics=$("simulation-snapshot-metrics");
  if(sample&&metrics){
    sample.hidden=false;
    const scope=$("simulation-snapshot-scope");
    if(scope)scope.textContent=stats.n+" real four-player game"+(stats.n===1?"":"s")+
      " · gorge · 40 life"+(state.requestedDeck&&
      state.requestedDeck!==deck&&!seenGames(state.games,state.requestedDeck).length?
      " · "+state.requestedDeck+" has no gorge samples yet":"");
    metrics.replaceChildren();
    for(const [glyph,value,label] of [
      ["◆",stats.n,"Gorge games · current sample"],
      ["♟",stats.winPct===null?"—":text(stats.winPct)+"%","Observed wins"],
      ["▤",stats.turnsMedian===null?"—":text(stats.turnsMedian),
        "Median global turns played"]
    ]){
      const tile=el("div","simulation-snapshot-stat");
      tile.append(el("span","simulation-snapshot-icon",glyph),
        el("strong",null,value),el("span","simulation-snapshot-name",label));
      metrics.append(tile);
    }
  }
  const status=$("game-outcome-status");
  if(status)status.textContent=stats.n+" gorge Commander game"+(stats.n===1?"":"s")+
    " · eight-deck pool · recorded 40-life source";
  const results=$("game-outcome-results");
  if(results){
    results.replaceChildren();
    const cards=el("div","board-grid game-outcome-grid latest-insight-grid");
    results.append(cards);
    const hero=el("div","game-outcome-hero-frame");
    const wrap=el("details","board-report game-outcome-card game-outcome-hero");
    const summary=el("summary","game-outcome-summary game-outcome-hero-summary");
    const chosen=stats.games[0],i=chosen.decks.indexOf(deck);
    const commander=chosen.snapshots[0].players[i].zones.command[0]?.name||deck;
    const commanderCard=lookup(commander);
    const art=commanderCard?.art;
    if(art){const img=el("img","game-outcome-hero-art");img.src=art;img.alt="";
      img.loading="lazy";summary.append(img);}
    const copy=el("div","game-outcome-hero-copy");
    copy.append(el("strong","game-outcome-title","Game Outcomes"));
    const values=el("div","game-outcome-hero-stats");
    for(const [statusValue,label,count] of [
      ["win","Wins",stats.wins],["loss","Losses",stats.losses],
      ["unresolved","Unresolved",0]]){
      const item=el("div","game-outcome-hero-stat is-"+statusValue);
      item.append(el("strong",null,text(100*count/stats.n)+"%"),
        el("span",null,label+" · "+count+"/"+stats.n));
      values.append(item);
    }
    copy.append(values);
    const bar=el("div","game-outcome-stacked-bar");
    bar.setAttribute("role","img");
    bar.setAttribute("aria-label",stats.wins+" wins, "+stats.losses+
      " losses from "+stats.n+" gorge games");
    for(const [key,count] of [["win",stats.wins],["loss",stats.losses]]){
      if(!count)continue;
      const segment=el("span","is-"+key);
      segment.style.width=(100*count/stats.n)+"%";
      bar.append(segment);
    }
    copy.append(bar);
    const highlights=el("div","game-outcome-hero-highlights");
    const disclosures=new Map();
    for(const [key,label,value,caption] of [
      ["matchup","Best matchup",stats.matchups.length?
         text(100*Math.max(...stats.matchups.map(m=>m.wins/m.games)))+"%":"—",
        "Opponent deck present in pod"],
      ["length","Game length",text(stats.turnsMedian),
        "Median completed table turns"],
      ["survival","Survival",text(100*stats.lastAlive/stats.n)+"%",
        "Alive at last turn-entry checkpoint"],
      ["life","Last life",text(stats.lastLifeMedian),
        "Median at last turn-entry checkpoint"]]){
      highlights.append(storyCard(label,"Gorge",value,caption,()=>{
        const target=disclosures.get(key);
        if(target){target.open=true;target.scrollIntoView({behavior:"smooth",block:"nearest"});}
      }));
    }
    copy.append(highlights,el("span","game-outcome-hero-meta",
      stats.n+" source games · Seeds "+stats.games.map(g=>g.seed).join(", ")));
    summary.append(copy);
    const body=el("div","game-outcome-body");
    body.append(el("p","micro","Real gorge 40-life Commander games. "+
      "Two examples are insufficient for deck power rankings. "+
      "Each result identifies a true winning seat in a four-player pod."));
    for(const game of stats.games){
      const seat=game.decks.indexOf(deck);
      const won=winner(game)===seat;
      const row=el("div","game-outcome-bucket is-"+(won?"win":"loss"));
      row.append(el("strong",null,"Seed "+game.seed+" · "+(won?"Win":"Loss")),
        el("span",null,"Winner: "+game.decks[winner(game)]+
          " · "+(game.snapshots.at(-1).turn)+
          " observed turn-entry checkpoints"));
      const btn=el("button","stone-button","Inspect source replay");
      btn.type="button";btn.onclick=()=>selectGame(game.seed,true);
      row.append(btn);body.append(row);
    }
    wrap.append(summary,body);hero.append(wrap);cards.append(hero);
    const opponent=outcomeCard("Opponent Matchups","Real deck opponents",
      stats.matchups.length+" decks","Recorded pod participation",body=>{
        body.append(el("p","micro","Win share when each named opposing deck was "+
          "present in the four-player pod; NOT a head-to-head result."));
        for(const r of stats.matchups){
          const tile=metric(r.key,r.wins+"/"+r.games+" wins",
            "Across seeds "+r.seeds.join(", "));
          body.append(tile);
        }
      });
    const gameLength=outcomeCard("Game Length","Completed Commander games",
      text(stats.turnsMedian)+" turns",
      "Full table turns · no simplified six-turn horizon",body=>{
        for(const g of stats.games)
          body.append(metric("Seed "+g.seed,g.turns.filter(t=>t.turn>0).length+
            " turns","Recorded four-player game length"));
      });
    const life=outcomeCard("Life Progression","Authoritative physical states",
      "40 life","Per-seat life at turn-entry checkpoints",body=>{
        const chooser=el("select","game-outcome-scenario-select");
        chooser.setAttribute("aria-label","Choose gorge game life progression");
        for(const g of stats.games){
          const opt=el("option",null,"Seed "+g.seed);
          opt.value=String(g.seed);chooser.append(opt);
        }
        body.append(chooser);
        const graph=el("div","game-outcome-life-chart"),legend=el("div","game-outcome-legend");
        const last=el("div","game-outcome-round-detail");
        const render=()=>{
          const g=stats.games.find(g=>String(g.seed)===chooser.value)||stats.games[0];
          graph.replaceChildren(lifeChart(g,lookup));
          legend.replaceChildren();
          g.decks.forEach((name,seat)=>{
            const chip=el("span",null,name);
            chip.style.borderColor=COLORS[seat];legend.append(chip);
          });
          last.replaceChildren(el("p","micro",
            "Last authoritative state: turn "+g.snapshots.at(-1).turn+
            " · "+g.snapshots.at(-1).players.map((p,i)=>
              g.decks[i]+": "+p.life+" life").join(" · ")));
        };
        chooser.addEventListener("change",render);render();
        body.append(legend,graph,last);
      });
    cards.append(opponent,gameLength,life);
  }
  const insights=$("key-insights-grid");
  if(insights){
    insights.replaceChildren();
    const models=["all","creature","Artifact","Enchantment","Instant","Sorcery"]
      .map(type=>castModel(stats,type,lookup)).filter(Boolean);
    for(const model of models){
      const panel=window.DeckInsightExplorer?.render(model,{
        onOpenCard:id=>{
          const c=Object.values(state.catalog?.cards||{}).find(c=>c.oracle_id===id);
          if(c?.scryfall)window.open(c.scryfall,"_blank","noopener,noreferrer");
        },
        onRenderEvidence:(container,example)=>{
          const game=stats.games.find(g=>g.seed===example.seed);
          const turn=game?.turns.find(t=>t.turn===example.turn);
          if(!turn){container.textContent="Source turn unavailable";return;}
          const focus=turn.events.find(e=>e.seq===example.eventIndex);
          container.append(el("strong",null,"Gorge seed "+example.seed+" · turn "+
            example.turn+" · event #"+example.eventIndex),
            el("p","small","Source card: "+(focus?.card_name||"unknown")+
              " · "+(focus?.kind||"unknown event")));
          const button=el("button","gold-button","Open complete turn reviewer");
          button.type="button";button.onclick=()=>selectGame(example.seed,true);
          container.append(button);
        }
      });
      if(panel)insights.append(panel);
    }
    insights.append(unavailable("Median turns held",
      "Gorge currently publishes hand SIZE, not the individual private card "+
      "identities at each turn. A card-level held-duration metric would "+
      "require the seat-owner-only hand export. Nothing is estimated."));
    insights.append(unavailable("Cards drawn but never played",
      "The public game samples intentionally omit private draw identities. "+
      "We cannot rank cards drawn and left in hand until a new privacy-aware "+
      "per-seat export is available."));
    const message=$("key-insights-empty");
    if(message)message.hidden=true;
  }
  const development=$("bounded-results");
  if(development){
    development.replaceChildren();
    development.append(el("p","small",stats.n+" gorge games · complete 40-life "+
      "four-player replays. State measurements occur at turn entry."));
    const all=el("div","board-grid");
    all.append(outcomeCard("Land Development","Public zone observations","Turn entry",
      "Visible land counts only; no inferred land play attribution",body=>{
      for(const g of stats.games){
        const seat=g.decks.indexOf(deck),snap=g.snapshots.at(-1).players[seat];
        const lands=snap.zones.battlefield.filter(c=>{
          const meta=lookup(c.name);
          return /\bLand\b/i.test(meta?.type_line||"")||
            BASIC.has(c.name.toLowerCase());
        });
        body.append(metric("Seed "+g.seed,lands.length+" lands",
          "Lands visible at turn "+g.snapshots.at(-1).turn+" entry"));
      }
    }),outcomeCard("Hand Development","Public information",
      "Counts only","Private card identities not published",body=>{
      for(const g of stats.games){
        const seat=g.decks.indexOf(deck);
        const final=g.snapshots.at(-1).players[seat];
        body.append(metric("Seed "+g.seed,final.hand_count+" cards",
          "Hand count at turn "+g.snapshots.at(-1).turn+" entry"));
      }
    }));
    development.append(all);
  }
  const quiet=$("quiet-status");
  if(quiet)quiet.textContent=
    "Gorge turn-entry states loaded. Old Python quiet-turn detector is archived; "+
    "a new action-based detector must use native event evidence.";
  const quietRoot=$("quiet-output");
  if(quietRoot)quietRoot.replaceChildren(el("p","micro",
    "A missing cast in the public event export does not prove the pilot "+
    "had nothing useful to do. The prior Python hand-aware detector "+
    "is not comparable and is not used here."));
  const sampleSelect=$("gorge-replay-sample-select");
  if(sampleSelect&&!stats.games.some(g=>g.seed===Number(sampleSelect.value))){
    // Leave the selected sample alone when another commander is selected,
    // but make it clear the dashboard's cohort is independent.
  }
}
function selectGame(seed,scroll=false){
  const select=$("gorge-replay-sample-select"),load=$("gorge-replay-load");
  const name="gorge-seed-"+seed+".ui.json";
  if(select&&load&&[...select.options].some(x=>x.value===name)){
    select.value=name;load.click();
    if(scroll)$("turn-reviewer-panel")?.scrollIntoView({
      behavior:"smooth",block:"start"});
  }
}
function moveOriginalPanels(){
  const legacy=$("legacy-simulation-archive"),content=$("app-content");
  if(!legacy||!content)return;
  const root=content.parentNode;
  for(const id of ["simulation-snapshot","key-insights-panel",
    "long-game-panel","turn-reviewer-panel","development-panel"]){
    const section=$(id);
    if(section)root.insertBefore(section,content);
  }
  const gorge=$("gorge-replay-panel"),reviewer=$("turn-reviewer-results");
  if(gorge&&reviewer){
    reviewer.append(gorge);gorge.open=true;gorge.hidden=false;
  }
  // Historical Python panels retain every original CSS class and their
  // old DOM IDs, but remain collapsed and explicitly labelled archival.
  root.insertBefore(legacy,content);
  const title=$("turn-reviewer-heading");
  if(title)title.textContent="Turn reviewer";
  const src=$("results-current-warning");
  if(src)src.hidden=true;
}
async function init(){
  if(typeof location==="undefined"||
     !location.pathname.endsWith("/results.html"))return;
  moveOriginalPanels();
  const refresh=$("game-outcome-refresh");
  if(refresh)refresh.onclick=()=>load(true);
  await load(false);
}
async function load(refresh=false){
  if(state.loading&&!refresh)return state.loading;
  const work=(async()=>{
    const response=await fetch("./gorge-data/manifest.json",
      {cache:refresh?"no-store":"default"});
    if(!response.ok)throw Error("No published gorge games");
    const manifest=await response.json();
    if(manifest.schema!=="gorge-public-replay-manifest-v1"||
       !Array.isArray(manifest.games)||!manifest.games.length)
      throw Error("Invalid gorge sample manifest");
    const entries=manifest.games.filter(x=>/^gorge-seed-[0-9]+\.ui\.json$/.test(x.file));
    const records=await Promise.all(entries.map(async entry=>{
      const resp=await fetch("./gorge-data/"+encodeURIComponent(entry.file),
        {cache:refresh?"no-store":"default"});
      if(!resp.ok)throw Error("Source game unavailable: "+entry.file);
      const game=await resp.json();
      validate(game);
      if(game.seed!==entry.seed||game.chain!==entry.chain)
        throw Error("Source game does not match manifest");
      return game;
    }));
    let meta=null;
    try{
      const res=await fetch("./decks.json");
      if(res.ok)meta=await res.json();
    }catch(e){/* Metadata unavailable; names remain evidence-based. */}
    state.games=records;state.catalog=meta||{cards:{}};
    paint();
    return records;
  })();
  state.loading=work;
  try{return await work}
  catch(err){
    const status=$("game-outcome-status");
    if(status)status.textContent="Gorge dataset unavailable: "+err.message;
    const insights=$("key-insights-empty");
    if(insights){insights.hidden=false;
      insights.textContent="Gorge game data is not available yet.";}
    throw err;
  }finally{state.loading=null;}
}
function setDeck(name){
  if(typeof name!=="string"||!name)return;
  state.requestedDeck=name;
  if(!state.games.length||seenGames(state.games,name).length)state.deck=name;
  if(state.games.length)paint();
}
if(typeof document!=="undefined"){
  if(document.readyState==="loading")
    document.addEventListener("DOMContentLoaded",()=>{init().catch(console.warn)});
  else init().catch(console.warn);
}
return {SCHEMA,validate,winner,seatForObject,analyze,castModel,lifeRows,
  median,paint,setDeck,load,selectGame};
});
