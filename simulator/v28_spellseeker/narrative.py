"""Source-paid wizardcycling into Spellseeker and Consider."""
import importlib.util
from pathlib import Path
from spellseeker_table import SpellseekerTable,NAME
from wizard_tutor_table import STEP
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=SpellseekerTable(seed=2802,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*7+['Mountain']*3:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=={'wizardcycling':NAME,'spellseeker':'Consider'}[r.kind])
step=h.give(t,STEP);t.spell_stack.holder=0
choice=next(c for c in t.priority_choices(0) if c.kind=='wizardcycle' and c.source_id==step.object_id)
t.commit_choice(0,choice);t.spell_stack.resolve();assert NAME in [c.name for c in t.details.hand]
h.cast(t,h.give(t,NAME));assert 'Consider' in [c.name for c in t.details.hand]
h.cast(t,h.give(t,'Consider'))
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==1
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Wizardcycling to Spellseeker to Consider','','Forced fixture with actual land-source payments. Wizardcycling discarded Step Through and found Spellseeker. Its enter-the-battlefield ability found Consider, which was then cast and triggered Young Pyromancer. Cycling and casting the creature did not themselves trigger Pyromancer.','', '```text',*t.events,'```','']))
print('source-paid wizardcycling and Spellseeker chain passed')
