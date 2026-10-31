import importlib.util
from pathlib import Path
from reiterate_table import ReiterateTable,NAME
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=ReiterateTable(seed=3302,trace=True)
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*7+['Mountain']*6:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
t.priority_policy=lambda *a:None;h.cast(t,h.give(t,'Young Pyromancer'));h.cast(t,h.give(t,'Archmage Emeritus'));h.give(t,NAME);used=[]
def policy(seat,frames,choices):
 if seat==0 and not used:
  c=next((c for c in choices if c.kind=='spell' and c.action.source==NAME and c.action.parameters['buyback']),None)
  if c:used.append(True);return c
 return None
t.priority_policy=policy;h.cast(t,h.give(t,'Consider'));assert used
assert len(t.consider_events)==2 and NAME in [c.name for c in t.details.hand]
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==2
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Reiterate copies Consider','','Forced fixture, paid with actual land sources. Consider and Reiterate are cast, each triggering Young Pyromancer; the copy is not cast. Archmage Emeritus triggers on both casts and the copy. Reiterate returns to hand after buyback and both Consider instances resolve.','', '```text',*t.events,'```','']))
print('Source-paid Reiterate copy and buyback scenario passed')
