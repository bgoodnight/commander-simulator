"""Small runtime check only: diverging stochastic trajectories are not a paired benchmark."""
import json,statistics,time
from pathlib import Path
from adapter import V9Table
from table import CentralTable
ROOT=Path(__file__).resolve().parent
samples={}
for name,factory in [
 ('v8',lambda seed:CentralTable(seed=seed,trace=False)),
 ('v9_seat_0',lambda seed:V9Table(seed=seed,trace=False)),
 ('v9_seat_2',lambda seed:V9Table(['aggro','control','magnus','combo'],seed=seed,trace=False))]:
 times=[]
 for seed in range(40):
  a=time.perf_counter();t=factory(seed).run(10);times.append((time.perf_counter()-a)*1000)
  assert t.world.consistent()
 samples[name]={'n':len(times),'median_ms':round(statistics.median(times),3),
               'mean_ms':round(statistics.mean(times),3),'maximum_ms':round(max(times),3)}
print(json.dumps(samples,indent=2))
(ROOT/'benchmark_diagnostic.json').write_text(json.dumps(samples,indent=2)+'\n')
