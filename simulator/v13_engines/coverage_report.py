"""Versioned update of the conservative v12 code-path audit."""
import importlib.util
import json
from pathlib import Path
from collections import Counter
from engine_table import EngineTable

ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('v12_audit_baseline',ROOT.parent/'v12_combat'/'audit.py')
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
UPDATES={
 'Brainstorm':'Draw three, then choose/order two cards from the entire hand onto the library; one resolution.',
 'Ponder':'Look at up to three, order, optionally shuffle, then draw; explicit resolution choices.',
 'Preordain':'Scry two with ordered top/bottom partition, then draw.',
 'Telling Time':'Look at three; one to hand, one to top, one to bottom; short-library instruction order.',
 'Impulse':'Look at four; one to hand and the rest to bottom in chosen order; not a draw.',
 'Frantic Search':'Draw two, choose/discard two, untap up to three distinct lands; one resolution.',
 'Archmage Emeritus':'Body plus cast/copy magecraft draw descriptors, including Harmonic doubling; live spell-copy production remains absent.',
 'Harmonic Prodigy':'Prowess until cleanup; doubling of other Wizards or Shamans, with correct self-Wizard exclusion.',
 'Storm-Kiln Artist':'Live artifact-count power and cast/copy magecraft descriptors; spell-copy production remains absent.',
 'Baral, Chief of Compliance':'Generic discount and optional draw/discard trigger after a controlled spell/ability actually counters a spell.',
 'Stormsplitter':'Otter/Wizard, haste, copiable-base token triggers and next-end-step delayed exile; no general copy-effect layers.',
}


def build():
    data=_base.build();data['milestone']='v13'
    for row in data['cards']:
        if row['name'] in UPDATES:row.update(status='supported subset',detail=UPDATES[row['name']])
    data['unique_counts']=dict(Counter(r['status'] for r in data['cards']))
    physical=Counter()
    for r in data['cards']:physical[r['status']]+=r['quantity']
    data['physical_counts']=dict(physical)
    data['priorities']=[dict(priority='P1',area='Special-land entry/utility abilities',reason='Remaining live land adapters still affect mana development.'),
                        dict(priority='P2',area='Spell copies and relevant creature activations/tutors',reason='Unlock unsupported spellslinger cards using the shared stack and costs.'),
                        dict(priority='P3',area='Graveyard casting, layer/replacement breadth and verified combos',reason='Requires broader reusable rules and interruption tests.')]
    return data


def write():
    d=build();(ROOT/'CARD_COVERAGE.json').write_text(json.dumps(d,indent=2)+'\n')
    lines=['# Magnus coverage — v13','',
           'Implementation audit of all 100 physical cards, across 83 names. Supported subset means the behavior below is live, not complete Oracle certification. General legend rules, replacement/draw triggers, spell-copy production and other documented engine limits still apply.','',
           '| Status | Distinct names | Physical cards |','|---|---:|---:|']
    for s in ('supported subset','partial','unsupported'):lines.append(f"| {s} | {d['unique_counts'][s]} | {d['physical_counts'][s]} |")
    lines+=['','Nine distinct names moved from partial to supported subset. Frantic Search also gained an explicit discard policy. No previously unsupported named card was enabled. Historical v12 audit is preserved.','','| Card | Qty | Status | Behavior / gap |','|---|---:|---|---|']
    lines += [f"| {r['name']} | {r['quantity']} | {r['status']} | {r['detail']} |" for r in d['cards']]
    lines+=['','## Next triage','']+[f"- {p['priority']}: {p['area']} — {p['reason']}" for p in d['priorities']]+['']
    (ROOT/'CARD_COVERAGE.md').write_text('\n'.join(lines));return d


if __name__=='__main__':
    d=write();print(d['unique_counts'],d['physical_counts'])
