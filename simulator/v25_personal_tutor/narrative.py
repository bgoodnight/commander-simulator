"""Source-paid Personal Tutor into Ral's Reinforcements."""
import importlib.util
from pathlib import Path
from personal_tutor_table import PersonalTutorTable,NAME
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=PersonalTutorTable(seed=2502,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*3+['Mountain']*2:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=="Ral's Reinforcements")
h.cast(t,h.give(t,NAME));assert t.details.library[-1].name=="Ral's Reinforcements"
t.details.draw();h.cast(t,h.give(t,"Ral's Reinforcements"))
assert sum(o.card.card_id=='ral_elemental_1_1' for o in t.rules.controlled(0))==2
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==4
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Personal Tutor into Ral’s Reinforcements','','Forced setup with actual land payments. Personal Tutor found the sorcery and triggered Young Pyromancer. A subsequent declared draw and cast of Ral’s Reinforcements triggered Pyromancer again and created two blue/red Elementals: four Elemental tokens total.','', '```text',*t.events,'```','']))
print('source-paid Personal Tutor chain passed')
