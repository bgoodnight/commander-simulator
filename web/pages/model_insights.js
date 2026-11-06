/* Optional cohort-verified modeling insights. Never infer scores from UI pages. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.GorgeModelInsights=api;
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const SCHEMA="gorge-model-insights-v1";
  const PROHIBITED=new Set(["seed","outcome","winner_seat","won","source_sha256","game_id","status","future_turns","game_turns"]);
  const int=x=>Number.isSafeInteger(x)&&x>=0;
  function validate(payload,context){
    if(!payload||payload.schema!==SCHEMA||payload.status!=="validated"||
       !context||typeof context.deck!=="string"||!context.version||
       payload.deck!==context.deck||payload.cohort_version!==context.version||
       payload.feature_schema!==context.feature_schema&&context.feature_schema!==undefined)
      return {ready:false,reason:"Model report or cohort version unavailable"};
    const quality=payload.validation;
    if(!quality||quality.strategy!=="grouped_held_out"||
       quality.leakage_audit_passed!==true||
       quality.feature_coverage_complete!==true||
       quality.outcome_coverage_complete!==true||
       !int(quality.n_games)||quality.n_games!==context.total||
       !int(quality.n_groups)||quality.n_groups<100||
       !int(quality.wins)||!int(quality.losses)||
       Math.min(quality.wins,quality.losses)<20||
       quality.wins+quality.losses>quality.n_games ||
       !Number.isFinite(quality.brier)||quality.brier<0||quality.brier>1||
       !Number.isFinite(quality.baseline_brier)||quality.baseline_brier<0||quality.baseline_brier>1||
       !Array.isArray(payload.features))
      return {ready:false,reason:"Model validation or sample coverage incomplete"};
    const ids=new Set();
    const features=[];
    for(const item of payload.features){
      if(!item||typeof item.feature_id!=="string"||!item.feature_id||
         PROHIBITED.has(item.feature_id)||ids.has(item.feature_id)||
         typeof item.label!=="string"||!item.label.trim()||
         !["card","opening_hand","resource","opponent","interaction","timing","board"].includes(item.family)||
         !Number.isFinite(item.selection_frequency)||item.selection_frequency<0||
         item.selection_frequency>1||
         typeof item.association!=="string"||
         !["positive","negative","nonmonotonic"].includes(item.association)||
         item.evidence_status!=="held_out")
        return {ready:false,reason:"Incomplete or invalid predictor evidence"};
      ids.add(item.feature_id);
      features.push(item);
    }
    return {ready:true,features:features.slice(0,12),quality};
  }
  function render(target,payload,context){
    if(!target)return false;
    const checked=validate(payload,context);
    target.replaceChildren();
    if(!checked.ready){target.hidden=true;return false;}
    const make=(tag,cls,text)=>{
      const node=target.ownerDocument.createElement(tag);
      if(cls)node.className=cls;
      if(text!==undefined)node.textContent=text;
      return node;
    };
    target.hidden=false;
    const heading=make("h3","","Modeling insights");
    const method=make("p","micro","Exploratory associations · grouped held-out validation · "+checked.quality.n_games+" games");
    const scores=make("p","micro","Held-out Brier score "+checked.quality.brier.toFixed(3)+
      " · opponent-only baseline "+checked.quality.baseline_brier.toFixed(3));
    const notice=make("p","micro","Associations are predictive, not causal. Card swaps require independent simulations.");
    target.append(heading,method,scores,notice);
    const list=make("div","board-grid");
    checked.features.forEach(item=>{
      const card=make("article","panel");
      card.append(make("h4","",item.label));
      card.append(make("p","micro",item.family+" · "+item.association+
        " association · selected in "+Math.round(100*item.selection_frequency)+"% of resamples"));
      list.append(card);
    });
    target.append(list);
    return true;
  }
  return {validate,render,SCHEMA};
});
