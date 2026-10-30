"""All-seat conservation sweep and exploratory runtime comparison."""
import importlib.util, json, statistics, time
from pathlib import Path
from tutor_table import TutorTable
from channel_table import ChannelTable
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',ROOT.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
start=time.perf_counter();stops=[];searches=0
for seat in range(4):
 for seed in range(50):
  kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
  t=TutorTable(kinds,seed=seed).run(12);h.check(t);searches+=len(t.tutor_events)
  if t.safety_stop:stops.append([seat,seed,t.safety_stop])
 print('seat',seat,'complete',flush=True)
elapsed=round(time.perf_counter()-start,3);times={}
for cls in (ChannelTable,TutorTable):
 samples=[]
 for seed in range(12):
  start=time.perf_counter();cls(seed=seed).run(8);samples.append((time.perf_counter()-start)*1000)
 times[cls.__name__]=round(statistics.median(samples),3)
d={'deck':'historical Magnus v1.6 fixture','games':200,'rounds':12,'safety_stops':stops,'tutor_searches':searches,'elapsed_seconds':elapsed,'median_ms_8_rounds_12_samples':times}
(ROOT/'validation_results.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d),flush=True)
if stops:raise RuntimeError('Safety stops')
