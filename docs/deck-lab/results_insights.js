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
  return {summarize,findings,pct,round,sources,candidateCount};
});
