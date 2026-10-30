"""Demonstrate search over a formerly unknown card with a real Island payment."""
import importlib.util
from pathlib import Path
from verified_table import VerifiedTable
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=VerifiedTable(seed=2001,trace=True);t.priority_policy=lambda *args:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
t.enter_land(t.details,h.give(t,'Island').object_id,cause='declared_fixture')
t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Consider')
h.cast(t,h.give(t,'Mystical Tutor'))
assert t.details.library[-1].name=='Consider' and len(t.resources.payments)>=1
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Mystical Tutor finds Consider','','Forced setup with actual Island payment. Consider is eligible because its instant type is verified; its printed effect remains unsupported. Tutor reveals it, shuffles, and puts it on top.','', '```text',*t.events,'```','']))
print('source-paid tutor-to-Consider narrative passed')
