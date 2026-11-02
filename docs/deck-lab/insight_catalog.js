/* Data models for conditional, evidence-backed simulation insights.
 * These functions do not run Magic rules. They classify only explicitly
 * recorded events and snapshots from a pinned simulator/replay archive.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.DeckInsightCatalog=api;
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const SUPPORTED_TYPES=["Creature","Artifact","Enchantment","Sorcery","Instant"];
  const HAND_CASTS=new Set(["creature_cast","artifact_cast","enchantment_cast",
    "tutor_cast","token_spell_cast","reviewed_draw_spell_cast",
    "reviewed_ritual_cast","reviewed_buyback_cast","reviewed_flashback_cast",
    "reviewed_escape_cast","reviewed_graveyard_spell_cast",
    "reviewed_copy_spell_cast","reviewed_instant_response",
    "reviewed_commander_cast","reviewed_generic_spell_cast",
    "provisional_spell_cast"]);
  const SPELL_CASTS=new Set([...HAND_CASTS,"reviewed_common_spell_resolved",
    "reviewed_zone_spell_resolved"]);
  const APPLICABLE_RESOLUTIONS={
    Creature:new Set(["creature_resolved"]),
    Artifact:new Set(["artifact_resolved"]),
    Enchantment:new Set(["enchantment_resolved"]),
    Land:new Set(["land_play"]),
    Instant:SPELL_CASTS,Sorcery:SPELL_CASTS
  };
  const round=n=>Number.isFinite(n)?Math.round(n):null;
  const median=values=>{
    if(!values.length)return null;
    const v=[...values].sort((a,b)=>a-b),m=Math.floor(v.length/2);
    return v.length%2?v[m]:(v[m-1]+v[m])/2;
  };
  const part=name=>String(name||"").trim().toLowerCase();
  function isType(card,type){
    return !!card&&new RegExp("\\b"+type+"\\b","i")
      .test(String(card.type_line||"").split("—")[0]);
  }
  function cardsByName(names){
    return [...new Set((names||[]).filter(x=>typeof x==="string"&&x.trim()))];
  }
  function usableRuns(runs){
    return (runs||[]).filter(run=>Number.isInteger(run?.seed)&&
      Array.isArray(run.events)&&run.events.length&&
      Array.isArray(run.state_snapshots)&&
      run.state_snapshots.length>=run.events.length);
  }
  function isPlayedEvent(event){
    return !!event&&typeof event.card==="string"&&(
      HAND_CASTS.has(event.type)||event.type==="land_play"||
      event.type==="reviewed_common_spell_resolved"||
      event.type==="reviewed_zone_spell_resolved");
  }
  function isRecordedPlay(event,type,card){
    if(!isType(card,type))return false;
    if(!APPLICABLE_RESOLUTIONS[type]?.has(event.type))return false;
    if(type==="Creature"||type==="Artifact"||type==="Enchantment"||type==="Land")return true;
    // Other non-hand spell effects such as copy triggers are not hand casts.
    return SPELL_CASTS.has(event.type);
  }
  function seedFacts(run){
    const seen=new Set(cardsByName(run.mulligan?.opening_hand));
    const played=new Set();
    const handTurns=new Map();
    const previewTurns=new Map();
    const firstSeen=new Map();
    const drawEvidence=new Map();
    for(const name of cardsByName(run.mulligan?.opening_hand))firstSeen.set(name,1);
    for(let i=0;i<run.events.length;i++){
      const turn=run.events[i],number=turn.turn,hand=cardsByName(
        run.state_snapshots[i]?.hand);
      const handSet=new Set(hand);
      for(const name of hand){
        seen.add(name);
        if(!firstSeen.has(name))firstSeen.set(name,number);
        if(!handTurns.has(name))handTurns.set(name,[]);
        handTurns.get(name).push({turn:number,run,seed:run.seed,source:"bounded",
          cardName:name,focusTopic:"hand",eventIndex:null,
          description:"Still in hand at the end of turn "+number});
      }
      (turn.events||[]).forEach((event,eventIndex)=>{
        if(typeof event.card!=="string")return;
        const name=event.card;
        if(event.type==="draw"){
          seen.add(name);if(!firstSeen.has(name))firstSeen.set(name,number);
          drawEvidence.set(name,{turn:number,run,seed:run.seed,source:"bounded",
            cardName:name,eventIndex,focusTopic:"hand",
            description:"Drawn on turn "+number+"; no cast recorded through the horizon"});
        }
        if(isPlayedEvent(event)){played.add(name);seen.add(name);
          if(!firstSeen.has(name))firstSeen.set(name,number)}
        // Previewed source payment is checked by the engine AFTER its
        // modeled plays, and BEFORE cleanup; only count cards still in the
        // hand snapshot. It does NOT establish timing, targets or permission.
        if(event.type==="source_paid_candidate"&&handSet.has(name)){
          if(!previewTurns.has(name))previewTurns.set(name,[]);
          previewTurns.get(name).push({
            seed:run.seed,turn:number,run,source:"bounded",cardName:name,
            eventIndex,focusTopic:"hand",
            description:"Printed cost was payable in a post-action source preview; casting legality untested"
          });
        }
      });
    }
    return {seen,played,handTurns,previewTurns,firstSeen,drawEvidence};
  }
  function evidence(run,turn,eventIndex,cardName,description){
    return {source:"bounded",run,seed:run.seed,turn,eventIndex,cardName,
      description,focusTopic:null};
  }
  function commonPlayedByType(runs,lookup,type){
    if(!SUPPORTED_TYPES.includes(type)&&type!=="Land")return null;
    const valid=usableRuns(runs);
    if(!valid.length)return null;
    const records=new Map(),access=new Map();
    for(const run of valid){
      const facts=seedFacts(run);
      for(const name of facts.seen){
        if(!isType(lookup(name),type))continue;
        if(!access.has(name))access.set(name,new Set());
        access.get(name).add(run.seed);
      }
      for(const row of run.events){
        (row.events||[]).forEach((event,index)=>{
          const name=event.card;
          if(typeof name!=="string"||!isRecordedPlay(event,type,lookup(name)))return;
          if(!records.has(name))records.set(name,{name,ids:new Set(),first:new Map(),examples:[]});
          const record=records.get(name);
          // A card cast implies access even if it left the hand before
          // the end-of-turn snapshot.
          if(!access.has(name))access.set(name,new Set());
          access.get(name).add(run.seed);
          record.ids.add(run.seed);
          record.first.set(run.seed,Math.min(row.turn,record.first.get(run.seed)??Infinity));
          record.examples.push(evidence(run,row.turn,index,name,
            "Recorded "+(type==="Land"?"land play":"cast/resolution")+" on turn "+row.turn));
        });
      }
    }
    const contenders=[...records.values()].map(c=>{
      const turns=[...c.first.values()],first=median(turns);
      const examples=[...c.examples].sort((a,b)=>a.seed-b.seed||a.turn-b.turn||a.eventIndex-b.eventIndex);
      const observed=access.get(c.name)?.size||0;
      return {
        name:c.name,card:lookup(c.name),score:c.ids.size,
        scoreLabel:c.ids.size+" / "+valid.length+" runs",
        metrics:[
          {id:"played",label:"Runs played",value:c.ids.size+" / "+valid.length,
           explanation:"Runs with at least one named recorded play/resolution of this "+type.toLowerCase()+" within the modeled horizon.",
           examples},
          {id:"access",label:"Played when seen",
           value:observed?round(100*c.ids.size/observed)+"%":"—",
           explanation:c.ids.size+" of "+observed+" runs where the card appeared in a retained hand, draw or recorded play. This does not measure actual legal casting opportunities.",
           examples},
          {id:"turn",label:"Median first turn",value:first===null?"—":String(first),
           explanation:"Median turn of its first recorded play in the runs where it was played.",
           examples:[...examples].sort((a,b)=>Math.abs(a.turn-first)-Math.abs(b.turn-first)||a.seed-b.seed)},
          {id:"total",label:"Total plays",value:String(examples.length),
           explanation:"Number of recorded plays, counting repeated casts within the same seed. Only the first event matching the category is counted per action.",
           examples}
        ]
      };
    }).filter(c=>c.score>0).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
    // One rare played card is not an interesting comparative leaderboard.
    if(contenders.length<2||contenders[0].score<2)return null;
    const label=type.toLowerCase();
    return {
      id:"most-played-"+label,kind:"frequency",title:"Most common "+label,
      value:contenders[0].score+" / "+valid.length,
      chartLabel:"Runs with a recorded "+label+" play",
      explanation:"Compared by the share of pinned early-game runs with an explicitly recorded play. This measures frequency, not strength, combat impact or a full-game win contribution.",
      contenders,total:valid.length
    };
  }

  function heldInHand(runs,lookup){
    const valid=usableRuns(runs);if(valid.length<2)return null;
    const summaries=new Map();
    for(const run of valid){
      const facts=seedFacts(run);
      for(const [name,all] of facts.handTurns){
        const card=lookup(name);
        if(!card||isType(card,"Land"))continue;
        if(!summaries.has(name))summaries.set(name,{
          name,card,runs:new Map(),previews:[],unusedRuns:new Set()});
        const row=summaries.get(name);
        row.runs.set(run.seed,all);
        row.previews.push(...facts.previewTurns.get(name)||[]);
        if(!facts.played.has(name))row.unusedRuns.add(run.seed);
      }
    }
    const contenders=[...summaries.values()].map(c=>{
      const holdTurns=[...c.runs.values()].flat();
      const count=c.runs.size,total=holdTurns.length;
      const holdsPerSeed=[...c.runs.values()].map(x=>x.length);
      const best=[...c.runs.entries()].sort((a,b)=>b[1].length-a[1].length||a[0]-b[0])
        .map(([,x])=>x[x.length-1]);
      const previews=[...c.previews].sort((a,b)=>a.seed-b.seed||a.turn-b.turn);
      const noCast=best.filter(x=>c.unusedRuns.has(x.seed));
      return {
        name:c.name,card:c.card,score:total,
        scoreLabel:total+" turns / "+count+" runs",
        viewScores:{held:total,payable:previews.length},
        viewLabels:{held:total+" held turns",payable:previews.length+" cost previews"},
        metrics:[
          {id:"held",label:"Turns in hand",value:String(total),
           explanation:"Total end-of-turn snapshots containing this card. Counts only retained hand snapshots, including turns when the card may not be castable.",
           examples:best},
          {id:"seeds",label:"Runs held",value:count+" / "+valid.length,
           explanation:"Distinct pinned seeds with this card still in hand at the end of at least one turn.",
           examples:best},
          {id:"duration",label:"Median turns held",
           value:String(median(holdsPerSeed)),
           explanation:"Median number of end-of-turn hand snapshots among runs in which this card remained in hand at least once. Not uninterrupted elapsed time since draw.",
           examples:best},
          {id:"payable",label:"Cost-payable turns",value:String(previews.length),
           explanation:"Explicit source-paid printed-cost previews for a card that remained in hand. Measured after the pilot's modeled actions; not evidence of legal timing, valid targets or a missed play. Supported spells often have no such preview.",
           examples:previews},
          {id:"unplayed",label:"Not played in run",value:c.unusedRuns.size+" / "+count,
           explanation:"Among runs with the card observed in end-of-turn hand, no named cast was recorded through the six-turn horizon; this may be unsupported simulator behavior.",
           examples:noCast}
        ]
      };
    }).filter(c=>c.score>=2).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
    if(contenders.length<2)return null;
    const payment=contenders.some(c=>c.viewScores.payable>0);
    return {
      id:"held-in-hand",kind:"diagnostic",title:"Most often held in hand",
      value:String(contenders[0].score),chartLabel:"Observed end-of-turn hand appearances",
      explanation:"The primary ranking counts turns spent in retained hands, regardless of mana. When available, switch to a source-paid printed-cost preview; that diagnostic does not prove a legal casting opportunity or a piloting mistake.",
      views:[
        {id:"held",label:"All held turns",chartLabel:"End-of-turn hand appearances"},
        ...(payment?[{id:"payable",label:"Cost-payable previews",
          chartLabel:"Verified post-action printed-cost payment previews while still held"}]:[])
      ],
      contenders,total:valid.length
    };
  }

  function leftUnplayed(runs,lookup){
    const valid=usableRuns(runs);if(valid.length<2)return null;
    const records=new Map();
    for(const run of valid){
      const facts=seedFacts(run);
      for(const name of facts.seen){
        const card=lookup(name);
        if(!card||isType(card,"Land"))continue;
        if(!records.has(name))records.set(name,{
          name,card,seen:new Set(),unused:new Set(),end:new Set(),examples:[],
          unsupported:new Set(),firstTurns:[]});
        const c=records.get(name);
        c.seen.add(run.seed);
        if(facts.played.has(name))continue;
        c.unused.add(run.seed);
        if(run.state_snapshots.at(-1)?.hand?.includes(name))c.end.add(run.seed);
        if(run.events.some(row=>(row.unsupported_cards_in_hand||[]).includes(name)))
          c.unsupported.add(run.seed);
        c.firstTurns.push(facts.firstSeen.get(name)||1);
        const hands=facts.handTurns.get(name)||[];
        const latest=hands.at(-1)||facts.drawEvidence.get(name);
        if(latest)c.examples.push({...latest,description:
          "Seen but no named play was recorded through turn "+
          run.events[run.events.length-1].turn+
          (c.unsupported.has(run.seed)?" · simulator flagged unsupported effects":"")});
      }
    }
    const contenders=[...records.values()].map(c=>{
      const examples=[...c.examples].sort((a,b)=>a.seed-b.seed||a.turn-b.turn);
      const used=c.seen.size-c.unused.size;
      return {
        name:c.name,card:c.card,score:c.unused.size,
        scoreLabel:c.unused.size+" / "+c.seen.size+" seen",
        metrics:[
          {id:"unused",label:"Runs not played",value:c.unused.size+" / "+c.seen.size,
           explanation:"Runs where the card appeared in a retained hand or recorded draw, but no named cast/resolution was recorded by the end of the simulated horizon.",
           examples},
          {id:"fraction",label:"Not played when seen",value:round(100*c.unused.size/c.seen.size)+"%",
           explanation:c.unused.size+" of "+c.seen.size+" observed accesses lacked a recorded play. An unimplemented ability can produce this without indicating the card is strategically poor.",
           examples},
          {id:"horizon",label:"Still in final hand",value:c.end.size+" runs",
           explanation:"Distinct runs with this card in the last recorded end-of-turn hand, and no recorded play.",
           examples:examples.filter(e=>c.end.has(e.seed))},
          {id:"coverage",label:"Unsupported in hand",value:c.unsupported.size+" runs",
           explanation:"Runs where the bounded runner explicitly flagged this card as having an unsupported hand action. Results may reflect engine coverage rather than player decisions.",
           examples:examples.filter(e=>c.unsupported.has(e.seed))}
        ]
      };
    }).filter(c=>c.score>=3).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
    if(contenders.length<2)return null;
    return {
      id:"left-unplayed",kind:"diagnostic",title:"Most often left unplayed",
      value:contenders[0].score+" runs",
      chartLabel:"Observed runs without a recorded play",
      explanation:"Limited to cards actually seen in recorded hands or draws. “Unplayed” means not played within these modeled early turns, not never useful; unsupported simulator behavior is a major alternative explanation.",
      contenders,total:valid.length
    };
  }

  function verifiedImpact(replay,lookup){
    if(!replay||typeof replay.scenarios!=="object")return [];
    const games=Object.entries(replay.scenarios).flatMap(([scenario,entry])=>
      (entry.games||[]).map(game=>({scenario,game})));
    // Attributed damage/kill effects must name a reviewed pilot card and
    // carry an explicit typed numeric outcome. Abstract combat is excluded.
    const definitions=[
      {
        id:"direct-player-damage",title:"Most damage to opponents",
        chartLabel:"Verified damage to opposing players",metric:"Damage dealt",
        qualifying:a=>a.actor_seat===0&&Number.isInteger(a.target_seat)&&
          a.target_seat>=1&&a.target_seat<=3&&
          ["reviewed_player_damage","reviewed_direct_player_damage",
           "reviewed_damage_to_player"].includes(a.type)&&
          Number.isFinite(a.fields?.amount)&&a.fields.amount>0,
        measure:a=>a.fields.amount
      },
      {
        id:"creature-kills",title:"Most creature kills",
        chartLabel:"Verified creatures destroyed by named source",metric:"Creature kills",
        qualifying:a=>a.actor_seat===0&&
          (a.type==="reviewed_creature_kill"||
           a.type==="reviewed_removal_resolved")&&
          Number.isInteger(a.fields?.creatures_killed)&&a.fields.creatures_killed>0,
        measure:a=>a.fields.creatures_killed
      },
      {
        id:"permanents-destroyed",title:"Most permanents destroyed",
        chartLabel:"Reviewed permanent destruction by named source",
        metric:"Permanents destroyed",
        qualifying:a=>a.actor_seat===0&&a.type==="reviewed_removal_resolved"&&
          Number.isInteger(a.fields?.destroyed_count)&&a.fields.destroyed_count>0,
        measure:a=>a.fields.destroyed_count
      }
    ];
    const results=[];
    for(const def of definitions){
      const perName=new Map();
      for(const {scenario,game} of games)for(const round of game.rounds||[]){
        (round.actions||[]).forEach((action,eventIndex)=>{
          if(action.fidelity!=="reviewed"||typeof action.card_name!=="string"||
             !lookup(action.card_name)||!def.qualifying(action))return;
          const name=action.card_name,amount=def.measure(action);
          if(!perName.has(name))perName.set(name,{name,total:0,runs:new Set(),examples:[]});
          const c=perName.get(name);
          c.total+=amount;c.runs.add(scenario+":"+game.seed);
          c.examples.push({
            source:"opponent_replay",replay,scenario,gameId:game.id,
            seed:game.seed,turn:round.round,eventIndex,cardName:name,
            amount,description:amount+" "+def.metric.toLowerCase()+
              " · "+scenario+" scenario",focusTopic:"creatures"
          });
        });
      }
      const contenders=[...perName.values()].map(c=>{
        const examples=[...c.examples].sort((a,b)=>b.amount-a.amount||a.seed-b.seed);
        return {name:c.name,card:lookup(c.name),score:c.total,
          scoreLabel:c.total+" "+(def.id==="direct-player-damage"?"damage":"removed"),
          metrics:[
            {id:"impact",label:def.metric,value:String(c.total),
             explanation:"Sum of source-attributed reviewed outcomes in the "+games.length+
               " exported narrated games. This is not the full simulation population.",
             examples},
            {id:"games",label:"Narrated games involved",value:c.runs.size+" / "+games.length,
             explanation:"Count of narrated scenario/seed samples with at least one verified attributed event.",
             examples},
            {id:"max",label:"Largest single event",value:String(Math.max(...examples.map(e=>e.amount))),
             explanation:"Largest individually recorded outcome attributable to this source.",
             examples}
          ]};
      }).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
      // Require actual comparative data rather than making a one-card
      // headline out of an isolated, exceptional event.
      if(contenders.length<2||contenders[0].score<2)continue;
      results.push({
        id:def.id,kind:"impact",title:def.title,
        value:contenders[0].score+" "+(def.id==="direct-player-damage"?"damage":"removed"),
        chartLabel:def.chartLabel,
        explanation:"Only named, reviewed, source-attributed events in "+
          games.length+" narrated samples are counted. These are NOT all "+
          (replay.scenarios?Object.values(replay.scenarios).reduce((n,x)=>n+(x.summary?.seeds||0),0):0)+
          " scenario seeds. Abstract combat cannot identify a damaging or killing card.",
        contenders,total:games.length
      });
    }
    return results;
  }

  return {SUPPORTED_TYPES,isType,isPlayedEvent,usableRuns,seedFacts,
    commonPlayedByType,heldInHand,leftUnplayed,verifiedImpact};
});
