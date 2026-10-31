import importlib.util
from pathlib import Path
from premium_table import PremiumTable
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=PremiumTable(seed=3102,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*2+['Mountain']:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Cyclonic Rift')
h.cast(t,h.give(t,'Merchant Scroll'))
assert 'Cyclonic Rift' in [c.name for c in t.details.hand]
assert next(c for c in t.details.hand if c.name=='Cyclonic Rift').effect=='unsupported'
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Premium deck: Merchant Scroll finds Cyclonic Rift','','Forced fixture, paid with actual land sources: Merchant Scroll legally searches for Cyclonic Rift, reveals it, puts it into hand, and shuffles. Cyclonic Rift itself remains unsupported and is not cast in this narrative.','', '```text',*t.events,'```','']))
print('Premium source-paid Merchant Scroll -> Rift search passed')
