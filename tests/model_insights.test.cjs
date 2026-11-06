const assert=require("node:assert/strict");
const {test}=require("node:test");
const {validate}=require("../web/pages/model_insights.js");
const context={deck:"mortarion_current",version:"v-test",total:160,feature_schema:"features-v1"};
function report(){
  return {schema:"gorge-model-insights-v1",status:"validated",deck:"mortarion_current",
    cohort_version:"v-test",feature_schema:"features-v1",
    validation:{strategy:"grouped_held_out",leakage_audit_passed:true,
      feature_coverage_complete:true,outcome_coverage_complete:true,
      n_games:160,n_groups:160,wins:60,losses:100,brier:.18,baseline_brier:.21},
    features:[{feature_id:"card.Sol_Ring.drawn_before_4",label:"Sol Ring drawn by turn 4",
      family:"card",association:"positive",selection_frequency:.76,evidence_status:"held_out"}]};
}
test("validated grouped held-out report can render",()=>{
  const result=validate(report(),context);
  assert.equal(result.ready,true);assert.equal(result.features.length,1);
});
test("reject partial cohort, smaller sample or misaligned fingerprint",()=>{
  for(const edit of [
    p=>p.cohort_version="stale",
    p=>p.validation.n_games=25,
    p=>p.validation.n_groups=10,
    p=>p.validation.wins=3,
    p=>p.feature_schema="old",
    p=>p.validation.leakage_audit_passed=false,
    p=>p.validation.feature_coverage_complete=false,
    p=>p.validation.strategy="in_sample",
    p=>p.status="experimental",
  ]) {const p=report();edit(p);assert.equal(validate(p,context).ready,false);}
});
test("reject duplicate, post-outcome or unaudited feature",()=>{
 for(const edit of [
   p=>p.features[0].feature_id="won",
   p=>p.features[0].selection_frequency=1.1,
   p=>p.features[0].evidence_status="in_sample",
   p=>p.features.push({...p.features[0]}),
 ]){const p=report();edit(p);assert.equal(validate(p,context).ready,false);}
});
