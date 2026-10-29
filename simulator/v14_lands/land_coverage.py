"""Versioned audit update for the bounded land-entry/fetch milestone."""
import importlib.util,json
from pathlib import Path
from collections import Counter
from land_table import LandTable

ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('v13_coverage_baseline',ROOT.parent/'v13_engines'/'coverage_report.py')
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
COMPLETE={
 'Steam Vents':'Island/Mountain subtypes; optional affordable two-life entry payment (not damage); otherwise tapped; U/R source.',
 'Training Center':'Enters untapped with at least two current opponents; tapped with one; U/R source.',
 'Stormcarved Coast':'Enters untapped with at least two other lands; U/R source.',
 'Sulfur Falls':'Enters untapped when an already controlled land has Island or Mountain subtype; U/R source.',
 'Spirebluff Canal':'Enters untapped with at most two other lands; U/R source.',
 'Fabled Passage':'Explicit tap/sacrifice stack ability; choose a basic land or fail to find, enter tapped, shuffle, then check four lands to untap.',
}


def build():
    d=_base.build();d['milestone']='v14'
    for r in d['cards']:
        if r['name'] in COMPLETE:r.update(status='supported subset',detail=COMPLETE[r['name']])
        elif r['name']=='Mystic Sanctuary':r['detail']='Island subtype and three-other-Islands entry condition live; targeted graveyard-to-top ETB trigger remains absent.'
        elif r['name']=='Riverglide Pathway':r['detail']='Explicit U/R mana-face choice on entry; full modal double-faced characteristics remain partial.'
        elif r['name'] in ('Island','Mountain'):r['detail']='Basic supertype and matching land subtype, source mana and land timing live.'
    d['unique_counts']=dict(Counter(r['status'] for r in d['cards']));physical=Counter()
    for r in d['cards']:physical[r['status']]+=r['quantity']
    d['physical_counts']=dict(physical)
    d['priorities']=[dict(priority='P1',area='Mystic Sanctuary ETB and utility/channel abilities',reason='Finish the remaining live-land text in targeted batches.'),
                        dict(priority='P2',area='Spell copying and creature activations/tutors',reason='Unlock more central spellslinger interactions.'),
                        dict(priority='Later',area='Additional caching with exact-output comparison',reason='Track runtime now; preserve reference fingerprints before optimization.')]
    return d


def write():
    d=build();(ROOT/'CARD_COVERAGE.json').write_text(json.dumps(d,indent=2)+'\n')
    lines=['# Magnus coverage — v14','','All 100 physical cards, across 83 names. Supported subset certifies the listed behavior, not complete Oracle coverage. Six partial land names advanced; Mystic Sanctuary and Pathway remain partial. No unsupported name was enabled.','','| Status | Distinct names | Physical cards |','|---|---:|---:|']
    for s in ('supported subset','partial','unsupported'):lines.append(f"| {s} | {d['unique_counts'][s]} | {d['physical_counts'][s]} |")
    lines+=['','| Card | Qty | Status | Behavior / gap |','|---|---:|---|---|']
    lines += [f"| {r['name']} | {r['quantity']} | {r['status']} | {r['detail']} |" for r in d['cards']]
    lines+=['','## Next triage','']+[f"- {p['priority']}: {p['area']} — {p['reason']}" for p in d['priorities']]+['']
    (ROOT/'CARD_COVERAGE.md').write_text('\n'.join(lines));return d


if __name__=='__main__':
    d=write();print(d['unique_counts'],d['physical_counts'])
