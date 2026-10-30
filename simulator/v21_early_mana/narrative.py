"""A source-paid Frostboil Snarl opening and Mystical Tutor."""
import importlib.util
from pathlib import Path
from mana_table import EarlyManaTable
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=EarlyManaTable(seed=2101,trace=True);t.priority_policy=lambda *args:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
h.give(t,'Island');source=t.enter_land(t.details,h.give(t,'Frostboil Snarl').object_id,cause='declared_fixture')
assert not t.rules.get(source).tapped
t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Consider')
h.cast(t,h.give(t,'Mystical Tutor'))
assert t.details.library[-1].name=='Consider' and t.rules.get(source).tapped
assert any(x['source_id']==source for x in t.resources.activations)
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Frostboil Snarl pays for Mystical Tutor','','Forced fixture: the Island card in hand was revealed, allowing Frostboil Snarl to enter untapped. It produced U to pay for Mystical Tutor, which found Consider. Consider remains unsupported as a spell.','', '```text',*t.events,'```','']))
print('source-paid narrative passed')
