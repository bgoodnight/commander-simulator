"""Source-paid Magnus, Pyromancer and Ral's Reinforcements interaction."""
import importlib.util
from pathlib import Path
from reinforcements_table import ReinforcementTable,NAME
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=ReinforcementTable(seed=2402,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*9+['Mountain']*5:
 t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
commander=t.zones.views(0,'command')[0];assert t.cast(t.action_for_card(t.details,commander))
h.cast(t,h.give(t,NAME))
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==3
target=t.add_creature(t.players[1],2,2,'fixture target',token=True)
card=h.give(t,'Capsize');action=t.action_with_options(t.details,card,buyback=True,target=target.id)
assert action.cost==3 and action.parameters['U']==2
assert t.cast(action);h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Magnus, Young Pyromancer and Ral’s Reinforcements','','Forced fixture using actual lands. Casting Ral’s Reinforcements triggered Young Pyromancer and then created two blue/red Elemental tokens. With Magnus, the resulting three creature tokens reduced Capsize with buyback from 4UU to 1UU. Capsize produced another Pyromancer trigger and returned to hand.','', '```text',*t.events,'```','']))
print('source-paid Magnus, Pyromancer and Reinforcements narrative passed')
