"""Versioned, deterministic regression snapshots for the assembled premium engine."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'simulator'/'v35_copy_targets'))
from copy_table import CopyTable
from reference_state import reference_payload,canonical

DECK=ROOT/'decklists'/'magnus_thousand_sons_v1_14_premium.txt'
CASES=Path(__file__).with_name('REFERENCE_CASES.json')

def digest(value):
 return hashlib.sha256(json.dumps(canonical(value),sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

def run_case(case):
 providers=['aggro','control','combo'];providers.insert(case['seat'],'magnus')
 t=CopyTable(providers,seed=case['seed'],trace=False).run(case['rounds'])
 if t.safety_stop:raise RuntimeError('Unresolved baseline: '+str(t.safety_stop))
 t.assert_consistent()
 payload=reference_payload(t)
 # Historical serializer predates copied-spell and Adventure state. Record these
 # separately without changing the old v14 fingerprint contract.
 payload['current_extension']=canonical(dict(adventure_exiled=sorted(t.adventure_exiled),
  adventure_ticket_count=len(t.adventure_tickets),copy_action_count=len(t.copy_actions),
  copy_counter_count=len(t.copy_counter_types),tutor_events=t.tutor_events,
  rule_events=t.rule_events,consider_events=t.consider_events,
  dynamic_step_targets=[(f.frame_id,getattr(f.action,'step_targets',None)) for f in t.spell_stack.frames if f.action]))
 return dict(sha256=digest(payload),life=[p.life for p in t.players],reason=t.win_reason,safety=t.safety_stop)

def check():
 data=json.loads(CASES.read_text())
 actual=hashlib.sha256(DECK.read_bytes()).hexdigest()
 if actual!=data['deck_sha256']:raise ValueError('Deck hash differs from baseline; establish an explicit new baseline')
 for case in data['cases']:
  got=run_case(case)
  if got!=case['expected']:raise AssertionError(f"Reference mismatch seat={case['seat']} seed={case['seed']}: {got}")
 return len(data['cases'])

if __name__=='__main__':print(f'{check()} current-engine replay fingerprints match')
