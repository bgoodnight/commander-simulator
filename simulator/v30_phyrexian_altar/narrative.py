import importlib.util
from pathlib import Path
from altar_table import AltarTable,NAME
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=AltarTable(seed=3002,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*5+['Mountain']*5:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,NAME));h.cast(t,h.give(t,'Young Pyromancer'));h.cast(t,h.give(t,"Ral's Reinforcements"))
tokens=[o.object_id for o in t.rules.controlled(0) if o.token and 'creature' in o.types]
assert len(tokens)==3
for o in t.rules.controlled(0,{'land'}):o.tapped=True
t.rules._dirty();h.cast(t,h.give(t,'Consider'))
assert any(x.get('source')==NAME and x.get('sacrificed_id') in tokens for x in t.resources.activations)
assert any(o.card.name=='Young Pyromancer' for o in t.rules.controlled(0))
assert sum(o.token and 'creature' in o.types for o in t.rules.controlled(0))==3
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Phyrexian Altar interaction','','Forced fixture with real land-source payments: cast Altar and Young Pyromancer, then Ral’s Reinforcements creates two tokens and triggers Pyromancer for a third. After an explicitly forced tap of the lands, Altar sacrifices an Elemental for blue mana to cast Consider; Pyromancer then replaces the sacrificed token.','', '```text',*t.events,'```','']))
print('Altar source-paid token-to-Consider chain passed')
