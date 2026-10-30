"""Source-paid Fabricate and Step Through wizardcycling."""
import importlib.util
from pathlib import Path
from wizard_tutor_table import WizardTutorTable,FABRICATE,STEP
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=WizardTutorTable(seed=2702,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*5+['Mountain']*3:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
def tutor(req):
 name={'fabricate':'Phyrexian Altar','wizardcycling':'Spellseeker'}[req.kind]
 return next(c.object_id for c in req.cards if c.name==name)
t.tutor_policy=tutor
h.cast(t,h.give(t,FABRICATE));assert 'Phyrexian Altar' in [c.name for c in t.details.hand]
c=h.give(t,STEP);t.spell_stack.holder=0
choice=next(c2 for c2 in t.priority_choices(0) if c2.kind=='wizardcycle' and c2.source_id==c.object_id)
t.commit_choice(0,choice);t.spell_stack.resolve()
assert 'Spellseeker' in [c.name for c in t.details.hand]
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==1
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Fabricate and wizardcycling with Young Pyromancer','','Forced setup with actual land payments. Fabricate found Phyrexian Altar and triggered Pyromancer. Step Through was then discarded and its wizardcycling ability found Spellseeker; cycling did not trigger Pyromancer because no spell was cast. Altar and Spellseeker effects are not yet implemented.','', '```text',*t.events,'```','']))
print('source-paid Fabricate and wizardcycling narrative passed')
