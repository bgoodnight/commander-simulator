import importlib.util
from pathlib import Path
from copy_table import CopyTable
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=CopyTable(seed=3502,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*7+['Mountain']*5:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'));h.give(t,'Reiterate')
a,b,c,d=[t.add_creature(t.players[seat],2,2,'fixture',token=True).id for seat in (1,1,2,2)]
t.copy_target_policy=lambda seat,original:(c,d);used=[]
def policy(seat,frames,choices):
 if seat==0 and not used:
  choice=next((x for x in choices if x.kind=='spell' and x.action.source=='Reiterate' and not x.action.parameters['buyback'] and any(f.label=='Step Through' and f.frame_id==x.action.target_object for f in frames)),None)
  if choice:used.append(True);return choice
 return None
t.priority_policy=policy;card=h.give(t,'Step Through');assert t.cast(t.step_action(t.details,card,(a,b)));assert used
assert all(x not in t.rules.objects for x in (a,b,c,d))
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==2
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Reiterate copies Step Through','','Forced fixture with actual land-source payments. Reiterate copied Step Through and changed both targets. The copy returned the second pair, and the original returned the first. Young Pyromancer triggered for the two cast spells, not the copy.','', '```text',*t.events,'```','']))
print('Source-paid Reiterate/Step Through retarget scenario passed')
