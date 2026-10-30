"""Source-paid tutor-to-Consider interaction with Young Pyromancer."""
import importlib.util
from pathlib import Path
from consider_table import ConsiderTable
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=ConsiderTable(seed=2202,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ('Island','Island','Island','Mountain','Mountain'):
 t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Consider')
h.cast(t,h.give(t,'Mystical Tutor'));assert t.details.library[-1].name=='Consider'
t.details.draw();h.cast(t,h.give(t,'Consider'))
assert sum(o.card.name=='Elemental' for o in t.rules.controlled(0))==2
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Mystical Tutor, Consider, and Young Pyromancer','','Forced fixture with actual land payments: Mystical Tutor searched for Consider; the subsequent draw and cast of Consider produced a second Elemental. The default surveil choice kept the looked-at card on top, then drew it.','', '```text',*t.events,'```','']))
print('source-paid tutor and Consider narrative passed')
