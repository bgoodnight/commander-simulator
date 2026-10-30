"""Source-paid Sapphire Medallion and Capsize buyback interaction."""
import importlib.util
from pathlib import Path
from medallion_table import MedallionTable
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=MedallionTable(seed=2302,trace=True);t.priority_policy=lambda *args:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*7:
 t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Sapphire Medallion'))
target=t.add_creature(t.players[1],2,2,'fixture target',token=True)
card=h.give(t,'Capsize');a=t.action_with_options(t.details,card,buyback=True,target=target.id)
assert a.cost==5 and a.parameters['U']==2
assert t.cast(a) and target.id not in t.rules.objects
assert 'Capsize' in [c.name for c in t.details.hand];h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Sapphire Medallion and Capsize buyback','','Forced fixture with actual Islands. Sapphire Medallion was cast for two generic mana. Capsize with buyback then cost 3UU instead of 4UU, bounced the token target, and returned to hand.','', '```text',*t.events,'```','']))
print('source-paid Medallion and buyback narrative passed')
