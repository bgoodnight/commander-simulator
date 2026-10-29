"""Update the v14 implementation coverage table for the utility-land batch."""
import importlib.util,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('prior_land_coverage',ROOT.parent/'v14_lands'/'land_coverage.py')
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
UPDATED={
 'Mystic Sanctuary':'Island subtype and untapped entry condition; choose a target instant/sorcery in your graveyard when its trigger is placed, optionally return it to library top on resolution.',
 'Fiery Islet':'U/R mana with life payment; 1, tap, sacrifice to draw with priority and source reservation.',
 'Riptide Laboratory':'Colorless mana; 1U and tap to return target Wizard permanent you control, including derived Wizard types and target rechecks.',
}
def write():
 d=_base.build();d['milestone']='v15'
 for r in d['cards']:
  if r['name'] in UPDATED:r.update(status='supported subset',detail=UPDATED[r['name']])
 d['unique_counts']=dict(Counter(r['status'] for r in d['cards']));physical=Counter()
 for r in d['cards']:physical[r['status']]+=r['quantity']
 d['physical_counts']=dict(physical)
 d['priorities']=[dict(priority='P1',area='Otawara/Sokenzan channel and remaining land subsets',reason='Complete the remaining utility land choices.'),dict(priority='P2',area='Spell copying, tutors and creature activations',reason='Unlock central spell and tutor chains.'),dict(priority='Later',area='Additional caching',reason='Compare against preserved reference outputs after functional milestones.')]
 (ROOT/'CARD_COVERAGE.json').write_text(json.dumps(d,indent=2)+'\n')
 lines=['# Magnus coverage — v15','','All 100 physical cards across 83 names. Supported subset describes the implemented behavior, not complete Oracle coverage. Three land names advanced.','','| Status | Distinct names | Physical cards |','|---|---:|---:|']
 for s in ('supported subset','partial','unsupported'):lines.append(f"| {s} | {d['unique_counts'][s]} | {d['physical_counts'][s]} |")
 lines+=['','| Card | Qty | Status | Behavior / gap |','|---|---:|---|---|']
 lines += [f"| {r['name']} | {r['quantity']} | {r['status']} | {r['detail']} |" for r in d['cards']]
 lines+=['','## Next triage','']+[f"- {p['priority']}: {p['area']} — {p['reason']}" for p in d['priorities']]+['']
 (ROOT/'CARD_COVERAGE.md').write_text('\n'.join(lines));return d
if __name__=='__main__':print(write()['unique_counts'])
