/* Commander bracket evidence, independent of simulation execution.
 * Rule-based estimate, not an official adjudication or simulated win-rate.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.CommanderBrackets=api;
})(typeof window!=="undefined"?window:null,function(){
  "use strict";
  function normalize(name){return String(name||"").normalize("NFKC").trim().toLowerCase();}
  function assess(entries,cards,registry){
    if(!Array.isArray(entries)||!registry||!Array.isArray(registry.names))
      return {status:"unavailable",reason:"Card list or Game Changers reference is unavailable."};
    const changers=new Set(registry.names.map(normalize));
    const matches=[],unknown=[],tutors=[],extraTurns=[],landDenial=[];
    let total=0;
    for(const item of entries){
      const qty=Number(item.qty??item.quantity);
      if(!Number.isInteger(qty)||qty<1)continue;
      total+=qty;
      const card=cards[item.oracle_id]||null;
      const name=item.name||card?.name||"Unknown card";
      if(!card){unknown.push(name);continue;}
      const aliases=[name,card.name,...(card.face_names||[])].map(normalize);
      if(aliases.some(alias=>changers.has(alias)))matches.push({name,qty,oracle_id:item.oracle_id});
      const rules=String(card.oracle_text||"");
      if(/search your library for/i.test(rules)&&!/basic land card/i.test(rules))
        tutors.push(name);
      if(/take an extra turn|takes an extra turn/i.test(rules))extraTurns.push(name);
      if(/destroy all lands|exile all lands|return all lands to their owners/i.test(rules))
        landDenial.push(name);
    }
    const count=matches.reduce((sum,x)=>sum+x.qty,0);
    const floor=count>3?4:count>0?3:2;
    const estimate=landDenial.length?Math.max(4,floor):floor;
    return {
      status:total===100&&unknown.length===0?"provisional":"incomplete",
      estimated_bracket:estimate,minimum_by_game_changers:floor,
      count, matches, unknown, total, tutors:[...new Set(tutors)],
      extraTurns:[...new Set(extraTurns)],landDenial:[...new Set(landDenial)],
      source:registry.source,reference_updated:registry.updated,
      caveat:"Provisional rules-text/decklist screening only: combinations, intentional strategies, actual win speed, playgroup expectations and cEDH intent require review. Neither simulations nor early-game win probabilities are inferred."
    };
  }

  // Game-performance evidence must be explicitly complete, revision-matched,
  // and include modeled opponents and win conditions. Six-turn bounded runs
  // and opening-hand observations are NOT qualifying performance samples.
  function performanceEvidence(runs,deckSha){
    if(!Array.isArray(runs)||!deckSha)return null;
    const valid=runs.filter(run=>run&&run.deck_sha256===deckSha&&
      run.mode==="complete_multiplayer_game"&&run.game_complete===true&&
      run.opponents_modeled===true&&run.win_conditions_modeled===true&&
      Number.isInteger(run.winning_turn)&&run.winning_turn>0&&
      typeof run.won==="boolean");
    if(valid.length<30)return null;
    const sorted=valid.map(run=>run.winning_turn).sort((a,b)=>a-b);
    const wins=valid.filter(run=>run.won).length;
    const median=sorted[Math.floor((sorted.length-1)/2)];
    const early=valid.filter(run=>run.won&&run.winning_turn<=5).length;
    return {sample:valid.length,wins,win_rate:Math.round(100*wins/valid.length),
      median_finish_turn:median,early_wins:early,
      note:"Complete modeled four-player games, matched to this exact deck revision. Performance depends on opponent selection and pilot fidelity."};
  }
  function combineEvidence(cardResult,runs,deckSha){
    if(!cardResult||cardResult.status==="unavailable")return cardResult;
    const performance=performanceEvidence(runs,deckSha);
    if(!performance)return {...cardResult,evidence_mode:"cards_only",performance:null};
    // A completed-game dataset supplies additional evidence, but game speed
    // alone cannot override Wizards' intent/strategy requirements or determine
    // an official bracket. Preserve hard Game Changer minimum.
    let suggested=cardResult.estimated_bracket;
    if(performance.early_wins/performance.sample>=0.20)
      suggested=Math.max(suggested,4);
    return {...cardResult,estimated_bracket:suggested,
      evidence_mode:"cards_and_games",performance};
  }
  return {assess,normalize,performanceEvidence,combineEvidence};
});
