"""Paired-trajectory diagnostic (observational association, not causal effect)."""
import json,statistics
from pathlib import Path
from engine import Table,ARCHETYPES
root=Path(__file__).parent
N=300
rows=[]
for ai,arch in enumerate(ARCHETYPES):
    groups={'early_mana_le_3':[], 'early_mana_ge_5':[], 'early_engine_yes':[], 'early_engine_no':[]}
    for i in range(N):
        p=Table([arch,'midrange','control'],seed=912378+100000*ai+i,interaction=False).run(8).players[1]
        s4,s8=p.stats[3],p.stats[7]
        if s4['mana_sources']<=3:groups['early_mana_le_3'].append(s8['threat'])
        if s4['mana_sources']>=5:groups['early_mana_ge_5'].append(s8['threat'])
        groups['early_engine_yes' if s4['engine_count'] else 'early_engine_no'].append(s8['threat'])
    rows.append({'archetype':arch,**{k:{'n':len(v),'mean_t8_threat':round(statistics.mean(v),2) if v else None} for k,v in groups.items()}})
(root/'snowball_results.json').write_text(json.dumps({'trials_per_archetype':N,'design':'Uninterrupted goldfish; observational grouping by turn-4 state, no intervention','results':rows},indent=2))
print('Saved snowball_results.json')
