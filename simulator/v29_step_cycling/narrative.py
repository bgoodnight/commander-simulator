import importlib.util
from pathlib import Path
from step_cycling import StepCyclingTable,STEP
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=StepCyclingTable(seed=2902,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*7+['Mountain']*2:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
a=t.add_creature(t.players[1],2,2,'fixture one',token=True).id
b=t.add_creature(t.players[2],2,2,'fixture two',token=True).id
used=[]
def response(seat,frames,choices):
 if frames and frames[-1].label==STEP and not used:
  used.append(True);t.note('SYNTHETIC RESPONSE: remove the first target before resolution.');t.world.move(a,'graveyard','destroy')
 return None
t.priority_policy=response
card=h.give(t,STEP);assert t.cast(t.step_action(t.details,card,(a,b)))
assert used and b not in t.rules.objects
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==1
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Step Through interaction','','Forced fixture using real land-source payments. Casting Step Through triggered Young Pyromancer. A synthetic response removed one target; the remaining legal creature returned. The spell resolved rather than fizzling.','', '```text',*t.events,'```','']))
print('Step Through source-paid partial target scenario passed')
