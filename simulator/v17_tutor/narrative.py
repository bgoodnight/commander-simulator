"""Forced real-source tutor/engine interaction."""
import importlib.util
from pathlib import Path
from tutor_table import TutorTable
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',ROOT.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=TutorTable(seed=1701,trace=True);t.priority_policy=lambda *args:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ('Island','Island','Mountain','Mountain'):
 t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Ponder')
h.cast(t,h.give(t,'Mystical Tutor'))
assert t.details.library[-1].name=='Ponder'
assert sum(o.card.name=='Elemental' for o in t.rules.controlled(0))==1
assert len(t.resources.payments)>=2
h.check(t)
lines=['# Mystical Tutor and Young Pyromancer','','Forced fixture with actual land-source payments. Casting Mystical Tutor triggered Young Pyromancer, creating an Elemental before the tutor resolved. The tutor then revealed Ponder, shuffled, and put it on top.','', '```text',*t.events,'```','']
(ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines))
print('source-paid tutor narrative passed')
