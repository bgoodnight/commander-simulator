/* Results Insights: deterministic aggregation and carefully scoped interpretation.
 * Every displayed statistic comes from pinned Python observation records.
 * This is NOT gameplay, spell castability, goldfishing, or win-rate analysis.
 * Pure functions are also tested in Node by tests/pages_insights.test.cjs.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.DeckInsights=api;
})(typeof window!=="undefined"?window:null,function(){
  "use strict";
  const BASIC=new Set(["Plains","Island","Swamp","Mountain","Forest","Wastes",
    "Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp",
    "Snow-Covered Mountain","Snow-Covered Forest","Command Tower"]);
  const average=values=>values.length?values.reduce((sum,x)=>sum+x,0)/values.length:0;
  const round=(x,d=1)=>Number(x.toFixed(d));
  const pct=(part,total)=>total?Math.round(100*part/total):0;
  function sources(t){
    if(Array.isArray(t.modeled_sources))return t.modeled_sources.length;
    return Math.max(0,Number(t.battlefield_count)||0);
  }
  const candidateCount=t=>Array.isArray(t.candidate_if_supported)?
    t.candidate_if_supported.length:0;
  function summarize(records){
    const runs=Object.values(records||{}).filter(r=>r&&r.mode==="observation"&&
      Array.isArray(r.trace)&&r.trace.length>=6&&Array.isArray(r.opening_hand));
    if(!runs.length)return null;
    // Treat each stored seed as one observed sample, not an independent
    // or representative Monte Carlo run. Ignore malformed trace slots.
    const seeds=runs.map(r=>String(r.seed));
    const opening=runs.map(r=>r.opening_hand.filter(n=>BASIC.has(n)).length);
    const sourcesByTurn=Array.from({length:6},(_,i)=>runs.map(r=>sources(r.trace[i])));
    const candidatesByTurn=Array.from({length:6},(_,i)=>runs.map(r=>candidateCount(r.trace[i])));
    const landByTurn=Array.from({length:6},(_,i)=>runs.map(r=>r.trace[i].land_played?1:0));
    const count=runs.length;
    const t3=sourcesByTurn[2],t4=sourcesByTurn[3];
    const earlyLand=opening.filter(x=>x>=2&&x<=5).length;
    const t3Enough=t3.filter(x=>x>=3).length;
    const t4Candidate=candidatesByTurn[3].filter(x=>x>=1).length;
    const detail=Object.fromEntries(runs.map(r=>[String(r.seed),r]));
    const meanSources=sourcesByTurn.map(row=>round(average(row),2));
    const candidateRate=candidatesByTurn.map(row=>pct(row.filter(x=>x>0).length,count));
    const landRate=landByTurn.map(row=>pct(row.filter(Boolean).length,count));
    const categories=[
      {label:"0",min:0,max:0},{label:"1",min:1,max:1},
      {label:"2",min:2,max:2},{label:"3",min:3,max:3},
      {label:"4",min:4,max:4},{label:"5+",min:5,max:Infinity}
    ];
    const openingGroups=categories.map(bucket=>({
      label:bucket.label,
      value:opening.filter(x=>x>=bucket.min&&x<=bucket.max).length,
      seeds:seeds.filter((_,i)=>opening[i]>=bucket.min&&opening[i]<=bucket.max)
    }));
    const turn3Groups=Array.from({length:7},(_,i)=>({
      label:String(i===6?"6+":i),value:t3.filter(x=>i===6?x>=6:x===i).length,
      seeds:seeds.filter((_,j)=>i===6?t3[j]>=6:t3[j]===i)
    }));
    const candidateGroups=candidatesByTurn.map((row,i)=>({
      label:"T"+(i+1),value:pct(row.filter(x=>x>0).length,count),
      numerator:row.filter(x=>x>0).length,
      seeds:seeds.filter((_,j)=>row[j]>0),
      absent:seeds.filter((_,j)=>row[j]===0),
      mean:round(average(row),2)
    }));
    return {
      n:count,seeds,runsBySeed:detail,opening,openingGroups,turn3Groups,candidateGroups,
      meanSources,candidateRate,landRate,sourcesByTurn,candidatesByTurn,
      metrics:{
        earlyLand:{count:earlyLand,pct:pct(earlyLand,count)},
        t3Sources:{count:t3Enough,pct:pct(t3Enough,count),mean:round(average(t3))},
        t4Candidate:{count:t4Candidate,pct:pct(t4Candidate,count)}
      },
      provenance:"Fixed cached observations: keep-seven hands, first modeled basic/Command Tower land, mana-value-only candidates; no spells cast."
    };
  }
  function findings(result){
    if(!result)return [];
    const n=result.n,m=result.metrics;
    const opening=m.earlyLand,t3=m.t3Sources,available=m.t4Candidate;
    const intro={
      title:"How consistently do the opening hands contain modeled lands?",
      summary:`${opening.count} of ${n} archived opening hands (${opening.pct}%) contain 2–5 modeled basic/Command Tower lands.`,
      meaning:opening.count===n?
        "All sampled opening hands meet this narrow land-count screen. This does not establish they are good keeps.":
        opening.count===0?
        "None of these sampled hands meet this narrow land-count screen. Check the land composition and the unmodeled nonbasics before changing the deck.":
        "Some sampled hands fall outside the 2–5 modeled-land range. Inspect individual hands before deciding whether that reflects a deck problem.",
      caveat:"Other nonbasic lands and hand quality are excluded; this is not a mulligan recommendation."
    };
    const resources={
      title:"Do modeled mana sources develop by turn three?",
      summary:`${t3.count} of ${n} archived runs (${t3.pct}%) have at least three modeled sources by turn 3; mean: ${t3.mean}.`,
      meaning:t3.count===n?
        "Every archived run reached this modeled-source checkpoint. Actual mana production can differ because other lands and abilities are excluded.":
        t3.count===0?
        "None of the archived runs reached three modeled sources by turn three. Investigate source coverage before judging the deck's real speed.":
        "The archived runs vary in early modeled-source development. Select bars to see which seeds reached the checkpoint.",
      caveat:"This measures a basic-land/Command Tower policy—not real mana fixing, ramp or spell casting."
    };
    const choices={
      title:"When do mana-value candidates appear?",
      summary:`${available.count} of ${n} archived runs (${available.pct}%) have at least one mana-value candidate on turn 4.`,
      meaning:available.count===n?
        "Every archived run had an inexpensive-enough nonland card on turn four. This is not evidence that the spell can legally be cast.":
        available.count===0?
        "None of the archived runs had a card passing this limited turn-four mana-value screen. Check actual costs and mana rules before drawing a conclusion.":
        "Candidate availability differs across archived draws. Select a turn to inspect which seeds passed this limited screen.",
      caveat:"The candidate screen does not check colors, timing, targets, spell resolution or opponents."
    };
    return [intro,resources,choices];
  }
  // Conservative, inspectable text signals; a mention is not an executable ability.
  const signals=[
    {id:"spells",label:"Instants & sorceries",kind:"Card type",matches:c=>/\b(Instant|Sorcery)\b/i.test(c.type_line||"")},
    {id:"tokens",label:"Token creation",kind:"Rules-text pattern",matches:c=>/\bcreate\b[^.\n]*\btokens?\b/i.test(c.oracle_text||"")},
    {id:"graveyard",label:"Graveyard",kind:"Rules-text mention",matches:c=>/\bgraveyards?\b/i.test(c.oracle_text||"")},
    {id:"draw",label:"Card draw",kind:"Rules-text pattern",matches:c=>/\bdraws?\b[^.\n]*\bcards?\b/i.test(c.oracle_text||"")},
    {id:"sacrifice",label:"Sacrifice",kind:"Rules-text mention",matches:c=>/\bsacrific(?:e|es|ed|ing)\b/i.test(c.oracle_text||"")},
    {id:"search",label:"Library search",kind:"Rules-text pattern",matches:c=>/\bsearch\b[^.\n]*\blibrary\b/i.test(c.oracle_text||"")}
  ];
  function creatureSubtypes(card){
    const types=new Set();
    for(const face of (card.type_line||"").split(" // ")){
      const parts=face.split(/\s[—–]\s/);
      if(parts.length<2||!/\bCreature\b/i.test(parts[0]))continue;
      for(const word of parts[1].match(/[A-Za-z][A-Za-z'-]*/g)||[])types.add(word);
    }
    return [...types];
  }
  function textMentionsSubtype(card,subtype){
    const escaped=subtype.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
    return new RegExp("\\b"+escaped+"s?\\b","i").test(card.oracle_text||"");
  }
  function themes(entries,cardById,records,commander){
    const library=(entries||[]).filter(e=>e.zone!=="Commander"&&e.qty>0)
      .map(e=>({entry:e,card:cardById[e.oracle_id]})).filter(x=>x.card);
    const subtypes=new Set();
    for(const x of library)for(const subtype of creatureSubtypes(x.card))subtypes.add(subtype);
    if(commander)for(const subtype of creatureSubtypes(commander))subtypes.add(subtype);
    const groups=[...signals,...[...subtypes].map(subtype=>({
      id:"subtype:"+subtype.toLowerCase(),label:subtype,kind:"Creature subtype or rules-text mention",
      matches:c=>creatureSubtypes(c).some(x=>x.toLowerCase()===subtype.toLowerCase())||textMentionsSubtype(c,subtype)
    }))];
    const validRuns=Object.values(records||{}).filter(r=>r&&r.mode==="observation"&&
      Array.isArray(r.opening_hand)&&Array.isArray(r.trace)&&r.trace.length>=6&&
      r.trace.slice(0,6).every((t,i)=>t&&t.turn===i+1&&Object.hasOwn(t,"drawn")&&
        (typeof t.drawn==="string"||t.drawn===null)));
    return groups.map(group=>{
      const matches=library.filter(x=>group.matches(x.card));
      const copies=matches.reduce((n,x)=>n+x.entry.qty,0);
      const names=new Set(matches.map(x=>x.entry.name.toLowerCase()));
      const first=validRuns.map(r=>{
        if(r.opening_hand.some(n=>typeof n==="string"&&names.has(n.toLowerCase())))return 0;
        const index=r.trace.slice(0,6).findIndex(t=>typeof t.drawn==="string"&&names.has(t.drawn.toLowerCase()));
        return index<0?null:index+1;
      });
      return {id:group.id,label:group.label,kind:group.kind,copies,
        cards:matches.map(x=>({name:x.entry.name,qty:x.entry.qty})),
        commanderMatch:!!commander&&(group.matches(commander)||(group.id==="spells"&&/\binstant\b[^.\n]*\bsorcer(?:y|ies)\b/i.test(commander.oracle_text||""))),sample:validRuns.length,
        opening:first.filter(t=>t===0).length,
        byTurn3:first.filter(t=>t!==null&&t<=3).length,
        byTurn6:first.filter(t=>t!==null&&t<=6).length};
    }).filter(g=>g.copies>=3).sort((a,b)=>Number(b.commanderMatch)-Number(a.commanderMatch)||b.copies-a.copies||a.label.localeCompare(b.label));
  }
  function sourceTimeline(summary){
    if(!summary)return [];
    return summary.meanSources.map((mean,i)=>({turn:i+1,mean,
      runs:summary.seeds.map(seed=>{
        const row=summary.runsBySeed[seed].trace[i];
        return {seed,count:sources(row),cards:Array.isArray(row.modeled_sources)?
          row.modeled_sources.map(source=>source.card).filter(name=>typeof name==="string"):[]};
      })}));
  }
  function themeTimelines(groups,records){
    const runs=Object.values(records||{}).filter(r=>r&&r.mode==="observation"&&
      Array.isArray(r.opening_hand)&&Array.isArray(r.trace)&&r.trace.length>=6&&
      r.trace.slice(0,6).every((row,i)=>row&&row.turn===i+1&&
        Object.prototype.hasOwnProperty.call(row,"drawn")&&
        (typeof row.drawn==="string"||row.drawn===null)));
    if(!runs.length)return [];
    return (groups||[]).slice(0,3).map(group=>{
      const names=new Set(group.cards.map(card=>card.name.toLowerCase()));
      const first=runs.map(run=>{
        const initial=run.opening_hand.find(name=>typeof name==="string"&&names.has(name.toLowerCase()));
        if(initial)return {seed:String(run.seed),turn:0,card:initial};
        const index=run.trace.slice(0,6).findIndex(row=>typeof row.drawn==="string"&&names.has(row.drawn.toLowerCase()));
        return {seed:String(run.seed),turn:index<0?null:index+1,card:index<0?null:run.trace[index].drawn};
      });
      return {id:group.id,label:group.label,kind:group.kind,copies:group.copies,sample:runs.length,
        points:Array.from({length:7},(_,turn)=>{
          const matching=first.filter(item=>item.turn!==null&&item.turn<=turn);
          return {turn,count:matching.length,pct:pct(matching.length,runs.length),matches:matching};
        })};
    });
  }
  const PROGRESS_EVENTS=new Set(["land_play","creature_resolved","artifact_resolved",
    "tutor_resolved","token_spell_resolved","reviewed_trigger_resolved"]);
  function quietTurns(runs,deckKey,deckHash){
    if(!Array.isArray(runs)||!runs.length)throw Error("Select one or more individual run records.");
    const seeds=new Set(),first=runs[0],horizon=first?.events?.length,policy=first?.mulligan?.policy;
    if(!Number.isInteger(horizon)||horizon<2||horizon>10||!policy)throw Error("Runs need at least two turns and a mulligan policy.");
    for(const run of runs){
      if(run?.mode!=="bounded_authoritative_early_actions"||run.deck_key!==deckKey||run.deck_sha256!==deckHash)
        throw Error("Every run must match the selected built-in deck and its exact version.");
      if(!Number.isInteger(run.seed)||seeds.has(run.seed))throw Error("Each run needs a distinct integer seed.");
      seeds.add(run.seed);
      if(run.mulligan?.policy!==policy||!Array.isArray(run.events)||run.events.length!==horizon||
          !Array.isArray(run.state_snapshots)||run.state_snapshots.length!==horizon)
        throw Error("Runs must have the same turn count and mulligan policy, with complete snapshots.");
      run.events.forEach((row,i)=>{
        if(row?.turn!==i+1||!Array.isArray(row.events)||!Array.isArray(row.unsupported_cards_in_hand)||
           !Number.isFinite(row.land_count)||!Number.isFinite(row.hand_size)||
           run.state_snapshots[i]?.turn!==i+1||!Array.isArray(run.state_snapshots[i].hand)||
           !Array.isArray(run.state_snapshots[i].battlefield))throw Error("A turn or snapshot is incomplete.");
      });
    }
    return Array.from({length:horizon-1},(_,i)=>{
      const turn=i+2;
      const quiet=runs.filter(run=>[turn-2,turn-1].every(index=>
        !run.events[index].events.some(event=>PROGRESS_EVENTS.has(event.type))));
      const mean=(xs,fn)=>xs.length?xs.reduce((sum,x)=>sum+fn(x),0)/xs.length:0;
      const unknown=r=>[...new Set(r.events.slice(turn-2,turn).flatMap(row=>row.unsupported_cards_in_hand))];
      const lands=mean(quiet,r=>r.events[turn-1].land_count),
        unsupported=mean(quiet,r=>unknown(r).length);
      const examples=[...quiet].sort((a,b)=>{
        const distance=r=>Math.abs(r.events[turn-1].land_count-lands)+
          Math.abs(unknown(r).length-unsupported);
        return distance(a)-distance(b)||a.seed-b.seed;
      }).map(run=>({seed:run.seed,turn,landCount:run.events[turn-1].land_count,
        hand:run.state_snapshots[turn-1].hand,battlefield:run.state_snapshots[turn-1].battlefield,
        unsupported:unknown(run),
        events:run.events.slice(turn-2,turn).map(row=>({turn:row.turn,events:row.events}))}));
      return {turn,total:runs.length,count:quiet.length,pct:pct(quiet.length,runs.length),
        uncertain:quiet.filter(r=>unknown(r).length>0).length,
        nonquiet:runs.filter(run=>!quiet.includes(run)).map(run=>({seed:run.seed,hand:run.state_snapshots[turn-1].hand})),
        examples};
    });
  }
  return {summarize,findings,pct,round,sources,candidateCount,themes,sourceTimeline,themeTimelines,quietTurns};
});
