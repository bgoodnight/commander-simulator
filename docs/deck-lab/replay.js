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
  function actionRow(action,index,lookup,openCard,seats){
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
    const actorSeat=seats?.find(s=>s.seat===action.actor_seat);
    const actorLabel=action.actor_seat===0?"You · Mortarion":
      actorSeat?titleCase(actorSeat.role||"opponent")+" · Seat "+actorSeat.seat:
      isSeat(action.actor_seat)?"Seat "+action.actor_seat:"Event without actor";
    header.append(el("span","replay-action-type",eventTitle(action)),
      el("span","replay-action-seat",actorLabel));
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
  // Round-level measures only. Never infer individual token identities, mana
  // production, life-change causes, or opponent battlefield composition.
  const STARTING_LIFE=40;
  function changeIn(round,previous,field){
    const now=statsForRound(round,0)?.[field];
    const was=previous?statsForRound(previous,0)?.[field]:null;
    return typeof now==="number"&&typeof was==="number"?now-was:null;
  }
  function recordedCombat(round){
    return round.actions.reduce((counts,a)=>{
      const n=typeof a.fields?.amount==="number"?a.fields.amount:0;
      if(a.type==="player_abstract_unblocked_damage")counts.dealt+=n;
      if(a.type==="opponent_abstract_unblocked_damage"&&a.target_seat===0)counts.taken+=n;
      if(a.type==="player_abstract_blocked_combat")counts.blocks++;
      if(a.type==="opponent_abstract_blocked_combat"&&a.target_seat===0)counts.defended++;
      return counts;
    },{dealt:0,taken:0,blocks:0,defended:0});
  }
  function cardSpotlight(round,lookup){
    const picked=round.actions.find(a=>a.type==="reviewed_commander_cast"&&a.card_name)||
      round.actions.find(a=>a.card_name&&["reviewed_removal_resolved",
        "reviewed_common_spell_resolved","reviewed_zone_spell_resolved",
        "reviewed_composed_activated"].includes(a.type))||
      round.actions.find(a=>a.card_name&&a.type!=="land_play")||
      round.actions.find(a=>a.card_name&&a.type==="land_play");
    const card=picked?.card_name&&typeof lookup==="function"?lookup(picked.card_name):null;
    return {action:picked||null,card:validateCard(card)?card:null};
  }
  function statChangeClass(delta,kind){
    if(delta===null||delta===0)return "replay-stat-steady";
    if(kind==="life"||kind==="creatures")return delta>0?"replay-stat-up":"replay-stat-down";
    return delta>0?"replay-stat-up":"replay-stat-shift";
  }
  function statBadge(icon,label,value,delta,kind){
    const chip=el("span","replay-turn-stat "+statChangeClass(delta,kind));
    const amount=value===null||value===undefined?"—":String(value);
    chip.append(el("span","replay-turn-stat-icon",icon),
      el("span","replay-turn-stat-copy",label),
      el("strong","replay-turn-stat-number",amount));
    if(delta!==null&&delta!==0)
      chip.appendChild(el("span","replay-stat-delta",(delta>0?"+":"")+delta));
    return chip;
  }
  function relatedActions(round,topic){
    const relevant=round.actions.filter(a=>{
      const t=a.type, enemy=t.startsWith("opponent_"),us=a.actor_seat===0;
      switch(topic){
        case "life":
          return t.includes("life")||t.includes("damage")||
            t==="reviewed_composed_end_step"||t==="reviewed_reactive_trigger";
        case "lands":
          return t==="land_play"||t.includes("ramp")||t.includes("mana");
        case "creatures":
          return (us&&(t.includes("commander")||t.includes("sacrifice")||
            t.includes("enter")||t.includes("removal")||t.includes("creature")||
            t.includes("reanimated")))||
            (enemy&&a.target_seat===0&&(t.includes("destroy")||t.includes("exile")))||
            t==="opponent_life_zero";
        case "hand":
          return (us&&(t.includes("spell")||t.includes("cast")||t==="land_play"))||
            (enemy&&a.target_seat===0&&t.includes("discard"));
        case "combat":
          return t.includes("combat")||t.includes("damage");
        default:return true;
      }
    });
    return relevant;
  }
  function focusedNote(topic){
    return {
      life:"Only end-of-round life totals and a subset of damage events are retained. The recorded actions may not fully explain the net life change.",
      lands:"This is a land count, not a mana-production or available-mana estimate. Named land plays appear where they were exported.",
      creatures:"Creature totals are end-of-round counts. Net changes do not identify individual entries, deaths, or tokens; only explicitly named events can be shown as cards.",
      hand:"Hand size is an end-of-round count. Individual draws and the complete sequence of casts/discards are not in this abbreviated narrative.",
      combat:"These are selected, abstract combat events. Specific attacking or blocking cards and complete combat damage assignments are not available."
    }[topic];
  }
  function roundSection(round,previous,seats,lookup,openCard,index){
    const snapshot=statsForRound(round,0)||{};
    const life=typeof snapshot.life==="number"?snapshot.life:null;
    const healthDelta=changeIn(round,previous,"life");
    const creaturesDelta=changeIn(round,previous,"creatures");
    const landDelta=changeIn(round,previous,"lands");
    const handDelta=changeIn(round,previous,"hand_size");
    const spotlight=cardSpotlight(round,lookup);
    const combat=recordedCombat(round);
    const wrap=el("details","replay-round replay-turn-row");
    const summary=el("summary","replay-round-summary replay-turn-summary");
    const featured=spotlight.card&&(spotlight.card.art||spotlight.card.image);
    if(featured){
      const backdrop=el("img","replay-turn-backdrop");
      backdrop.src=featured;backdrop.alt="";backdrop.loading="lazy";
      summary.appendChild(backdrop);
    }
    const lead=el("span","replay-turn-lead");
    lead.append(el("span","replay-turn-number",""+round.round),
      el("span","replay-turn-title","Round "+round.round));
    const highlight=spotlight.action?
      summarizeAction(spotlight.action):
      (round.actions.length?"No named key play captured":"No key actions retained");
    lead.appendChild(el("span","replay-turn-highlight",highlight));
    summary.appendChild(lead);

    const stats=el("span","replay-turn-stats");
    const lifeLabel=life!==null?life+" / "+STARTING_LIFE:"—";
    const lifeChip=statBadge("♥","Life",lifeLabel,healthDelta,"life");
    lifeChip.title="End-of-round life / starting 40 (not a maximum)";
    const commander=typeof lookup==="function"?lookup("Mortarion, Daemon Primarch"):null;
    if(validateCard(commander)){
      const portrait=el("img","replay-life-portrait");portrait.alt="";
      portrait.src=commander.art||commander.image;portrait.loading="lazy";
      lifeChip.appendChild(portrait);
    }
    stats.append(lifeChip,
      statBadge("◆","Lands",snapshot.lands,landDelta,"lands"),
      statBadge("♟","Creatures",snapshot.creatures,creaturesDelta,"creatures"),
      statBadge("▤","Hand",snapshot.hand_size,handDelta,"hand"));
    summary.appendChild(stats);
    if(combat.dealt||combat.taken||combat.defended){
      const combatText=[
        combat.dealt?"⚔ "+combat.dealt+" dealt":null,
        combat.taken?"♥ −"+combat.taken+" recorded damage":null,
        combat.defended?"◈ "+combat.defended+" attacks blocked":null
      ].filter(Boolean).join(" · ");
      summary.appendChild(el("span","replay-turn-combat",combatText));
    }
    summary.appendChild(el("span","replay-turn-expand","Explore"));
    wrap.appendChild(summary);

    const body=el("div","replay-round-body");
    body.appendChild(el("p","micro replay-round-guidance",
      "Select a stat to inspect relevant recorded actions, or open the full play-by-play. Highlighted counts compare against the prior recorded round."));
    const tray=el("div","replay-focus-tray");
    const choices=el("div","replay-focus-choices");
    const detail=el("div","replay-focus-detail");
    const focusLabels=[
      ["life","♥ Life"],["lands","◆ Lands"],["creatures","♟ Creatures"],
      ["hand","▤ Hand"],["combat","⚔ Combat"]];
    const focusButtons=[];
    function showFocus(topic){
      detail.replaceChildren();
      for(const [name,button] of focusButtons)
        button.setAttribute("aria-pressed",String(name===topic));
      const current=statsForRound(round,0)||{};
      const label={
        life:"Life: "+displayAmount(current.life),
        lands:"Lands: "+displayAmount(current.lands),
        creatures:"Creatures: "+displayAmount(current.creatures),
        hand:"Hand: "+displayAmount(current.hand_size),
        combat:"Combat and targeting"
      }[topic];
      detail.append(el("strong","replay-focus-heading",label),
        el("p","micro",focusedNote(topic)));
      const actions=relatedActions(round,topic);
      if(!actions.length)detail.appendChild(el("p","small",
        "No relevant actions were retained for this category in this round."));
      else{
        const list=el("div","replay-action-list replay-focused-list");
        actions.forEach((a,i)=>list.appendChild(actionRow(a,i,lookup,openCard,seats)));
        detail.appendChild(list);
      }
    }
    for(const [topic,text] of focusLabels){
      const button=el("button","replay-focus-button",text);
      button.type="button";button.setAttribute("aria-pressed","false");
      button.onclick=()=>showFocus(topic);
      choices.appendChild(button);
      focusButtons.push([topic,button]);
    }
    tray.append(choices,detail);body.appendChild(tray);
    showFocus("creatures");

    const table=el("details","replay-table-context");
    table.appendChild(el("summary",null,
      "Table context · "+seats.length+" "+(seats.length===1?"seat":"seats")+" (opponents on request)"));
    const grid=el("div","replay-seats");
    seats.forEach(seat=>grid.appendChild(seatCard(round,seat,previous)));
    table.appendChild(grid);body.appendChild(table);

    const all=el("details","replay-playbyplay");
    all.appendChild(el("summary",null,"Full play-by-play · "+round.actions.length+" retained actions"));
    const actions=el("div","replay-action-list");
    if(round.actions.length)
      round.actions.forEach((a,i)=>actions.appendChild(actionRow(a,i,lookup,openCard,seats)));
    else actions.appendChild(el("p","small","No actions were retained in this abbreviated round."));
    all.appendChild(actions);body.appendChild(all);
    wrap.appendChild(body);
    return wrap;
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
  function takeaway(title,value,description,explanation){
    const item=el("details","replay-takeaway");
    const header=el("summary","replay-takeaway-summary");
    header.append(el("span","replay-takeaway-kicker",title),
      el("strong","replay-takeaway-value",value),
      el("span","replay-takeaway-description",description),
      el("span","replay-takeaway-explore","Explore evidence"));
    item.appendChild(header);
    item.appendChild(el("p","replay-takeaway-evidence",explanation));
    return item;
  }

  function render(root,data,options={}){
    validate(data,options.deckKey,options.deckHash);
    let scenario=options.scenario&&data.scenarios[options.scenario]?options.scenario:
      Object.keys(data.scenarios)[0];
    let gameId=null;
    const lookup=options.lookup,openCard=options.openCard;
    function draw(){
      root.replaceChildren();
      const heading=panelHeading("Example games · Mortarion",
        "Opponent pressure & turn progression");
      heading.appendChild(el("p","replay-lead-small",
        "Your board first, recorded actions on demand · "+data.seeds_per_scenario+
        " seeds per scenario · abbreviated pressure model, not verified game wins."));
      root.appendChild(heading);
      const scenarioBar=el("div","replay-scenario-picker");
      scenarioBar.appendChild(el("span","replay-picker-label","Compare pressure"));
      const buttons=el("div","replay-scenario-tabs");
      for(const [key,entry] of Object.entries(data.scenarios)){
        const active=key===scenario;
        const button=el("button","replay-scenario-tab"+(active?" is-active":""));
        button.type="button";button.setAttribute("aria-pressed",String(active));
        button.append(el("span","replay-scenario-tab-name",titleCase(key)),
          el("span","replay-scenario-tab-sub",entry.summary.mean_life_at_last_observation+" mean life"));
        button.onclick=()=>{scenario=key;gameId=null;draw()};
        buttons.appendChild(button);
      }
      scenarioBar.appendChild(buttons);root.appendChild(scenarioBar);

      const chosen=data.scenarios[scenario],summary=chosen.summary,games=chosen.games;
      const castCounts=summary.commander_cast_turn_counts||{};
      const never=Number(castCounts.never||0),cast=summary.seeds-never;
      const killed=Number(summary.eliminated_by_horizon||0);
      const cards=el("div","replay-takeaway-grid");
      cards.append(
        takeaway("Pressure survival",
          summary.survived_by_horizon+" / "+summary.seeds,
          "Still active after "+data.round_horizon+" rounds",
          killed+" of "+summary.seeds+" runs had Seat 0 eliminated by the recorded horizon. "+
          "This is survival against simplified opponent pressure, not a win rate."),
        takeaway("Life under pressure",
          String(summary.mean_life_at_last_observation),
          "Mean observed final life · 40 starting",
          "Mean Seat 0 life at the last observation, including any abbreviated runs. "+
          "Individual samples may differ significantly and can exceed the starting 40 life."),
        takeaway("Commander access",
          cast+" / "+summary.seeds,
          "Mortarion casts within the horizon",
          never+" run"+(never===1?"":"s")+" did not cast Mortarion within the "+
          data.round_horizon+"-round horizon. These counts reflect reviewed casts; "+
          "commander board presence at the end is not guaranteed."),
        takeaway("Reviewed removal",
          String(summary.average_reviewed_removal_per_seed??"—"),
          "Mean resolved removals per seed",
          "Only reviewed removal effects are counted; abstract opponent disruption "+
          "and unrecorded permanent identities cannot support card-specific attribution.")
      );
      root.appendChild(cards);

      const section=el("section","replay-explorer");
      const heading2=panelHeading("Inspect a recorded example","A game, one round at a time");
      section.appendChild(heading2);
      const control=el("div","replay-game-control");
      if(!games.length){
        section.appendChild(el("p","small","No example replay was exported for this scenario."));
        root.appendChild(section);return;
      }
      const label=el("label","replay-game-label","Example game");
      const select=el("select","replay-game-select");
      select.setAttribute("aria-label","Select an example replay game");
      if(!games.some(g=>g.id===gameId))gameId=games[0].id;
      for(const game of games){
        const opt=el("option",null,"Seed "+game.seed+" · "+
          game.rounds.length+" rounds · "+(game.eliminated?"Eliminated":"Survived horizon"));
        opt.value=game.id;select.appendChild(opt);
      }
      select.value=gameId;
      select.onchange=()=>{gameId=select.value;draw()};
      label.appendChild(select);control.appendChild(label);
      control.appendChild(el("div","replay-game-provenance",
        games.length+" narrated examples from "+summary.seeds+" simulated seeds"));
      section.appendChild(control);

      const game=games.find(g=>g.id===gameId)||games[0];
      const legend=el("details","replay-table-key");
      legend.appendChild(el("summary",null,"Show table seats and roles"));
      const seatLegend=el("div","replay-seat-legend");
      game.seats.forEach(seat=>seatLegend.appendChild(
        el("span","replay-seat-pill replay-seat-pill-"+seat.seat,seatName(seat))));
      legend.appendChild(seatLegend);section.appendChild(legend);
      section.appendChild(el("p","replay-legend",
        "Highlighted numbers changed since the previous round · ◆ lands, not available mana. "+
        "Expand a row for a specific stat, opponent context, or all recorded actions."));

      const timeline=el("div","replay-timeline");
      game.rounds.forEach((round,i)=>timeline.appendChild(
        roundSection(round,game.rounds[i-1]||null,game.seats,lookup,openCard,i)));
      section.appendChild(timeline);
      section.appendChild(el("p","replay-endline",
        game.eliminated?"Seat 0 was eliminated during this sample.":
        "Seat 0 was still active at the last observed round. No victory is inferred."));

      const trends=el("details","replay-table-key");
      trends.appendChild(el("summary",null,"Life totals over the sample"));
      const life=lifeTrack(game.rounds);
      if(life)trends.appendChild(life);
      section.appendChild(trends);
      const methodology=el("details","replay-table-key");
      methodology.appendChild(el("summary",null,"What this replay does and doesn't record"));
      methodology.appendChild(el("p","micro",
        "The source preserves selected events in exported order within each round, "+
        "not individual player turns or the full priority stack. Only Mortarion's "+
        "end-of-round life, lands, creatures and hand size are snapshots. "+
        "Opponent life/boards, mana spent, card draws, token identities and zone "+
        "movements are unavailable until later replay schemas include them. "+
        "Opposing roles use abstract behaviors, not invented named spells. "+
        "Source workflow #"+data.source.workflow_run_id+"."));
      section.appendChild(methodology);
      root.appendChild(section);
    }
    draw();
    return {redraw:draw};
  }
  return {FORMAT,validate,eventKind,eventTitle,summarizeAction,activity,statsForRound,render};
});
