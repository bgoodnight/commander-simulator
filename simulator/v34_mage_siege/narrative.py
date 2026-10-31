import importlib.util
from pathlib import Path
from adventure_table import AdventureTable,LAND
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=AdventureTable(seed=3402,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*6+['Mountain']*6:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Harmonic Prodigy'));land=h.give(t,LAND);t.spell_stack.holder=0;t.cast_adventure(0,land.object_id)
assert t.zones.names(0,'exile').count(LAND)==1
h.cast(t,h.give(t,'Consider'));assert [p.life for p in t.players]==[40,38,38,38]
oid=next(iter(t.adventure_exiled));t.play_adventure_land(0,oid)
assert any(o.card.name==LAND and o.tapped for o in t.rules.controlled(0))
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Mage Siege, Harmonic, and Lindblum','','Forced fixture using actual land-source payments. Mage Siege created a black Wizard token and exiled Lindblum. Casting Consider caused that Wizard to damage each opponent twice because Harmonic Prodigy doubled the triggered ability. Lindblum was then played tapped from Adventure exile.','', '```text',*t.events,'```','']))
print('Source-paid Mage Siege/Harmonic/land scenario passed')
