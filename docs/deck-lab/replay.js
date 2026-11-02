/* Replay renderer v1. Presentation only: no gameplay, rules, or inferred zones.
 * Source: versioned JSON produced by tools/build_opponent_replay.py.
 * Later full event streams can use the same rounds/seats/actions/snapshots API.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.CommanderReplay=api;
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const FORMAT="commander-replay-v1";
  const TYPES={
    land_play:["Land","land"],
    reviewed_commander_cast:["Commander cast","cast"],
    reviewed_common_spell_resolved:["Spell resolved","cast"],
    reviewed_removal_resolved:["Removal resolved","removal"],
    reviewed_composed_activated:["Ability activated","ability"],
    reviewed_composed_end_step:["End-step trigger","trigger"],
    reviewed_precast_mana_sacrifice:["Mana sacrifice","ability"],
    reviewed_sacrifice_activated:["Sacrifice ability","ability"],
    reviewed_utility_activated:["Utility ability","ability"],
    reviewed_zone_spell_resolved:["Zone spell resolved","cast"],
    reviewed_instant_response:["Instant response","cast"],
    reviewed_attachment_equipped:["Equipment attached","ability"],
    reviewed_attachment_reanimated:["Attachment reanimated","zone"],
    reviewed_aura_attached:["Aura attached","ability"],
    reviewed_attachment_upkeep:["Attachment upkeep","trigger"],
    reviewed_generic_activated:["Ability activated","ability"],
    reviewed_cast_reaction:["Cast reaction","trigger"],
    reviewed_reactive_trigger:["Reactive trigger","trigger"],
    reviewed_composed_tap_activation:["Tap ability","ability"],
    reviewed_composed_upkeep:["Upkeep trigger","trigger"],
    reviewed_enter_resolved:["Enters-battlefield ability","trigger"],
    player_abstract_blocked_combat:["Attack blocked","combat"],
    player_abstract_unblocked_damage:["Unblocked damage","combat"],
    opponent_abstract_creature:["Abstract creature pressure","abstract"],
    opponent_abstract_discard:["Abstract discard pressure","abstract"],
    opponent_abstract_destroy:["Abstract destruction","abstract"],
    opponent_abstract_exile:["Abstract exile","abstract"],
    opponent_abstract_blocked_combat:["Attack blocked","combat"],
    opponent_abstract_unblocked_damage:["Unblocked damage","combat"],
    opponent_abstract_combo_loss:["Abstract combo pressure","abstract"],
    opponent_reviewed_opponent_upkeep:["Opponent upkeep","trigger"],
    opponent_life_zero:["Opponent reached zero life","elimination"]
  };
  const titleCase=s=>String(s||"event").replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
  const isSeat=v=>Number.isInteger(v)&&v>=0&&v<=3;
  const roundNumber=r=>r.round;
  const eventKind=e=>(TYPES[e.type]||[titleCase(e.type),"other"])[1];
  const eventTitle=e=>(TYPES[e.type]||[titleCase(e.type),"other"])[0];

  function validate(data, expectedKey, expectedHash){
    if(!data||data.format!==FORMAT||data.schema_version!==1)
      throw Error("Unsupported replay schema; expected commander-replay-v1");
    if(data.deck_key!==expectedKey||data.deck_sha256!==expectedHash)
      throw Error("Replay does not match the selected deck's pinned revision.");
    const scenarios=Object.entries(data.scenarios||{});
    if(!scenarios.length)throw Error("Replay contains no scenarios");
    for(const [key,item] of scenarios){
      if(!Array.isArray(item.games)||!item.summary||item.summary.seeds<item.games.length)
        throw Error("Replay summary and available narrative samples disagree for "+key);
      for(const game of item.games){
        if(!Array.isArray(game.seats)||!Array.isArray(game.rounds)||game.scenario!==key)
          throw Error("Malformed replay game");
        for(const round of game.rounds){
          if(!Number.isInteger(roundNumber(round))||!Array.isArray(round.actions)||
             !round.snapshots||typeof round.snapshots!=="object")
            throw Error("Incomplete replay round");
          for(const action of round.actions){
            if(typeof action.type!=="string"||
               (action.actor_seat!==null&&!isSeat(action.actor_seat)))
              throw Error("Malformed replay action");
          }
        }
      }
    }
    return data;
  }

  function summarizeAction(action){
    const type=action.type,raw=action.fields||{},card=action.card_name;
    const actor=isSeat(action.actor_seat)?"Seat "+action.actor_seat:"Unattributed";
    const victim=isSeat(action.target_seat)?"Seat "+action.target_seat:null;
    if(type==="land_play")return "Played "+(card||"a land (name unrecorded)");
    if(type==="reviewed_commander_cast")return "Cast "+(card||"commander (name unrecorded)");
    if(type==="reviewed_removal_resolved")
      return "Resolved "+(card||"removal")+"; "+
        (Number.isInteger(raw.destroyed_count)?raw.destroyed_count+" objects destroyed":"target outcome not recorded");
    if(type==="opponent_life_zero")return "Seat "+raw.seat+" reached zero life (reported event)";
    if(type==="opponent_abstract_creature")
      return actor+" generated abstract creature pressure"+(Number.isFinite(raw.amount)?" (magnitude "+raw.amount+")":"");
    if(type==="opponent_abstract_unblocked_damage")
      return actor+" applied "+(raw.amount??"unquantified")+" abstract unblocked damage"+(victim?" to "+victim:"");
    if(type==="player_abstract_unblocked_damage")
      return "Seat 0 applied "+(raw.amount??"unquantified")+" abstract unblocked damage"+(victim?" to "+victim:"");
    if(type==="opponent_abstract_blocked_combat"||type==="player_abstract_blocked_combat")
      return (type.startsWith("player_")?"Seat 0":actor)+" attack was blocked"+(victim?" against "+victim:"")+" (abstract)";
    if(type==="opponent_abstract_discard"||type==="opponent_abstract_destroy"||
       type==="opponent_abstract_exile"||type==="opponent_abstract_combo_loss")
      return actor+" applied "+eventTitle(action).toLowerCase()+
        (victim?" toward "+victim:"")+(Number.isFinite(raw.amount)?" (magnitude "+raw.amount+")":"");
    return eventTitle(action)+(card?" · "+card:"");
  }

  function activity(round,seat){
    return round.actions.filter(action=>action.actor_seat===seat).length;
  }
  function statsForRound(round,seat){
    return Object.prototype.hasOwnProperty.call(round.snapshots,String(seat))?
      round.snapshots[String(seat)]:null;
  }
  function el(tag,cls,text){
    const node=document.createElement(tag);
    if(cls)node.className=cls;
    if(text!==undefined&&text!==null)node.textContent=String(text);
    return node;
  }
  function append(parent,...nodes){nodes.forEach(node=>parent.appendChild(node));return parent}
  function displayAmount(value){return typeof value==="number"?String(value):"Not recorded"}
  function seatName(seat){return seat.seat===0?"Mortarion · You":seat.label+" · "+(seat.role||"opponent")}
  function panelHeading(eyebrow,heading){
    const box=el("div","replay-intro");
    box.append(el("span","eyebrow",eyebrow),el("h2","replay-title",heading));
    return box;
  }
  function metric(label,value){
    const tile=el("div","replay-metric");
    tile.append(el("span","replay-metric-label",label),el("strong","replay-metric-value",value));
    return tile;
  }
  function validateCard(card){
    return card&&typeof card.name==="string"&&typeof card.oracle_id==="string"&&
      (typeof card.image==="string"||typeof card.art==="string");
  }
  function art(card,openCard){
    if(!validateCard(card))return null;
    const button=el("button","replay-card-art");button.type="button";
    button.title="View "+card.name;button.setAttribute("aria-label","View "+card.name);
    const image=el("img");image.alt=card.name;image.loading="lazy";
    image.src=card.art||card.image;
    button.appendChild(image);
    if(typeof openCard==="function")button.onclick=()=>openCard(card.oracle_id);
    else button.disabled=true;
    return button;
  }
  function detailedAction(action){
    const details=el("details","replay-action-detail");
    details.appendChild(el("summary",null,"Recorded fields & fidelity"));
    const dl=el("dl","replay-fields");
    const fields=Object.entries(action.fields||{});
    for(const [key,value] of fields){
      const dt=el("dt",null,titleCase(key));
      const dd=el("dd",null,value===null?"Not specified":typeof value==="object"?JSON.stringify(value):String(value));
      dl.append(dt,dd);
    }
    if(!fields.length)dl.append(el("dt",null,"Available data"),el("dd",null,"No additional fields"));
    details.appendChild(dl);
    details.appendChild(el("p","micro",action.fidelity==="abstract"?
      "Abstract pressure model, not a card-exact opponent action.":"Reviewed event with abbreviated source details; other outcomes may be omitted."));
    return details;
  }
  function actionRow(action,index,lookup,openCard){
    const card=action.card_name&&typeof lookup==="function"?lookup(action.card_name):null;
    const row=el("div","replay-action replay-kind-"+eventKind(action));
    const pic=art(card,openCard);
    if(pic)row.appendChild(pic);
    else row.appendChild(el("div","replay-action-symbol",{
      land:"◆",cast:"✧",removal:"✕",combat:"⚔",trigger:"✦",ability:"✳",
      elimination:"☠",abstract:"◌",zone:"◇",other:"·"
    }[eventKind(action)]||"·"));
    const body=el("div","replay-action-body");
    const header=el("div","replay-action-header");
    header.append(el("span","replay-action-type",eventTitle(action)),
      el("span","replay-action-seat",isSeat(action.actor_seat)?"Seat "+action.actor_seat:"Unattributed"));
    body.append(header,el("div","replay-action-label",summarizeAction(action)));
    if(action.card_name&&!card)body.appendChild(el("span","micro","Card art unavailable in pinned catalog"));
    if(isSeat(action.target_seat))body.appendChild(el("span","replay-target","Target: Seat "+action.target_seat));
    if(action.fields?.target_object_id!==undefined)
      body.appendChild(el("span","replay-target","Target object #"+action.fields.target_object_id+" · identity not in export"));
    body.appendChild(detailedAction(action));
    row.appendChild(body);
    return row;
  }
  function seatCard(round,seat,previous){
    const node=el("div","replay-seat replay-seat-"+seat.seat);
    const head=el("div","replay-seat-head");
    head.append(el("span","replay-seat-index","0"+seat.seat),el("strong",null,seatName(seat)));
    node.appendChild(head);
    const snapshot=statsForRound(round,seat.seat);
    if(snapshot){
      const prev=previous?statsForRound(previous,seat.seat):null;
      let difference="";
      if(prev&&typeof prev.life==="number"&&typeof snapshot.life==="number"){
        const d=snapshot.life-prev.life;
        if(d!==0)difference=" ("+(d>0?"+":"")+d+")";
      }
      node.appendChild(el("div","replay-seat-life",displayAmount(snapshot.life)+" life"+difference));
      node.appendChild(el("div","replay-seat-meta",
        displayAmount(snapshot.lands)+" lands · "+displayAmount(snapshot.creatures)+" creatures · "+
        displayAmount(snapshot.hand_size)+" in hand"));
      node.appendChild(el("div","replay-seat-note","Pilot counts only; zones not recorded"));
    }else{
      node.appendChild(el("div","replay-seat-life replay-untracked","Life not recorded"));
      node.appendChild(el("div","replay-seat-meta","Battlefield not recorded"));
      node.appendChild(el("div","replay-seat-note","Abstract opponent · "+activity(round,seat.seat)+" visible actions"));
    }
    return node;
  }
  function roundSection(round,previous,seats,lookup,openCard,index){
    const wrap=el("details","replay-round");wrap.open=index<2;
    const summary=el("summary","replay-round-summary");
    summary.append(el("span","replay-round-number","Round "+round.round),
      el("span","replay-round-counters",round.actions.length+" selected actions · "+
        (statsForRound(round,0)?.life??"—")+" pilot life"),
      el("span","replay-round-caret","Explore actions"));
    wrap.appendChild(summary);
    const board=el("div","replay-seats");
    seats.forEach(seat=>board.appendChild(seatCard(round,seat,previous)));
    wrap.appendChild(board);
    const actions=el("div","replay-action-list");
    if(round.actions.length){
      round.actions.forEach((action,i)=>actions.appendChild(actionRow(action,i,lookup,openCard)));
    }else actions.appendChild(el("p","small","No actions were retained in this abbreviated round narrative."));
    wrap.appendChild(actions);return wrap;
  }
  function lifeTrack(rounds){
    const points=rounds.filter(r=>typeof statsForRound(r,0)?.life==="number");
    if(!points.length)return null;
    const outer=el("div","replay-life-track");
    outer.append(el("strong",null,"Mortarion life progression"),
      el("span","micro","Recorded end-of-round life for Seat 0 only. Opponent life totals are not available."));
    const strip=el("div","replay-life-values");
    for(const round of points){
      const cell=el("div","replay-life-cell");
      cell.append(el("span",null,"R"+round.round),
        el("strong",null,statsForRound(round,0).life));
      strip.appendChild(cell);
    }
    outer.appendChild(strip);return outer;
  }
  function render(root,data,options={}){
    validate(data,options.deckKey,options.deckHash);
    let scenario=options.scenario&&data.scenarios[options.scenario]?options.scenario:
      Object.keys(data.scenarios)[0];
    let gameId=null;
    const lookup=options.lookup,openCard=options.openCard;
    function draw(){
      root.replaceChildren();
      const head=panelHeading("Opponent-pressure replays","Four-seat action timeline");
      head.appendChild(el("p","small",
        "Version 1 · source run #"+data.source.workflow_run_id+" · "+
        data.seeds_per_scenario+" simulated seeds per scenario. Only selected narrative samples were exported."));
      root.appendChild(head);
      root.appendChild(el("p","replay-fidelity",
        "Abbreviated, round-level events. Seat 0 has observed life and board counts; opponent life, boards, individual card draws, precise phases, and full zone changes are not in this artifact. No match win rates."));
      const layout=el("div","replay-scenario-grid");
      for(const [key,entry] of Object.entries(data.scenarios)){
        const summary=entry.summary;
        const button=el("button","replay-scenario"+(key===scenario?" is-active":""));
        button.type="button";button.setAttribute("aria-pressed",String(key===scenario));
        button.append(el("span","replay-scenario-title",titleCase(key)),
          el("strong",null,summary.survived_by_horizon+" / "+summary.seeds),
          el("span","micro","Seat 0 survived through observation horizon"),
          el("span","replay-scenario-foot",entry.games.length+" sample logs · mean final life "+summary.mean_life_at_last_observation));
        button.onclick=()=>{scenario=key;gameId=null;draw()};
        layout.appendChild(button);
      }
      root.appendChild(layout);
      const chosen=data.scenarios[scenario],games=chosen.games;
      const panel=el("section","replay-explorer");
      panel.appendChild(panelHeading("Explore a recorded game",titleCase(scenario)+" pressure"));
      const top=el("div","replay-explorer-overview");
      top.append(metric("Simulated seeds",chosen.summary.seeds),
        metric("Narratives available",games.length),
        metric("Mean pilot life (all seeds)",chosen.summary.mean_life_at_last_observation),
        metric("Pilot eliminated by horizon",chosen.summary.eliminated_by_horizon+" / "+chosen.summary.seeds));
      panel.appendChild(top);
      const note=el("p","micro",scenario==="goldfish"?
        "Goldfish is a solo baseline with no abstract opposing seats; no opponents are invented.":
        "Roles indicate the three modeled abstract adversaries. Surviving the horizon does not imply a game victory.");
      panel.appendChild(note);
      if(!games.length){panel.appendChild(el("p","small","No narrative examples were exported for this scenario."));root.appendChild(panel);return}
      const selection=el("div","replay-selection");
      const label=el("label",null,"Example game");
      const select=el("select");select.setAttribute("aria-label","Choose an example replay game");
      if(!games.some(g=>g.id===gameId))gameId=games[0].id;
      games.forEach(g=>{const opt=el("option",null,"Seed "+g.seed+" · "+
        g.rounds.length+" rounds · "+(g.eliminated?"pilot eliminated":"pilot still active"));
        opt.value=g.id;select.appendChild(opt)});
      select.value=gameId;
      select.onchange=()=>{gameId=select.value;draw()};
      label.appendChild(select);
      selection.appendChild(label);
      panel.appendChild(selection);
      const game=games.find(g=>g.id===gameId)||games[0];
      const seatLegend=el("div","replay-seat-legend");
      game.seats.forEach(seat=>seatLegend.appendChild(el("span","replay-seat-pill replay-seat-pill-"+seat.seat,seatName(seat))));
      panel.appendChild(seatLegend);
      const life=lifeTrack(game.rounds);if(life)panel.appendChild(life);
      panel.appendChild(el("p","micro",
        "Chronology is the order retained by the exporter within each numbered round—not a reconstructed player-turn or priority sequence. "+
        "Click a round to reveal the four seat summaries and the available action details."));
      const timeline=el("div","replay-timeline");
      game.rounds.forEach((round,i)=>timeline.appendChild(roundSection(round,game.rounds[i-1]||null,game.seats,lookup,openCard,i)));
      panel.appendChild(timeline);
      const end=el("div","replay-end");
      end.append(el("strong",null,game.eliminated?"Pilot eliminated in this example":"Pilot still active at end of example"),
        el("span","micro","No winner, opponent final standings, or complete battlefield state is recorded."));
      panel.appendChild(end);
      root.appendChild(panel);
    }
    draw();
    return {redraw:draw};
  }
  return {FORMAT,validate,eventKind,eventTitle,summarizeAction,activity,statsForRound,render};
});
