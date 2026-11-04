/* Gorge -> original DeckGameOutcomes compatibility layer.
 * This is a DATA adapter: the 2026-11-03 renderer owns every visible
 * insight, outcome card, chart and inline game timeline.
 * Source: pinned, sanitized gorge-ui-replay-v1. Never manufacture
 * draws, winners or end-of-turn snapshots. Explicit synthetic omniscient
 * exports CAN reveal native private hand/library identities, but only with
 * the source's synthetic-only provenance flag.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else{root.GorgeLegacyAdapter=api;root.GorgeDashboard=api;}
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const FORMAT="commander-gorge-outcomes-v1";
  const COLORS=["W","U","B","R","G","C"];
  // Pinned Gorge native event.go ordinals, not action-name guesses.
  // AbilityPush=34; TriggerPush=27.  Additional push kinds preserve
  // explicit source attribution.  Ordinary mana ability uses are not all
  // recorded as ManaActivate (55): that kind covers special limited/gained
  // mana abilities, not every tapped land or rock.
  const ACTIVATION_IDS=new Set([34,55,67,79,88]);
  const TRIGGER_IDS=new Set([27,38,46,54,72,80]);
  const $=id=>typeof document!=="undefined"?document.getElementById(id):null;
  const cardInfo=name=>typeof window!=="undefined"?
    window.GorgeDeckLabCardInfo?.(name)||null:null;
  const nfmt=n=>Number.isFinite(n)?String(n):"—";
  function validateReplay(g){
    if(!g||g.schema!=="gorge-ui-replay-v1"||g.engine!=="gorge"||
       !["public_events_only","omniscient"].includes(g.visibility)||
       (g.visibility==="omniscient"&&g.synthetic_simulation_only!==true)||
       !Number.isInteger(g.seed)||
       !Array.isArray(g.decks)||g.decks.length!==4||
       !Array.isArray(g.turns)||!g.turns.length||
       !Array.isArray(g.snapshots)||!g.snapshots.length||
       typeof g.chain!=="string")return false;
    if(!g.snapshots.every(s=>s.boundary==="first_pending_decision_of_turn"&&
       Number.isInteger(s.turn)&&Array.isArray(s.players)&&s.players.length===4&&
       s.players.every((p,i)=>p.seat===i&&Number.isFinite(p.life)&&
         Number.isInteger(p.hand_count)&&p.zones&&
         ["battlefield","graveyard","exile","command",
          ...(g.visibility==="omniscient"?["hand","library"]:[])].every(k=>
           Array.isArray(p.zones[k]))&&
         (g.visibility!=="public_events_only"||
           (!("hand" in p.zones)&&!("library" in p.zones)))&&
         (g.visibility!=="omniscient"||
           (p.zones.hand.length===p.hand_count&&
            p.zones.library.length===p.library_count)))))return false;
    return g.snapshots[0].players.every(p=>p.life===40);
  }
  function realWinner(g){
    // Gorge's native game_over event contains the winning DECK key.
    // Only accept a unique, exact deck-key match. Never infer a winner from
    // life totals, partial snapshots or the existence of a game_over marker.
    const endings=g.turns.flatMap(t=>t.events||[]).filter(e=>e.kind==="game_over");
    if(endings.length!==1)return null;
    const label=String(endings[0].text||"");
    if(label.toLowerCase()==="draw")return "draw";
    const seats=g.decks.map((name,i)=>name===label?i:-1).filter(i=>i>=0);
    return seats.length===1?seats[0]:null;
  }
  function visibleNames(g){
    const names=new Map();
    for(const [id,name] of Object.entries(g.object_identity||{})){
      if(/^\d+$/.test(id)&&typeof name==="string"&&name.trim())
        names.set(Number(id),name);
    }
    // Public zone identities can name an earlier public land movement
    // without disclosing a hidden card, hand, or library identity.
    for(const snap of g.snapshots)for(const player of snap.players)
      for(const cards of Object.values(player.zones||{}))
        for(const card of cards||[])if(Number.isInteger(card.object_id)&&
          typeof card.name==="string"&&card.name.trim())
          names.set(card.object_id,card.name);
    for(const turn of g.turns)for(const e of turn.events||[])
      if(Number.isInteger(e.obj)&&typeof e.card_name==="string"&&e.card_name.trim())
        names.set(e.obj,e.card_name);
    return names;
  }
  function landAt(turn,index,names){
    const e=turn.events[index];
    // One exact visible hand-to-battlefield move precedes a native land_played
    // marker. The name must be source-identified by the same game object.
    for(let i=index-1;i>=0&&i>=index-5;i--){
      const row=turn.events[i];
      if(row.kind==="zone_change"&&row.from===1&&row.to===2&&
         Number.isInteger(row.obj)&&e.seq-row.seq<=4)
        return names.get(row.obj)||null;
    }
    return null;
  }
  function typeFor(name){
    const printed=cardInfo(name);
    return String(printed?.type_line||printed?.type||"").toLowerCase();
  }
  function castType(name){
    const type=typeFor(name);
    if(/\bcreature\b/.test(type))return "creature_cast";
    if(/\bartifact\b/.test(type))return "artifact_cast";
    if(/\benchantment\b/.test(type))return "enchantment_cast";
    return "reviewed_generic_spell_cast";
  }
  function mapSeat(real,hero){return (real-hero+4)%4;}
  function actor(e,turn){return Number.isInteger(e.player)?e.player:turn.seat;}
  function nativeAbilityActor(e){
    // Gorge omits player:0 on JSON encoding, including when the ability
    // fires during another seat's turn.  Use the exact native zero value,
    // NEVER the currently active turn seat.
    return Number.isInteger(e.player)?e.player:0;
  }
  function abilityAction(e,hero,names){
    const activated=ACTIVATION_IDS.has(e.kind_id);
    const triggered=TRIGGER_IDS.has(e.kind_id);
    if(!activated&&!triggered)return null;
    const card=e.card_name||names.get(e.obj)||null;
    const real=nativeAbilityActor(e);
    if(real<0||real>3)return null;
    return {
      type:activated?"ability_activated":"ability_triggered",
      card,source:card,seat:mapSeat(real,hero),
      source_object_id:Number.isInteger(e.obj)?e.obj:null,
      native_kind_id:e.kind_id,
      // Index is the exact printed ability/trigger index only for
      // standard AbilityPush/TriggerPush. Other events overload Amount.
      native_ability_index:[27,34].includes(e.kind_id)?
        (Number.isInteger(e.amount)?e.amount:0):null,
      native_ability_family:e.kind_id===55?"special_mana":
        e.kind_id===34?"activated":e.kind_id===27?"triggered":
        "specialized",
      source_seq:e.seq,source_kind:e.kind
    };
  }
  function observedLife(s,hero,round,previous){
    const life_totals={},alive_seats=[],life_changes=[],new_eliminations=[];
    for(let real=0;real<4;real++){
      const seat=mapSeat(real,hero),p=s.players[real];
      life_totals[seat]=p.life;
      if(!p.lost)alive_seats.push(seat);
      if(previous){
        const prior=previous.players[real];
        if(prior.life!==p.life){
          // Only the observed net change is known at this boundary.
          // Its exact cause cannot be inferred from a pair of snapshots.
          life_changes.push({seat,kind:"net_observed_change",delta:p.life-prior.life,
            amount:Math.abs(p.life-prior.life),before:prior.life,after:p.life,
            source_object_id:null});
        }
        if(!prior.lost&&p.lost)
          new_eliminations.push({seat,round,cause:"observed eliminated at turn entry"});
      }
    }
    return {round,life_totals,alive_seats,life_changes,new_eliminations,
      source_boundary:s.boundary,source_turn:s.turn};
  }
  function sourceActions(g,hero,turnStart,turnEnd,names){
    const actions=[],mana={W:0,U:0,B:0,R:0,G:0,C:0};
    for(const t of g.turns){
      if(!Number.isInteger(t.turn)||t.turn<turnStart||
         t.turn>=turnEnd)continue;
      for(let i=0;i<(t.events||[]).length;i++){
        const actionStart=actions.length;
        const e=t.events[i],real=actor(e,t),seat=mapSeat(real,hero);
        const ability=abilityAction(e,hero,names);
        if(ability){
          ability.native_turn=t.turn;
          actions.push(ability);
        }else if(e.kind==="cast"){
          const name=e.card_name||names.get(e.obj)||null;
          actions.push({type:castType(name),card:name,seat,
            native_turn:t.turn,source_seq:e.seq,source_kind:e.kind});
        }else if(e.kind==="draw"){
          const name=e.card_name||names.get(e.obj)||null;
          if(name)actions.push({type:"draw",card:name,seat,
            native_turn:t.turn,source_seq:e.seq,source_kind:e.kind,
            omniscient:g.visibility==="omniscient"});
        }else if(e.kind==="land_played"){
          const name=landAt(t,i,names);
          actions.push({type:"land_play",card:name,seat,
            native_turn:t.turn,source_seq:e.seq,source_kind:e.kind});
        }else if(e.kind==="mana"&&seat===0&&Number(e.amount)>0){
          // Positive mana-pool changes are production, negative are spending.
          // ArtifactB/ArtifactC preserve their actual color, not a guess.
          const match=String(e.counter||"").match(/^(?:Artifact)?([WUBRGC])$/);
          if(match)mana[match[1]]+=e.amount;
        }else if(e.kind==="token_created"&&seat===0){
          actions.push({type:"token_created",card:names.get(e.obj)||null,seat,
            native_turn:t.turn,source_seq:e.seq,source_kind:e.kind});
        }
        // The source turn owner is distinct from an event's actor:
        // an opponent can respond or trigger during another player's turn.
        for(let k=actionStart;k<actions.length;k++)
          actions[k].native_turn_seat=mapSeat(t.seat,hero);
        // Native Resolve events name a minted stack object, not the
        // originating permanent. Do not attach later damage, tokens or
        // resolutions to this activation without an explicit source link.
      }
    }
    return {actions,mana};
  }
  function namedZone(p,key){
    return Array.isArray(p?.zones?.[key])?
      p.zones[key].filter(x=>typeof x.name==="string").map(x=>x.name):null;
  }
  function projectRun(g,hero,requestedRounds,deckHashes){
    if(!validateReplay(g)||!Number.isInteger(hero)||hero<0||hero>3)
      throw Error("Invalid source Gorge game or selected seat");
    const own=g.turns.filter(t=>Number.isInteger(t.turn)&&t.turn>0&&t.seat===hero);
    if(!own.length||own.length>30)throw Error("Unsupported Gorge round count");
    const snapshots=new Map(g.snapshots.map(s=>[s.turn,s]));
    const names=visibleNames(g),baseline=g.snapshots[0];
    const omniscient=g.visibility==="omniscient";
    const otherHands=frame=>[0,1,2,3].filter(seat=>seat!==hero).map(seat=>({
      seat:mapSeat(seat,hero),
      deck_key:g.decks[seat],
      hand:namedZone(frame.players[seat],"hand"),
      hand_count:frame.players[seat].hand_count
    })).sort((a,b)=>a.seat-b.seat);
    // All four seat snapshots come from Gorge's actual omniscient state.
    // Never reconstruct an opponent's hand/battlefield from observed actions.
    const boardStates=frame=>[0,1,2,3].map(real=>{
      const p=frame.players[real];
      return {
        seat:mapSeat(real,hero),deck_key:g.decks[real],
        hand:omniscient?namedZone(p,"hand"):null,
        hand_count:p.hand_count,
        battlefield:namedZone(p,"battlefield"),
        graveyard:namedZone(p,"graveyard"),exile:namedZone(p,"exile"),
        command:namedZone(p,"command"),
        snapshot_is_turn_end:false
      };
    }).sort((a,b)=>a.seat-b.seat);
    const life_history=[observedLife(baseline,hero,0,null)];
    const ui_observations=[];
    for(let i=0;i<own.length;i++){
      const start=own[i].turn,next=own[i+1]?.turn||Infinity;
      const observed=Number.isFinite(next)?snapshots.get(next):
        [...g.snapshots].reverse().find(s=>s.turn>=start);
      // Last recorded snapshot can precede the game's terminal event.
      // It remains an identified observation, never a fabricated final state.
      const frame=observed||snapshots.get(start)||g.snapshots.at(-1);
      const {actions,mana}=sourceActions(g,hero,start,next,names);
      const p=frame.players[hero];
      const turn=i+1;
      const obs={
        turn,actions,board_states:boardStates(frame),
        hand:omniscient?namedZone(p,"hand"):null,
        hand_count:p.hand_count,
        opponent_hands:omniscient?otherHands(frame):null,
        battlefield:namedZone(p,"battlefield"),
        graveyard:namedZone(p,"graveyard"),
        exile:namedZone(p,"exile"),
        command:namedZone(p,"command"),
        mana_produced_by_color:mana,
        source_boundary:"first_pending_decision_of_turn",
        source_turn:frame.turn,
        snapshot_is_turn_end:false,
        snapshot_note:Number.isFinite(next)?
          "Next own-turn entry; intervening opponent actions included":
          "Last captured turn-entry frame; not the game's final board",
      };
      ui_observations.push(obs);
      life_history.push(observedLife(frame,hero,turn,
        i?null:baseline));
      // Preserve observations as-is; previous turn's sampled life is not
      // authoritative to attribute intervening sources or life deltas.
    }
    const winner=realWinner(g);
    const status=winner==="draw"?"draw":
      Number.isInteger(winner)?winner===hero?"win":"loss":"unresolved";
    const finished=winner==="draw"||Number.isInteger(winner);
    const opponent_decks=[0,1,2,3].filter(i=>i!==hero).map(i=>({
      seat:mapSeat(i,hero),native_seat:i,deck_key:g.decks[i],
      commander_name:namedZone(baseline.players[i],"command")?.[0]||g.decks[i],
      deck_sha256:deckHashes?.[g.decks[i]]||"",
    })).sort((a,b)=>a.seat-b.seat);
    return {
      seed:g.seed,completed_rounds:own.length,
      opening_board_states:boardStates(baseline),
      opening_hand:omniscient?namedZone(baseline.players[hero],"hand"):null,
      opening_hands_by_seat:omniscient?otherHands(baseline):null,
      opening_hand_count:baseline.players[hero].hand_count,
      mulligan:null,ui_observations,life_history,opponent_decks,
      gorge_source:{chain:g.chain,original_seat:hero,visibility:g.visibility,
        source_event_count:g.source?.total_native_events,
        public_event_count:g.source?.exported_events,
        snapshot_boundary:"first_pending_decision_of_turn",
        synthetic_simulation_only:omniscient,
        outcome_provenance:finished?"native_game_over_event":"not_exported"},
      outcome:{status,complete:finished,reason:finished?
        "Verified Gorge game-over event":"Winner not recorded in public events",
        winner_seat:Number.isInteger(winner)?mapSeat(winner,hero):null,
        completed_rounds:own.length,requested_rounds:requestedRounds,
        surviving_seats:[],eliminations:[],fidelity:"gorge_native_four_player"},
    };
  }
  function adapt(games,key,deckHashes={}){
    const actual=(games||[]).filter(g=>validateReplay(g)&&g.decks.includes(key));
    if(!actual.length)return null;
    const selected=deckHashes[key];
    if(!selected)return null;
    const rounds=Math.max(...actual.map(g=>g.turns.filter(t=>t.turn>0&&
      t.seat===g.decks.indexOf(key)).length));
    if(rounds>30)return null; // Original renderer hard cap: do not silently truncate.
    const runs=actual.map(g=>projectRun(g,g.decks.indexOf(key),rounds,deckHashes));
    const batch={
      format:FORMAT,schema_version:1,engine:"gorge",
      deck_key:key,deck_sha256:selected,scenario:"four_real_commander_decks",
      pilot_style:"gorge_bot",provisional_mode:"not_applicable",
      opponent_fidelity:"gorge_native_full_100_card_decks",
      outcomes_are_competitive_win_rates:false,
      requested_rounds:rounds,runs,
      source_note:"Source-native Gorge synthetic games; omniscient hidden zones only when explicitly exported",
      example_replays:[],
    };
    return batch;
  }
  function render(games,activeSeed,deckKey){
    if(typeof document==="undefined")return;
    const key=deckKey||window.__deckLabActiveKey;
    const selected=window.GorgeDeckLabSelectedDeck?.(key);
    const outcomes=$("game-outcome-results");
    const status=$("game-outcome-status");
    const reviewer=$("turn-reviewer-results");
    if(!outcomes)return;
    const records=(games||[]).filter(validateReplay);
    const deckHashes=window.GorgeDeckLabDeckHashes?.()||{};
    const batch=selected?.eligible?adapt(records,key,deckHashes):null;
    const panel=$("turn-reviewer-panel");
    if(panel)panel.hidden=!batch;
    const refresh=$("game-outcome-refresh");if(refresh)refresh.hidden=true;
    for(const id of ["simulation-snapshot","key-insights-panel","development-panel",
      "archive-observation-details","opponent-replay-panel"]){
      const n=$(id);if(n)n.hidden=true;
    }
    const diagnostics=$("pane-records")?.querySelector(".diagnostic-panel");
    if(diagnostics)diagnostics.hidden=true;
    const raw=$("gorge-replay-panel");
    if(raw)raw.hidden=false;
    if(!selected?.eligible){
      outcomes.replaceChildren(document.createTextNode(
        "No verified Gorge simulation matches this exact built-in deck revision."));
      if(status)status.textContent="No matching Gorge batch";
      if(reviewer)reviewer.replaceChildren();return;
    }
    if(!batch){
      outcomes.replaceChildren(document.createTextNode(records.length?
        "No recorded Gorge game includes this exact deck.":
        "Loading source-verified Gorge simulations…"));
      // Offer a real matching Gorge run for the other Mortarion revision
      // without falsely presenting it as the selected Physical Final deck.
      if(records.length&&key==="mortarion_physical_final"&&
         records.some(game=>game.decks.includes("mortarion_current"))){
        const note=document.createElement("p");
        note.textContent="The available Mortarion simulation uses a different 100-card "+
          "revision (Current), not Physical Final. Three cards differ.";
        const link=document.createElement("a");
        const url=new URL(window.location.href);
        url.searchParams.set("deck","mortarion_current");
        url.searchParams.delete("version");
        link.href=url.toString();
        link.textContent="View Mortarion Current Gorge results";
        link.style.display="inline-block";
        link.style.marginTop="12px";
        outcomes.append(note,link);
      }
      if(status)status.textContent=records.length?"No Gorge games for this exact deck":"Loading Gorge games…";
      if(reviewer)reviewer.replaceChildren();return;
    }
    if(!window.DeckGameOutcomes?.validate(batch)){
      outcomes.replaceChildren(document.createTextNode("Gorge compatibility export failed validation."));
      if(status)status.textContent="Cannot validate Gorge export";return;
    }
    if(status)status.textContent=batch.runs.length+" real Gorge game"+
      (batch.runs.length===1?"":"s")+" · "+batch.runs[0].ui_observations.length+
      " recorded turns · "+(batch.runs[0].gorge_source.visibility==="omniscient"?
        "omniscient simulated hands and draws":"public-only replay");
    window.DeckGameOutcomes.render(outcomes,[batch],{
      deckKey:key,deckHash:deckHashes[key],
      commanderName:selected.commander,commanderArt:selected.art,
      isGorge:true,
      reviewerRoot:reviewer,reviewerPanel:panel,
      lookupRecordedCard:cardInfo,
      renderMana:value=>window.GorgeDeckLabMana?.(value),
      onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
    });
  }
  return {FORMAT,validateReplay,visibleNames,realWinner,projectRun,
    abilityAction,adapt,render};
});
