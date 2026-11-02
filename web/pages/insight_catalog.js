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

  // A held-hand opportunity is defined by an observed opening hand, draw,
  // or retained hand snapshot. A same-turn cast counts as ZERO held rounds.
  // Count each card name once per end-of-turn snapshot; individual copies
  // cannot be reconstructed from this abbreviated replay format.
  function heldInHand(runs,lookup){
    const valid=usableRuns(runs);if(valid.length<2)return null;
    const summaries=new Map();
    const playActions=new Set([...HAND_CASTS,
      "reviewed_common_spell_resolved","reviewed_zone_spell_resolved"]);
    const adjustedWeight=n=>n/(n+10); // Reliability prior: 10 pseudo-observations.
    const precision=n=>Number(n.toFixed(2));
    const duration=n=>Number(n.toFixed(1)).toString();
    const bySeed=(a,b)=>a.seed-b.seed||a.turn-b.turn||
      (a.eventIndex??-1)-(b.eventIndex??-1);
    function add(name){
      if(!summaries.has(name))summaries.set(name,{
        name,card:lookup(name),seen:new Set(),drawn:new Set(),
        held:new Map(),previews:[],played:[],seenEvidence:new Map(),drawEvidence:new Map()
      });
      return summaries.get(name);
    }
    for(const run of valid){
      const facts=seedFacts(run);
      const drawn=new Set(cardsByName(run.mulligan?.opening_hand));
      const drawing=new Map();
      for(const name of drawn){
        drawing.set(name,{seed:run.seed,turn:run.events[0].turn,
          run,source:"bounded",cardName:name,eventIndex:null,
          focusTopic:"hand",description:"In the kept opening hand"});
      }
      const plays=new Map();
      for(const row of run.events){
        const namedCasts=new Set((row.events||[])
          .filter(event=>HAND_CASTS.has(event.type)&&typeof event.card==="string")
          .map(event=>event.card));
        (row.events||[]).forEach((event,eventIndex)=>{
          const name=event.card;
          if(typeof name!=="string")return;
          if(event.type==="draw"){
            drawn.add(name);
            if(!drawing.has(name))drawing.set(name,{
              seed:run.seed,turn:row.turn,run,source:"bounded",
              cardName:name,eventIndex,focusTopic:"hand",
              description:"Drawn on turn "+row.turn
            });
          }
          if(!playActions.has(event.type))return;
          // When a named cast and a fallback resolution occur together,
          // they are one recorded play, not two.
          if(!HAND_CASTS.has(event.type)&&namedCasts.has(name))return;
          if(!plays.has(name))plays.set(name,[]);
          plays.get(name).push({
            seed:run.seed,turn:row.turn,run,source:"bounded",
            cardName:name,eventIndex,focusTopic:"hand",
            description:"Recorded "+event.type.replaceAll("_"," ")+" on turn "+row.turn
          });
        });
      }
      const seen=new Set([...drawn,...facts.handTurns.keys()]);
      // Do not treat an unrelated graveyard recast as proof this spell
      // was observed in hand during the same simulated horizon.
      for(const name of seen){
        const card=lookup(name);
        if(!card||isType(card,"Land"))continue;
        const c=add(name),held=facts.handTurns.get(name)||[];
        c.seen.add(run.seed);
        c.held.set(run.seed,held);
        if(drawn.has(name)){
          c.drawn.add(run.seed);
          c.drawEvidence.set(run.seed,drawing.get(name));
        }
        c.previews.push(...facts.previewTurns.get(name)||[]);
        c.played.push(...plays.get(name)||[]);
        c.seenEvidence.set(run.seed,
          held[0]||drawing.get(name)||plays.get(name)?.[0]);
      }
    }
    const minRuns=valid.length>=40?Math.max(3,Math.ceil(valid.length*0.05)):2;
    const contenders=[...summaries.values()].map(c=>{
      const n=c.seen.size,heldTurns=[...c.held.values()].flat();
      const total=heldTurns.length;
      const durations=[...c.held.values()].map(items=>items.length);
      // Include zero-hand-round games when observed in opening hand or
      // a draw but played immediately, rather than conditioning on a stall.
      const typical=median(durations);
      const average=total/n;
      const adjusted=precision(average*adjustedWeight(n));
      const ordered=[...c.held.entries()].sort((a,b)=>a[0]-b[0]);
      const byDuration=ordered.map(([seed,items])=>({
        seed,length:items.length,
        sample:items.at(-1)||c.seenEvidence.get(seed)
      })).filter(item=>item.sample);
      const nearMedian=[...byDuration].sort((a,b)=>
        Math.abs(a.length-typical)-Math.abs(b.length-typical)||
        a.seed-b.seed).map(item=>item.sample);
      const allHeld=[...heldTurns].sort(bySeed);
      const drawnExamples=[...c.drawn].sort((a,b)=>a-b)
        .map(seed=>c.drawEvidence.get(seed)).filter(Boolean);
      const allPlays=[...c.played].sort(bySeed);
      const previews=[...c.previews].sort(bySeed);
      const mostHeld=[...byDuration].sort((a,b)=>b.length-a.length||a.seed-b.seed)
        .map(item=>item.sample);
      const stillHeld=[...c.held.entries()]
        .filter(([,items])=>items.some(x=>x.turn===
          items[0].run.events[items[0].run.events.length-1].turn))
        .map(([,items])=>items.at(-1)).sort(bySeed);
      return {
        name:c.name,card:c.card,score:average,observedRuns:n,medianRounds:typical,
        scoreLabel:average.toFixed(2)+" mean rounds · "+n+" seen",
        viewScores:{mean:average,median:typical,held:total,adjusted,payable:previews.length},
        viewLabels:{
          mean:average.toFixed(2)+" mean rounds · "+n+" games seen",
          median:duration(typical)+" median rounds · "+n+" games seen",
          held:total+" rounds · "+n+" games seen",
          adjusted:adjusted.toFixed(2)+" adjusted · "+n+" games seen",
          payable:previews.length+" cost previews"
        },
        metrics:[
          {id:"median",label:"Median rounds held",value:duration(typical),
           explanation:"Median number of end-of-turn snapshots in hand per game where this card was observed ("+n+" games). Includes zero for cards drawn and played before the end-of-turn snapshot. This is not continuous real-time duration.",
           examples:nearMedian},
          {id:"held",label:"Rounds held",value:String(total),
           explanation:"Total recorded end-of-turn hand snapshots with this card across "+n+" observed games. Each game/turn counts once per card name, even if multiple copies were present.",
           examples:allHeld},
          {id:"drawn",label:"Games drawn",value:c.drawn.size+" / "+valid.length,
           explanation:"Distinct games where the card was in the kept opening hand or appeared in a recorded draw. Games where it appeared in hand without a recorded draw can contribute to the median but not this count.",
           examples:drawnExamples},
          {id:"played",label:"Times played",value:String(allPlays.length),
           explanation:"Named recorded spell casts (and fallback resolutions when no corresponding cast event exists), counting repeat casts separately. A zero can reflect unsupported simulator behavior, not necessarily an unplayable card.",
           examples:allPlays},
          {id:"average",label:"Average rounds held",value:average.toFixed(2),
           explanation:"Total rounds held divided by "+n+" games in which the card was observed. Games with no end-of-turn retention contribute zero.",
           examples:nearMedian},
          {id:"adjusted",label:"Adjusted score",value:adjusted.toFixed(2),
           explanation:"Exploratory reliability-adjusted persistence: (rounds held / games seen) × (games seen / (games seen + 10)). The +10 is a configurable evidence penalty, not a Magic rule or statistical confidence interval.",
           examples:mostHeld},
          {id:"payable",label:"Cost-payable previews",value:String(previews.length),
           explanation:"Read-only post-action source-paid printed-cost previews while this card stayed in hand. This does not establish legal timing, targets, or a missed casting opportunity. Supported spells often have no such preview.",
           examples:previews},
          {id:"last",label:"Still held at horizon",value:String(stillHeld.length),
           explanation:"Games with the card in the final retained end-of-turn hand. This is not necessarily a bad result; instants and interaction may be held deliberately.",
           examples:stillHeld}
        ]
      };
    }).filter(c=>c.viewScores.held>=2&&c.viewScores.median>0&&
      c.observedRuns>=minRuns)
      .sort((a,b)=>b.score-a.score||
        b.viewScores.adjusted-a.viewScores.adjusted||
        b.viewScores.held-a.viewScores.held||
        a.name.localeCompare(b.name));
    if(contenders.length<2)return null;
    const payment=contenders.some(c=>c.viewScores.payable>0);
    return {
      id:"held-in-hand",kind:"diagnostic",title:"Median turns held",
      value:duration(contenders[0].medianRounds)+" turns",
      headlineDetail:duration(contenders[0].medianRounds)+
        " median rounds held · "+contenders[0].observedRuns+" games seen",
      chartLabel:"Mean end-of-turn hand rounds per observed game",
      explanation:"The tile reports the median rounds held for the top-ranked card, while the graph ranks by mean rounds held per game where the card was seen. Mean preserves more differences between cards than the median. Immediate plays contribute zero; low-sample cards are filtered. These are not assessments of card quality or missed legal casts.",
      views:[
        {id:"mean",label:"Mean rounds",chartLabel:"Mean rounds held when seen"},
        {id:"median",label:"Median rounds",chartLabel:"Median rounds held when seen"},
        {id:"held",label:"Total rounds",chartLabel:"All recorded rounds held"},
        {id:"adjusted",label:"Adjusted score",
          chartLabel:"Reliability-adjusted mean rounds held",
          formula:"(Total rounds held ÷ Games seen) × (Games seen ÷ (Games seen + 10))",
          explanation:"This optional heuristic downweights cards seen in few games. The 10 is an evidence-penalty constant; it is not a probability, win-rate estimate, or Magic rule."},
        ...(payment?[{id:"payable",label:"Cost-payable",
          chartLabel:"Post-action printed-cost payment previews while held"}]:[])
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
