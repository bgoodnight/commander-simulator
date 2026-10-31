import importlib.util
from pathlib import Path
from rift_table import RiftTable,RIFT
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=RiftTable(seed=3202,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*8+['Mountain']*2:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
a=t.add_creature(t.players[1],2,2,'hexproof fixture',token=True,keywords=('hexproof',)).id
b=t.add_creature(t.players[2],2,2,'normal fixture',token=True).id
own=t.add_creature(t.details,1,1,'own fixture',token=True).id
c=h.give(t,RIFT);assert t.cast(t.rift_action(t.details,c,overload=True));assert a not in t.rules.objects and b not in t.rules.objects and own in t.rules.objects
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==1
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Overloaded Cyclonic Rift','','Forced fixture with land-source payments. Overload returned two opposing creatures, including one with hexproof, while the controlled creature stayed. Young Pyromancer triggered once for casting the spell.','', '```text',*t.events,'```','']))
print('Overloaded Rift source-paid interaction passed')
