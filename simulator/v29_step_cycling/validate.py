"""Canonical deck conservation and timing diagnostics; not a deck-strength study."""
import importlib.util,json,statistics,time
from pathlib import Path
from step_cycling import StepCyclingTable
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',ROOT.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
start=time.perf_counter();stops=[]
for seat in range(4):
 for seed in range(50):
  kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
  t=StepCyclingTable(kinds,seed=seed).run(12);h.check(t)
  if t.safety_stop:stops.append([seat,seed,t.safety_stop])
 print('seat',seat,'complete',flush=True)
elapsed=round(time.perf_counter()-start,3);samples=[]
for seed in range(12):
 start=time.perf_counter();StepCyclingTable(seed=seed).run(8);samples.append((time.perf_counter()-start)*1000)
d={'deck':'magnus_thousand_sons_v1_13_budget.txt','games':200,'rounds':12,'safety_stops':stops,'elapsed_seconds':elapsed,'benchmark_games':12,'benchmark_rounds':8,'median_ms':round(statistics.median(samples),3),'limitations':'Cycling triggers on the cycled card itself, ordinary cycling, color-changing effects, simultaneous entry and many effects remain unsupported.'}
(ROOT/'validation_results.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d),flush=True)
if stops:raise RuntimeError('Safety stops')
